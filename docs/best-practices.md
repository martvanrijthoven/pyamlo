# Best Practices

## Avoiding Common Pitfalls
- Do not use `!patch` unless you want to fully replace a dictionary.
- Use `!extend` only on lists.
- Use `${...}` for referencing both config values and object attributes.

## Named Instances and Namespace Resolution

### When to Use Named Instances
Use explicit `id` attributes for objects that need to be referenced from multiple places:

```yaml
# Good: Central database config with explicit ID
database: !@dict
  id: "primary_db"
  host: "localhost"
  port: 5432

# Good: Reference from multiple places
app:
  db_url: "${primary_db.host}:${primary_db.port}"
logging:
  db_handler: "${primary_db.host}"
```

### Avoid ID Conflicts
Choose unique, descriptive IDs to prevent namespace conflicts:

```yaml
# Bad: Generic IDs that might conflict
cache: !@dict
  id: "config"  # Too generic!
  
database: !@dict  
  id: "config"  # Conflict!

# Good: Specific, descriptive IDs
cache: !@dict
  id: "redis_cache"
  
database: !@dict
  id: "postgres_db"
```

### Include-Safe Patterns
When using includes, structure references to be namespace-safe:

```yaml
# base.yaml
database:
  host: "localhost"  # Structured data takes precedence
  
# production.yaml  
include!: 
  - base.yaml
  
database:
  host: "prod-db.com"  # This overrides the included value

# References resolve correctly regardless of include order
app:
  db_host: "${database.host}"  # Always gets the final merged value
```


## Using Environment Variables
- Always provide a default for non-critical env vars:
  ```yaml
  db_url: !env {var: DATABASE_URL, default: "sqlite:///default.db"}
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
