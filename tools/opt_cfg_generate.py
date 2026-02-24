# ABOUTME: Generates Custom_Clash_Full_Opt.ini by merging Rule_Ext and Node_Ext configs into Custom_Clash_Full.ini.
# ABOUTME: Reads v2 rule/proxy_group data from Rule_Ext (with markers) and Node_Ext (flat proxy_group lines).

import os
import io

root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# File paths
RULE_NODE_FILE = os.path.join(root_path, "cfg", "Custom_Clash_A1_Rule_Ext.ini")
FULL_CFG_FILE = os.path.join(root_path, "cfg", "Custom_Clash_Full.ini")
OUTPUT_FILE = os.path.join(root_path, "cfg", "Custom_Clash_Full_Opt.ini")
NODE_EXT_FILE = os.path.join(root_path, "cfg", "Custom_Clash_A1_Node_Ext.ini")

# Marker constants for v2 node file sections
RULESET_START = ";ruleset-start"
RULESET_END = ";ruleset-end"
PROXY_GROUP_START = ";custom_proxy_group-start"
PROXY_GROUP_END = ";custom_proxy_group-end"


def parse_rule_node_file(file_path):
    """Parse v2 node file using state machine, return (rulesets, proxy_groups)."""
    rulesets = []
    proxy_groups = []
    state = None

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()

            # Check for section markers
            if stripped == RULESET_START:
                state = "ruleset"
                continue
            elif stripped == RULESET_END:
                state = None
                continue
            elif stripped == PROXY_GROUP_START:
                state = "proxy_group"
                continue
            elif stripped == PROXY_GROUP_END:
                state = None
                continue

            # Skip empty lines and comment lines (';' prefix, non-marker)
            if not stripped or stripped.startswith(";"):
                continue

            normalized = line if line.endswith("\n") else line + "\n"
            if state == "ruleset":
                rulesets.append(normalized)
            elif state == "proxy_group":
                proxy_groups.append(normalized)

    return rulesets, proxy_groups

def parse_node_ext_file(file_path):
    """Parse node ext file, return (node_names, proxy_group_lines).

    Node_Ext file has no section markers — collects all custom_proxy_group lines.
    """
    names = []
    lines = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith(";"):
                continue
            if not stripped.startswith("custom_proxy_group="):
                continue
            normalized = line if line.endswith("\n") else line + "\n"
            name = extract_proxy_group_name(line)
            if name:
                names.append(name)
            lines.append(normalized)
    return names, lines


def extract_ruleset_identity(line):
    """Extract identity from 'ruleset=NAME,SPEC' for deduplication.

    Returns the full value after 'ruleset=' with whitespace stripped.
    """
    stripped = line.strip()
    if not stripped.startswith("ruleset="):
        return None
    _, _, value = stripped.partition("ruleset=")
    return value.strip()


def extract_proxy_group_name(line):
    """Extract group name from 'custom_proxy_group=NAME`type`...'."""
    stripped = line.strip()
    if not stripped.startswith("custom_proxy_group="):
        return None
    _, _, value = stripped.partition("custom_proxy_group=")
    return value.split("`")[0].strip()


def is_ruleset_anchor(line):
    """Check if line is the ruleset insertion anchor.

    Matches 'ruleset=...,[]GEOSITE,cn' but not variants like
    google-cn or category-games@cn.
    """
    return line.strip().endswith(",[]GEOSITE,cn")


def is_proxy_group_anchor(line):
    """Check if line is the proxy group insertion anchor (🎯 全球直连)."""
    return extract_proxy_group_name(line) == "🎯 全球直连"


def inject_node_ext_names(line, node_ext_names):
    """Inject node_ext group names before .* in a proxy group line."""
    rvals = line.strip().partition("custom_proxy_group=")[2].split("`")
    if rvals and rvals[-1].strip() == ".*":
        rvals.pop()  # remove .*
        rvals.extend(f"[]{node_name}" for node_name in node_ext_names)
        rvals.append(".*")
        return f"custom_proxy_group={'`'.join(rvals)}\n"
    return line


def merge_config(full_lines, rule_rulesets, rule_proxy_groups, node_ext_names, node_ext_lines):
    """Merge v2 rulesets, v2 proxy_groups, and node_ext data into full config lines.

    Rulesets: smart dedup, insert new ones before the GEOSITE,cn anchor.
    V2 Proxy groups: replace matching names in-place, insert new ones before 🎯 全球直连.
    Node_Ext groups: insert definitions before 🎯 全球直连 anchor, inject node names into .* groups.
    """
    # Build v2 proxy_group index by name, preserving order
    rule_pg_by_name = {}
    rule_pg_order = []
    for line in rule_proxy_groups:
        name = extract_proxy_group_name(line)
        if name:
            rule_pg_by_name[name] = line
            rule_pg_order.append(name)
    rule_pg_used = set()

    seen_ruleset_identities = set()
    result = []
    custom_flag = False
    ruleset_inserted = False
    pg_inserted = False

    for line in full_lines:
        stripped = line.strip()

        # Skip comments before [custom] section
        if stripped.startswith(";") and not custom_flag:
            continue

        if stripped == "[custom]":
            custom_flag = True

        # Track seen ruleset identities
        if stripped.startswith("ruleset="):
            identity = extract_ruleset_identity(line)
            if identity:
                seen_ruleset_identities.add(identity)

            # At the anchor, insert non-duplicate v2 rulesets before it
            if not ruleset_inserted and is_ruleset_anchor(line):
                for rule_line in rule_rulesets:
                    rule_id = extract_ruleset_identity(rule_line)
                    if rule_id and rule_id not in seen_ruleset_identities:
                        result.append(rule_line)
                        seen_ruleset_identities.add(rule_id)
                ruleset_inserted = True

        # Handle proxy_group lines
        if stripped.startswith("custom_proxy_group="):
            name = extract_proxy_group_name(line)

            # At the anchor, insert unused v2 proxy groups before it
            if not pg_inserted and is_proxy_group_anchor(line):
                for pg_name in rule_pg_order:
                    if pg_name not in rule_pg_used:
                        result.append(inject_node_ext_names(rule_pg_by_name[pg_name], node_ext_names))
                        rule_pg_used.add(pg_name)
                pg_inserted = True
                # Insert node_ext group definitions before anchor
                result.extend(node_ext_lines)

            # Replace existing group with v2 version if available
            if name and name in rule_pg_by_name:
                line = rule_pg_by_name[name]
                rule_pg_used.add(name)

            # Inject node_ext names before .* in proxy groups
            line = inject_node_ext_names(line, node_ext_names)

        result.append(line)

    return result


def main():
    rule_rulesets, rule_proxy_groups = parse_rule_node_file(RULE_NODE_FILE)
    node_ext_names, node_ext_lines = parse_node_ext_file(NODE_EXT_FILE)

    with open(FULL_CFG_FILE, "r", encoding="utf-8") as f:
        full_lines = f.readlines()

    merged_lines = merge_config(full_lines, rule_rulesets, rule_proxy_groups, node_ext_names, node_ext_lines)

    # Buffer output and apply global replacements
    string_buffer = io.StringIO()
    string_buffer.write(";Auto generated by tools/opt_cfg_generate.py\n")
    string_buffer.write(";Do not edit this file manually\n")
    string_buffer.writelines(merged_lines)

    content = string_buffer.getvalue()
    string_buffer.close()

    content = content.replace("Aethersailor", "pzyyll")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    main()
