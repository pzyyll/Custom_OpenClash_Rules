# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **Custom_OpenClash_Rules**, a comprehensive OpenClash configuration template and rule management system for OpenWrt routers. The project provides subscription conversion templates (`.ini` files) and custom routing rules (`.list` files) for the OpenClash plugin, focusing on DNS leak prevention, optimal routing, and minimal performance impact on local network access.

**Key Philosophy**: This project delivers "turnkey" OpenClash configurations through automated workflows and subscription conversion, eliminating manual config editing while achieving fast domestic access, zero DNS leaks/pollution, and comprehensive traffic splitting.

## Repository Structure

```
cfg/                    # Subscription conversion templates (.ini files)
├── Custom_Clash.ini           # Standard template (recommended)
├── Custom_Clash_Full.ini      # Heavy traffic splitting rules
├── Custom_Clash_Lite.ini      # Minimal rules (China direct, all else proxy)
├── Custom_Clash_GFW.ini       # China direct + GFW rules only
├── Custom_Clash_Opt.ini       # Auto-generated optimized version
└── Custom_Clash_A1_Node.ini   # Node group definitions for Opt

rule/                   # Custom routing rule fragments
├── Custom_Direct.list         # Main direct connection rules
├── Custom_Proxy.list          # Main proxy rules
├── Custom_Direct_Merge.list   # Additional direct rules to merge
├── Custom_Proxy_Merge.list    # Additional proxy rules to merge
├── Custom_Direct_Full.list    # Auto-generated merged direct rules
├── Custom_Proxy_Full.list     # Auto-generated merged proxy rules
├── Steam_CDN.list             # Steam download CDN rules
├── Game_Download_CDN.list     # Game platform download CDN rules
└── *.yaml / *.mrs             # Auto-generated from .list files

tools/                  # Python build scripts
├── generate.py                # Main generator (merges rules, generates Opt config)
└── rule_merge_generate.py     # Legacy merger (Custom_Direct only)

py/                     # Standalone Python scripts
└── generate_game_cdn.py       # Fetches/converts game CDN rules from v2fly

.github/workflows/      # GitHub Actions automation
├── auto-generate-rules.yml    # Converts .list → .yaml/.mrs on push
├── update_clash_opt.yml       # Regenerates Custom_Clash_Opt.ini
├── auto-update-game-cdn.yml   # Updates Game_Download_CDN.list
└── auto-update-mainland.yml   # Updates mainland rules
```

## Common Commands

### Development Setup

```bash
# Install uv (Python package manager)
# uv is used for dependency management in this project

# Install dependencies and setup
uv sync --locked --all-extras --dev
```

### Generate Rules and Configs

```bash
# Generate Custom_Clash_Opt.ini and merged rule files
# This merges Custom_Direct.list + Custom_Direct_Merge.list → Custom_Direct_Full.list
# And Custom_Proxy.list + Custom_Proxy_Merge.list → Custom_Proxy_Full.list
# Then generates Custom_Clash_Opt.ini from Custom_Clash_Full.ini + A1_Node.ini
uv run generate

# Or use the legacy merge script (only merges Custom_Direct)
python tools/rule_merge_generate.py

# Generate game CDN rules from v2fly upstream
python py/generate_game_cdn.py
```

### Manually Test Rule Conversion

The project uses `mihomo` (Meta kernel) to convert YAML rules to binary MRS format:

```bash
# Convert domain YAML to MRS
mihomo convert-ruleset domain yaml rule/Custom_Direct_Domain.yaml rule/Custom_Direct_Domain.mrs

# Convert IP YAML to MRS
mihomo convert-ruleset ipcidr yaml rule/Custom_Direct_IP.yaml rule/Custom_Direct_IP.mrs
```

### Git Operations

```bash
# Check status (common in this repo due to auto-generation)
git status

# Add and commit rule changes
git add rule/Custom_Direct.list
git commit -m "feat(rules): add example.com to direct list"

# The following will auto-trigger GitHub Actions:
# - Pushing *.list files → auto-generate-rules.yml
# - Pushing Custom_Clash_Full.ini → update_clash_opt.yml
```

