import os

root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

target_rule_direct_list = os.path.join(root_path, "rule", "Custom_Direct.list")
merge_rule_direct_list = os.path.join(
    root_path, "rule", "Custom_Direct_Merge.list"
)


def main():
    # Read the existing rules from the target file and merge merge_rule_direct_list into it
    with open(target_rule_direct_list, "r", encoding="utf-8") as f:
        existing_rules = set(line.strip() for line in f if line.strip())
    with open(merge_rule_direct_list, "r", encoding="utf-8") as f:
        new_rules = set(line.strip() for line in f if line.strip())
    merged_rules = existing_rules.union(new_rules)

    with open(target_rule_direct_list, "w", encoding="utf-8") as f:
        for rule in sorted(merged_rules):
            f.write(rule + "\n")

    print("Merged rules have been written to", target_rule_direct_list)


if __name__ == "__main__":
    main()
