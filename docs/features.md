# Features

PYAMLO enhances standard YAML loading with powerful features for complex configurations.

## File Inclusion

### Standard Includes (`include!`)
Merge multiple configuration files with deep merging:
```yaml
include!:
  - base.yaml
  - environment.yaml
```

### Positional Includes (`!include_from`)
Include files at specific positions, replacing the key with file contents:

```yaml
app:
  name: MyApp
middleware: !include_from middleware.yml
database:
  host: localhost
```

**middleware.yml:**
```yaml
middleware:
  cache:
    enabled: true
    ttl: 3600
  monitoring:
    enabled: true
    port: 9090
```

**Result:**
```yaml
app:
  name: MyApp
middleware:
  cache:
    enabled: true
    ttl: 3600
  monitoring:
    enabled: true
    port: 9090
database:
  host: localhost
```

#### Key Validation
`!include_from` validates that included files contain only expected keys:

```yaml
# Single key - file must contain 'config' key
config: !include_from config.yml

# Multiple keys - file must contain 'train_loader' and 'val_loader' keys  
train_loader, val_loader: !include_from loaders.yml
```

Keys starting with underscore (e.g., `_helper`) are always allowed.

#### Dynamic Include Paths
Use variable interpolation in file paths:
```yaml
environment: production
config: !include_from configs/${environment}/api.yml
```



## Multiple Config Files
Load and merge multiple configuration files in order:
```python
# Base config, then environment-specific, then user overrides
config = load_config(['base.yaml', 'production.yaml', 'user-override.yaml'])
```

## Merging Strategies
- **Deep Merge**: Recursively merges dictionaries (default)
- **List Extension (`!extend`)**: Appends to existing lists
- **Dictionary Replacement (`!patch`)**: Completely replaces dictionaries

## Environment Variables (`!env`)
Inject environment variables with optional defaults:
```yaml
api_key: !env {var: API_KEY, default: "not-set"}
database_url: !env DATABASE_URL
```

## Python Integration

### Module Import (`!import`)
Import Python modules, classes, or functions:
```yaml
datetime: !import datetime.datetime
pathlib: !import pathlib.Path
```

### Object Instantiation (`!@`)
Create Python objects directly from YAML:
```yaml
log_path: !@pathlib.Path /var/log/app.log
database: !@psycopg2.connect
  host: localhost
  port: 5432
```

### Interpolated Object Instantiation (`!$`)
Create objects with variable interpolation in the module path:
```yaml
model_type: "Linear"
activation_type: "ReLU"

# Variable in module path
layer: !$torch.nn.@model_type
  in_features: 10
  out_features: 5

# Variable as entire path
activation: !$@activation_type

# Multiple variables in nested config
network:
  layer1: !$torch.nn.@model_type
    in_features: 784
    out_features: 128
  activation1: !$torch.nn.@activation_type
```

This enables dynamic object creation based on configuration variables, making configs more flexible and reusable.

## Variable Interpolation (`${...}`)
Reference other config values and perform calculations within YAML.

### Basic References
```yaml
app:
  name: MyApp
  version: 1.0
  title: ${app.name} v${app.version}  # "MyApp v1.0"
```

### Mathematical Expressions
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

### Conditional Logic
```yaml
app:
  env: production
  debug: ${app.env == 'development'}  # false
  
database:
  pool_size: ${50 if app.env == 'production' else 10}
  host: ${'prod.db.com' if app.env == 'production' else 'localhost'}
  
features:
  enable_cache: ${app.env in ['production', 'staging']}
  rate_limiting: ${app.env == 'production' or app.env == 'staging'}
```

### Object Property Access
```yaml
database: !@psycopg2.connect
  host: localhost
  port: 5432

connection_info: ${database.host}:${database.port}  # "localhost:5432"
```

### Bitwise Operations
```yaml
permissions:
  read: 4    # Binary: 100
  write: 2   # Binary: 010
  execute: 1 # Binary: 001
  
  full_access: ${permissions.read | permissions.write | permissions.execute}  # 7
  can_read: ${permissions.full_access & permissions.read}  # 4 (truthy)
  no_write: ${permissions.full_access & ~permissions.write}  # 5
```

**Supported Operations:**
- **Math**: `+`, `-`, `*`, `/`, `//`, `%`, `**`
- **Bitwise**: `&`, `|`, `^`, `~`, `<<`, `>>`
- **Comparison**: `==`, `!=`, `<`, `<=`, `>`, `>=`, `in`
- **Logical**: `and`, `or`, `not`
- **Ternary**: `value_if_true if condition else value_if_false`
- **Ternary**: `value_if_true if condition else value_if_false`

## CLI Overrides
Override configuration values via command line using the `pyamlo.` prefix:

```bash
# Single config with overrides
python -m pyamlo config.yml pyamlo.app.name=MyApp pyamlo.database.host=localhost

# Multiple configs with overrides
python -m pyamlo base.yml production.yml pyamlo.debug=true pyamlo.database.pool_size=20

# Special tags in overrides
python -m pyamlo config.yml 'pyamlo.items=!extend [4,5]' 'pyamlo.settings=!patch {"debug": true}'
```

**Programmatic usage:**
```python
from pyamlo import load_config

# Manual overrides
config = load_config("config.yml", overrides=["pyamlo.app.name=MyApp"])

# Automatic CLI reading
config = load_config("config.yml", use_cli=True)

# Combined approach
config = load_config("config.yml", 
    overrides=["pyamlo.app.name=MyApp"],  # Manual
    use_cli=True  # Also read from sys.argv
)
```

**Processing Order:**
1. Include processing (per file)
2. Config file merging (left to right)
3. Manual overrides (via `overrides` parameter)
4. CLI overrides (via `use_cli=True`)
5. Variable resolution and object instantiation