## Architecture and Key Concepts

### Rule File Formats and Performance

The project maintains multiple formats of the same rules for different use cases:

- **`.list`**: Source format, used by Subconverter (subscription converter)
  - Format: `DOMAIN-SUFFIX,example.com`, `IP-CIDR,1.2.3.4/24`, etc.

- **`_Domain.yaml`**: Pure domain rules (mihomo domain tree)
  - Best performance for domain matching
  - Format: `payload: ['+.example.com', 'exact.com']`

- **`_IP.yaml`**: Pure IP-CIDR rules (mihomo Radix tree)
  - Best performance for IP matching
  - Format: `payload: ['1.2.3.4/24']`

- **`_Classical.yaml`**: Mixed domain + IP rules
  - Slower than pure formats, use only when needed
  - Format: `payload: ['DOMAIN-SUFFIX,example.com', 'IP-CIDR,1.2.3.4/24,no-resolve']`

- **`.mrs`**: Binary format (fastest loading, same runtime performance as YAML)
  - Only domain and ipcidr types support MRS
  - Classical format cannot be converted to MRS

**Performance Hierarchy**: Domain/IP-CIDR > Classical (rule traversal), MRS > YAML (loading speed only)

### Rule Generation Pipeline

1. **Manual Editing**: Edit source `.list` files ([rule/Custom_Direct.list](rule/Custom_Direct.list), [rule/Custom_Proxy.list](rule/Custom_Proxy.list))
2. **Auto-Trigger**: Push triggers [.github/workflows/auto-generate-rules.yml](.github/workflows/auto-generate-rules.yml)
3. **Shell Processing**: GitHub Actions uses `grep`/`sed` to split `.list` into:
   - `*_Domain.yaml` (domain rules only)
   - `*_IP.yaml` (IP rules only)
   - `*_Classical.yaml` (mixed rules)
4. **Binary Conversion**: mihomo converts YAML → MRS format
5. **Git Commit**: Each generated file gets individual commit with descriptive message

### Config Generation Pipeline (Custom_Clash_Opt.ini)

The `Custom_Clash_Opt.ini` file is auto-generated from multiple sources:

1. **Base Template**: [cfg/Custom_Clash_Full.ini](cfg/Custom_Clash_Full.ini) (maintained manually)
2. **Node Definitions**: [cfg/Custom_Clash_A1_Node.ini](cfg/Custom_Clash_A1_Node.ini) (custom node groups)
3. **Merge Logic** ([tools/generate.py](tools/generate.py:60-146)):
   - Parses `Custom_Clash_Full.ini` line by line
   - When encountering `custom_proxy_group` with format `[]NODE_GROUP`, injects all node names from A1_Node.ini
   - Replaces references: `Custom_Direct.list` → `Custom_Direct_Full.list`
   - Replaces author: `Aethersailor` → `pzyyll` (forked customization)
4. **Merged Rules**: Uses `Custom_Direct_Full.list` / `Custom_Proxy_Full.list` (which combine main + merge lists)

**Workflow Trigger**: Editing [cfg/Custom_Clash_Full.ini](cfg/Custom_Clash_Full.ini), [cfg/Custom_Clash_A1_Node.ini](cfg/Custom_Clash_A1_Node.ini), or rule merge lists triggers [.github/workflows/update_clash_opt.yml](.github/workflows/update_clash_opt.yml)

### Custom Rule Maintenance

**Adding Direct Connection Rules**:
- For permanent additions: Edit [rule/Custom_Direct.list](rule/Custom_Direct.list)
- For temporary/testing: Edit [rule/Custom_Direct_Merge.list](rule/Custom_Direct_Merge.list)
- Run `uv run generate` to produce [rule/Custom_Direct_Full.list](rule/Custom_Direct_Full.list)

**Adding Proxy Rules**: Same process with `Custom_Proxy*.list` files

**Rule Format Examples**:
```
DOMAIN-SUFFIX,example.com        # Matches example.com and *.example.com
DOMAIN,exact.example.com         # Exact match only
DOMAIN-KEYWORD,keyword           # Contains keyword
IP-CIDR,1.2.3.4/24              # IP range
IP-CIDR6,2001:db8::/32          # IPv6 range
```

