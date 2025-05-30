# Best Practices

## Using Environment Variables
- Always provide a default for non-critical env vars:
  ```yaml
  db_url: !env {var: DATABASE_URL, default: "sqlite:///default.db"}
  ```

## Avoiding Common Pitfalls
- Do not use `!patch` unless you want to fully replace a dictionary.
- Use `!extend` only on lists.
- Use `${...}` for referencing both config values and object attributes.

## Testing Configs
- Use PYAMLO in your test suite to validate all config files load and resolve as expected.
- Example pytest:
  ```python
  import pytest
  from pyamlo import load_config
  @pytest.mark.parametrize("fname", ["prod.yaml", "dev.yaml"])
  def test_config_loads(fname):
      with open(fname) as f:
          cfg, _ = load_config(f)
      assert "app" in cfg
  ```

## CLI Overrides Best Practices

### Programmatic vs Command Line Usage

PYAMLO supports overrides in two ways:

**Programmatic overrides** (via `overrides` parameter):
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

**Command line usage**:
```bash
python -m pyamlo config.yml pyamlo.app.debug=true pyamlo.database.host=localhost
```

### Namespace Your Arguments
- Always use the `pyamlo.` prefix for PYAMLO config overrides
- This avoids conflicts with other CLI arguments
```bash
# Good
python script.py pyamlo.app.name=MyApp --verbose

# Bad - no pyamlo prefix, will be ignored
python script.py app.name=MyApp --verbose
```

### Use Proper YAML Syntax in Values
- Use single quotes for values containing spaces or special characters
- Use valid YAML for !extend and !patch values
```bash
# Good
python script.py 'pyamlo.items=!extend [4,5]' 'pyamlo.settings=!patch {"debug": true}'

# Bad - invalid YAML syntax
python script.py pyamlo.items=!extend[4,5] pyamlo.settings=!patch{debug:true}
```

### Order of Precedence
1. Included file values (!include)
2. Config file values (loaded from YAML files)
3. Manual overrides (provided via `overrides` parameter)
4. CLI overrides (when `use_cli=True`, read from sys.argv)

When both manual overrides and CLI overrides are used together, they are combined with manual overrides processed first, then CLI overrides applied on top.
