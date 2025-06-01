# Features

PYAMLO enhances standard YAML loading with several powerful features designed to handle complex configurations.



## Includes (`include!`)
- Structure your configuration across multiple files using the `include!` key.
- Files are deep-merged in order, with later files overriding earlier ones.


## Multiple Config Files
- Load and merge multiple configuration files in a single call.
- Each file processes `!include` directives independently relative to its own location.
- Files are merged in order with later files overriding earlier ones.
- Perfect for environment-specific overrides, user customizations, and modular configurations.

```python
# Load base config, then environment-specific, then user overrides
config = load_config(['base.yaml', 'production.yaml', 'user-override.yaml'])
```

## Merging Strategies
- **Deep Merge**: Recursively merges dictionaries.
- **List Extension (`!extend`)**: Appends to lists.
- **Dictionary Replacement (`!patch`)**: Replaces dictionaries.

## Environment Variables (`!env`)
- Inject environment variables directly into your config.
- Supports default values: `!env {var: NAME, default: ...}`

## Python Module Import (`!import`)
- Import Python modules, classes, or functions without instantiation.

## Python Object Instantiation (`!@`)
- Instantiate Python classes or call functions directly from YAML.
- Supports positional, keyword, and scalar arguments.

## Variable Interpolation & Expressions (`${...}`)
Reference other config values, perform calculations, and evaluate conditions within your YAML configuration.

### Basic Variable References
```yaml
app:
  name: MyApp
  version: 1.0
  title: ${app.name} v${app.version}  # "MyApp v1.0"
```

### Mathematical Expressions
Perform calculations using standard Python operators:
```yaml
server:
  workers: 4
  connections_per_worker: 100
  max_connections: ${server.workers * server.connections_per_worker}  # 400
  
pricing:
  base_price: 10.0
  tax_rate: 0.21
  total: ${pricing.base_price * (1 + pricing.tax_rate)}  # 12.1
```

### Conditional Expressions
Use Python-style conditionals for dynamic configuration:
```yaml
app:
  env: production
  debug: ${app.env == 'development'}  # false
  
database:
  pool_size: ${app.env == 'production' if 50 else 10}  # 50
  host: ${app.env == 'production' if 'prod.db.com' else 'localhost'}
  
features:
  enable_cache: ${app.env in ['production', 'staging']}
  log_level: ${'ERROR' if app.env == 'production' else 'DEBUG'}
```

### Logical Operations
Combine conditions with `and`, `or`, and `not`:
```yaml
app:
  env: production
  maintenance_mode: false
  
api:
  enabled: ${app.env == 'production' and not app.maintenance_mode}
  rate_limiting: ${app.env == 'production' or app.env == 'staging'}
```

### Object Property Access
Access properties of instantiated objects:
```yaml
database: !@ psycopg2.connect
  host: localhost
  port: 5432

connection_string: ${database.host}:${database.port}  # "localhost:5432"
```

### Bitwise Operations
Perform bitwise operations for flags, permissions, and low-level data manipulation:
```yaml
permissions:
  read: 4    # Binary: 100
  write: 2   # Binary: 010
  execute: 1 # Binary: 001
  
  # Combine permissions using bitwise OR
  full_access: ${permissions.read | permissions.write | permissions.execute}  # 7
  
  # Check if permission is granted using bitwise AND
  can_read: ${permissions.full_access & permissions.read}  # 4 (truthy)
  
  # Remove permission using bitwise AND with NOT
  no_write: ${permissions.full_access & ~permissions.write}  # 5

flags:
  debug: 1
  verbose: 2
  current: ${flags.debug | flags.verbose}  # 3
  shift_left: ${flags.debug << 2}          # 4 (multiply by 4)
  shift_right: ${flags.verbose >> 1}       # 1 (divide by 2)
```

**Supported Operations:**
- **Math**: `+`, `-`, `*`, `/`, `//`, `%`, `**`
- **Bitwise**: `&` (AND), `|` (OR), `^` (XOR), `~` (NOT), `<<` (left shift), `>>` (right shift)
- **Comparison**: `==`, `!=`, `<`, `<=`, `>`, `>=`, `in`
- **Logical**: `and`, `or`, `not`
- **Ternary**: `value_if_true if condition else value_if_false`

## CLI Overrides
Override configuration values via command-line arguments using the `pyamlo.` prefix:

```bash
# Single config with overrides
python -m pyamlo config.yml pyamlo.app.name=MyApp pyamlo.database.host=localhost

# Multiple configs with overrides (configs are merged first, then overrides applied)
python -m pyamlo base.yml production.yml pyamlo.debug=true pyamlo.database.pool_size=20

# Use with special tags
python -m pyamlo config.yml 'pyamlo.items=!extend [4,5]' 'pyamlo.settings=!patch {"debug": true}'
```

You can also use overrides programmatically with the `load_config` function:

```python
from pyamlo import load_config

# Manual overrides only
config = load_config(
    "config.yml", 
    overrides=["pyamlo.app.name=MyApp", "pyamlo.debug=true"]
)

# Automatically read CLI overrides from sys.argv
config = load_config("config.yml", use_cli=True)

# Combine manual overrides with CLI overrides
config = load_config(
    "config.yml", 
    overrides=["pyamlo.app.name=MyApp"],  # Manual overrides
    use_cli=True  # Also read from sys.argv
)
```

### Order of Operations
1. **Include Processing**: Each config file processes its own `!include` directives
2. **Config Merging**: Multiple config files are merged in order (left to right)
3. **CLI Overrides**: Command-line overrides are applied last
4. **Resolution**: Variable interpolation and object instantiation occur

CLI overrides support all YAML features and take precedence over file-based configuration.
