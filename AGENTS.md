# AGENTS.md

Agent guidance for coding in the **Custom_OpenClash_Rules** repository.

## Project Overview

OpenClash configuration template and rule management system for OpenWrt routers. The project provides:
- **Subscription conversion templates** (.ini files in `cfg/`)
- **Custom routing rules** (.list files in `rule/`)
- **Automated workflows** for rule generation and conversion

**DO NOT manually edit auto-generated files**: `Custom_Clash_Opt.ini`, `Custom_Direct_Full.list`, `Custom_Proxy_Full.list`, `*.yaml`, `*.mrs`

**DO edit source files**: `Custom_Clash_Full.ini`, `Custom_Clash_A1_Node.ini`, `Custom_Direct.list`, `Custom_Proxy.list`, `*_Merge.list`

## Build/Development Commands

### Setup Environment

```bash
# Install uv (Python package manager - required)
# Install from: https://docs.astral.sh/uv/

# Setup development environment
uv sync --locked --all-extras --dev
```

### Generate Rules and Configs

```bash
# Main generation command (merges rules + generates Custom_Clash_Opt.ini)
# This is the primary command for rule generation
uv run generate

# Legacy merge script (only merges Custom_Direct.list)
python tools/rule_merge_generate.py

# Generate game CDN rules from v2fly upstream
python py/generate_game_cdn.py
```

### Testing/Validation

```bash
# Verify rule syntax (no invalid rule types)
grep -E '^[^#]' rule/Custom_Direct.list | grep -v -E '^(DOMAIN|IP-CIDR|GEOIP|USER-AGENT|PROCESS-NAME)' || echo "OK"

# Test rule generation locally
uv run generate && git diff cfg/Custom_Clash_Opt.ini rule/Custom_Direct_Full.list rule/Custom_Proxy_Full.list

# Manually test YAML to MRS conversion (requires mihomo binary)
mihomo convert-ruleset domain yaml rule/Custom_Direct_Domain.yaml rule/Custom_Direct_Domain.mrs
mihomo convert-ruleset ipcidr yaml rule/Custom_Direct_IP.yaml rule/Custom_Direct_IP.mrs
```

**Note**: No unit tests exist. Validation is done through manual testing and GitHub Actions workflows.

### Git Operations

```bash
# Check status (frequently used due to auto-generation)
git status

# Commit rule changes (triggers auto-generate-rules.yml)
git add rule/Custom_Direct.list
git commit -m "feat(rules): add example.com to direct list"

# Commit config changes (triggers update_clash_opt.yml)
git add cfg/Custom_Clash_Full.ini
git commit -m "feat(config): update proxy group configuration"
```

## Code Style Guidelines

### Python Style

#### General Principles
- **Python Version**: Requires Python 3.13+ (see `pyproject.toml`)
- **Package Manager**: Use `uv` exclusively (not pip/pipenv/poetry)
- **Encoding**: Always use UTF-8 with explicit `encoding="utf-8"` parameter
- **Line Length**: No strict limit, prioritize readability over arbitrary line breaks

#### Imports
```python
# Standard library imports first
import os
import io
import re
import urllib.request
from pathlib import Path

# No third-party dependencies in this project
# Keep imports minimal and organized
```

#### Naming Conventions
```python
# Variables and functions: snake_case
custom_direct_list = "path/to/file"
def read_rule_file(file_path):
    pass

# Constants: UPPER_SNAKE_CASE (module-level only)
UPSTREAM_URL = "https://example.com"
HEADER_LINES = 20

# No classes in this project (script-based utilities)
```

#### Types and Documentation
```python
# Use type hints for function parameters and returns (Python 3.9+ style)
def convert_line(line: str) -> str:
    """
    Single-line summary in Chinese or English
    
    Detailed explanation if needed (Chinese acceptable)
    """
    pass

# For complex types, use modern syntax
def generate_rules(content: str) -> list[str]:  # Not List[str]
    pass
```

#### File Operations
```python
# Always use context managers for file I/O
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Use Path for path operations (preferred)
from pathlib import Path
output_file = Path(__file__).parent.parent / "rule" / "file.list"

# Or os.path for backward compatibility
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
```

#### Error Handling
```python
# Minimal error handling - let exceptions propagate for debugging
# Only catch exceptions when you can meaningfully recover

# Good: Let urllib raise if download fails
with urllib.request.urlopen(UPSTREAM_URL) as response:
    content = response.read().decode('utf-8')

# Avoid: Over-defensive try-except blocks unless required
```

