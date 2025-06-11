# Features

PYAMLO extends standard YAML with powerful features for complex configurations, making it perfect for machine learning, data pipelines, and application configuration management.

## Quick Reference

### Special Tags
| Syntax | Purpose | Example |
|--------|---------|---------|
| `include!` | Include & merge files | `include!: [base.yml, env.yml]` |
| `!include` | Include single file at key | `config: !include config.yml` |
| `!include_from` | Include key from config  | `config: !include_from config.yml` |
| `!@` | Instantiate Python objects | `!@datetime.datetime 2023 1 1` |
| `!@$` | Dynamic object creation | `!@collections.$counter_type` or `!@$target_class` |
| `!import` | Import Python modules | `!import datetime.datetime` |
| `!env` | Environment variables | `!env {var: API_KEY, default: none}` |
| `!extend` | Extend existing lists | `items: !extend [4, 5, 6]` |
| `!patch` | Replace dictionaries | `config: !patch {debug: true}` |

### Variable Expressions (`${...}`)
| Type | Operators | Example |
|------|-----------|---------|
| **References** | `.` access | `${app.name} v${app.version}` |
| **Math** | `+` `-` `*` `/` `//` `%` `**` | `${workers * 2 + 1}` |
| **Bitwise** | `&` `\|` `^` `~` `<<` `>>` | `${flags \| permissions}` |
| **Comparison** | `==` `!=` `<` `<=` `>` `>=` `in` | `${env == 'production'}` |
| **Logical** | `and` `or` `not` | `${debug and verbose}` |
| **Conditional** | `if-else` | `${50 if prod else 10}` |


### CLI Overrides
Override any configuration value from the command line using `pyamlo.` prefix:

```bash
# Basic overrides
python -m pyamlo config.yml pyamlo.app.name=MyApp pyamlo.debug=true

# Multiple files with overrides
python -m pyamlo base.yml prod.yml pyamlo.database.pool_size=20

# Special tags in overrides
python -m pyamlo config.yml 'pyamlo.items=!extend [4,5]' 'pyamlo.settings=!patch {"debug": true}'
```

### Programmatic Usage
Control configuration loading in Python:

```python
from pyamlo import load_config

# Manual overrides
config = load_config("config.yml", overrides=["pyamlo.app.name=MyApp"])

# Automatic CLI reading
config = load_config("config.yml", use_cli=True)

# Combined approach
config = load_config("config.yml", 
    overrides=["pyamlo.app.name=MyApp"],  # Manual overrides
    use_cli=True                         # Also read from sys.argv
)
```

### Processing Order
Configuration values are processed in this order (later overrides earlier):

1. **Include processing** (per file)
2. **Config file merging** (left to right)
3. **Manual overrides** (via `overrides` parameter)
4. **CLI overrides** (via `use_cli=True`)
5. **Variable resolution** and object instantiation