### GitHub Actions Automation

Key workflows:

- **[auto-generate-rules.yml](.github/workflows/auto-generate-rules.yml)**: Converts `.list` → `.yaml` + `.mrs` (triggers on push to `rule/*.list`)
- **[update_clash_opt.yml](.github/workflows/update_clash_opt.yml)**: Regenerates `Custom_Clash_Opt.ini` (triggers on config/rule changes)
- **[auto-update-game-cdn.yml](.github/workflows/auto-update-game-cdn.yml)**: Fetches game CDN rules from v2fly/domain-list-community
- **[auto-update-mainland.yml](.github/workflows/auto-update-mainland.yml)**: Updates China mainland IP/domain lists

All workflows use `github-actions[bot]` for commits, creating atomic commits per file.

## Project-Specific Notes

### Subscription Conversion Templates

Templates in [cfg/](cfg/) are **Subconverter INI format**, not Clash YAML configs. They define:
- `ruleset=GROUP,TYPE:URL` — Rule-set assignments
- `custom_proxy_group=NAME`TYPE`OPTIONS` — Proxy group definitions

These templates are consumed by subscription conversion services (like api.asailor.org/sub) to generate final Clash configs.

### Fork-Specific Customizations

This is a fork with custom modifications:
- Author replacement: `Aethersailor` → `pzyyll` in generated files ([tools/generate.py:140](tools/generate.py#L140))
- Custom node groups in [cfg/Custom_Clash_A1_Node.ini](cfg/Custom_Clash_A1_Node.ini)
- Custom merge rules in `*_Merge.list` files

### Rule Source Attribution

Rules are derived from multiple upstream projects:
- **v2fly/domain-list-community**: GeoSite data (GEOSITE rules in .ini)
- **Loyalsoldier/v2ray-rules-dat**: GeoIP data
- **blackmatrix7/ios_rule_script**: Various platform rules
- Custom additions for uncommon CN domains (via Telegram bot @asailor_rulebot)

### Important File Relationships

- **DO NOT** manually edit `Custom_Clash_Opt.ini`, `Custom_Direct_Full.list`, `Custom_Proxy_Full.list`, `*.yaml`, `*.mrs` — they are auto-generated
- **DO** edit source files: `Custom_Clash_Full.ini`, `Custom_Clash_A1_Node.ini`, `Custom_Direct.list`, `Custom_Proxy.list`, `*_Merge.list`
- **Mihomo version** is pinned in workflows ([.github/workflows/auto-generate-rules.yml:32](.github/workflows/auto-generate-rules.yml#L32)), currently `v1.19.18`

### Python Environment

- Uses **uv** for dependency management (not pip/pipenv/poetry)
- Python 3.13+ required ([pyproject.toml:6](pyproject.toml#L6))
- Entry point: `generate` command defined in [pyproject.toml:10](pyproject.toml#L10) → [tools/generate.py](tools/generate.py)

### Testing Changes Locally

```bash
# Test rule generation
uv run generate

# Verify output files
git diff cfg/Custom_Clash_Opt.ini rule/Custom_Direct_Full.list rule/Custom_Proxy_Full.list

# Test game CDN update
python py/generate_game_cdn.py

# Verify no syntax errors in rules
grep -E '^[^#]' rule/Custom_Direct.list | grep -v -E '^(DOMAIN|IP-CIDR|GEOIP|USER-AGENT|PROCESS-NAME)' || echo "OK"
```

### Common Issues

1. **MRS Conversion Fails**: Ensure using compatible mihomo version and correct rule type (domain/ipcidr only)
2. **Merge Not Working**: Check that merge list files exist and have correct format
3. **Opt Generation Issues**: Verify [cfg/Custom_Clash_Full.ini](cfg/Custom_Clash_Full.ini) and [cfg/Custom_Clash_A1_Node.ini](cfg/Custom_Clash_A1_Node.ini) are valid INI format with `custom_proxy_group` entries