#### String Formatting
```python
# Prefer f-strings for readability
print(f"[✓] Generated {output_file}")
print(f"[✓] Rules count: {len(rules)}")

# Use format() or % only for specific templating needs
content = content.replace("Aethersailor", "pzyyll")  # Simple replacements
```

#### List Comprehensions and Functional Style
```python
# Use comprehensions for filtering/transformation
rules = [line.strip() for line in f.readlines() 
         if line and not line.lstrip().startswith("#")]

# Prefer set operations for deduplication
merged_rules = list(set(main_rules + merge_rules))
merged_rules.sort()

# Use join() for string concatenation in loops
content = '`'.join(rvals)
```

## File Format Conventions

### Rule Files (.list)
```ini
# Header format (first 3-6 lines)
# NAME: Custom_Direct
# AUTHOR: Aethersailor
# REPO: https://github.com/Aethersailor/Custom_OpenClash_Rules

# Rule format (one per line)
DOMAIN-SUFFIX,example.com       # Matches example.com and *.example.com
DOMAIN,exact.example.com        # Exact match only
DOMAIN-KEYWORD,keyword          # Contains keyword
IP-CIDR,1.2.3.4/24             # IPv4 range
IP-CIDR6,2001:db8::/32         # IPv6 range

# Blank lines and comments allowed
# No trailing commas, no inline comments after rules
```

### Config Files (.ini)
```ini
; Subconverter INI format (NOT Clash YAML)
; Comments use semicolons

[custom]
ruleset=🎯 Direct,https://example.com/rule.list
custom_proxy_group=🚀 Proxy`select`[]NODE_GROUP`.*

; Format: custom_proxy_group=NAME`TYPE`OPTIONS
; []NODE_GROUP is replaced by generate.py with actual node names
```

## Workflow Triggers

| File Changed | Workflow Triggered | Action |
|--------------|-------------------|--------|
| `rule/*.list` | `auto-generate-rules.yml` | Converts .list → .yaml + .mrs |
| `cfg/Custom_Clash_Full.ini` | `update_clash_opt.yml` | Regenerates Custom_Clash_Opt.ini |
| `cfg/Custom_Clash_A1_Node.ini` | `update_clash_opt.yml` | Regenerates Custom_Clash_Opt.ini |
| `rule/*_Merge.list` | `update_clash_opt.yml` | Regenerates merged rules + Opt config |

**Commits by Workflows**: Use `github-actions[bot]` author, one atomic commit per file.

## Common Tasks

### Adding Direct Connection Rules
```bash
# 1. Edit source file
vim rule/Custom_Direct.list
# Add: DOMAIN-SUFFIX,newsite.com

# 2. Test locally
uv run generate

# 3. Commit (triggers workflows)
git add rule/Custom_Direct.list
git commit -m "feat(rules): add newsite.com to direct list"
git push
```

### Adding Temporary Test Rules
```bash
# Use merge files for temporary additions (not tracked permanently)
vim rule/Custom_Direct_Merge.list
# Add test rules here

# Generate merged output
uv run generate
# Review rule/Custom_Direct_Full.list
```

### Modifying Config Templates
```bash
# Edit base template
vim cfg/Custom_Clash_Full.ini
# Modify custom_proxy_group entries

# Regenerate optimized version
uv run generate

# Check result
git diff cfg/Custom_Clash_Opt.ini
```

## Performance Notes

- **Domain/IP-CIDR rules** use optimized tree structures (fast)
- **Classical rules** use linear traversal (slower, avoid when possible)
- **MRS format** loads faster than YAML but same runtime performance
- **Only domain and ipcidr types support MRS** (classical cannot convert)

## Anti-Patterns to Avoid

❌ Editing auto-generated files directly  
❌ Using pip/pipenv instead of uv  
❌ Creating classes (project uses functional style)  
❌ Adding third-party dependencies without discussion  
❌ Mixing rule types in same file (keep domain/IP separate when possible)  
❌ Committing without testing `uv run generate` first  
❌ Using Python < 3.13  

## References

- **Mihomo Version**: v1.19.18 (pinned in workflows)
- **Entry Point**: `generate` command → `tools/generate.py:main()`
- **Fork Customizations**: Author replacement (Aethersailor → pzyyll), custom node groups
- **Rule Sources**: v2fly/domain-list-community, Loyalsoldier/v2ray-rules-dat, blackmatrix7/ios_rule_script

For detailed project context, see [CLAUDE.md](./CLAUDE.md).
