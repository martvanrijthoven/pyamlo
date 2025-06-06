# Best Practices

## General Guidelines
- Use `!patch` only when you need to completely replace a dictionary
- Use `!extend` only on lists to append items
- Always provide defaults for non-critical environment variables
- Use `${...}` for referencing both config values and object attributes

## Environment Variables
Always provide meaningful defaults:
```yaml
db_url: !env {var: DATABASE_URL, default: "sqlite:///default.db"}
log_level: !env {var: LOG_LEVEL, default: "INFO"}
```

## CLI Overrides

### Namespace Your Arguments
Always use the `pyamlo.` prefix to avoid conflicts:
```bash
# Good
python script.py pyamlo.app.name=MyApp --verbose

# Bad - will be ignored
python script.py app.name=MyApp --verbose
```

### Use Proper YAML Syntax
Quote complex values and use valid YAML:
```bash
# Good
python script.py 'pyamlo.items=!extend [4,5]' 'pyamlo.settings=!patch {"debug": true}'

# Bad - invalid syntax
python script.py pyamlo.items=!extend[4,5] pyamlo.settings=!patch{debug:true}
```

### Programmatic vs Command Line Usage

**Programmatic overrides:**
```python
from pyamlo import load_config

# Manual overrides for specific values
config = load_config("config.yml", overrides=[
    "pyamlo.app.debug=true",
    "pyamlo.database.host=localhost"
])

# Automatic CLI reading
config = load_config("config.yml", use_cli=True)

# Combined approach
config = load_config("config.yml", 
    overrides=["pyamlo.app.name=MyApp"],  # Always applied
    use_cli=True  # Read additional overrides from command line
)
```

**Command line usage:**
```bash
python -m pyamlo config.yml pyamlo.app.debug=true pyamlo.database.host=localhost
```

### Processing Order
1. File includes (`!include` directives)
2. Config file values (loaded from YAML files)
3. Manual overrides (via `overrides` parameter)
4. CLI overrides (when `use_cli=True`)

Manual and CLI overrides can be combined, with CLI overrides taking final precedence.
