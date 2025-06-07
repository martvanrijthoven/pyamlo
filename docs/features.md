# Features

PYAMLO extends standard YAML with powerful features for complex configurations, making it perfect for machine learning, data pipelines, and application configuration management.

## Quick Reference

### Special Tags
| Syntax | Purpose | Example |
|--------|---------|---------|
| `include!` | Include & merge files | `include!: [base.yml, env.yml]` |
| `!include` | Include single file at key | `config: !include config.yml` |
| `!include_from` | Include content as key(s) | `config1, config2: !include_from config.yml` |
| `!@` | Instantiate Python objects | `!@datetime.datetime 2023 1 1` |
| `!$@` | Dynamic object creation | `!$torch.nn.@layer_type` or `!$@optimizer_class` |
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

## 1. File Management

### Multiple Configuration Files
Load and merge configurations in order of precedence:

```python
from pyamlo import load_config

# Single file
config = load_config('config.yml')

# Multiple files (later files override earlier ones)
config = load_config(['base.yml', 'production.yml', 'user.yml'])
```

### File Inclusion (`include!`)
Merge external files with deep merging:

```yaml
# main.yml
include!:
  - database.yml
  - logging.yml
  - features.yml

app:
  name: MyApp
  version: 1.0
```

### Positional Inclusion (`!include_from`)
Insert file contents at specific locations:

```yaml
# config.yml
app:
  name: MyApp
middleware: !include_from middleware.yml
database:
  host: localhost
```

```yaml
# middleware.yml
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
Validates included files contain expected keys:
```yaml
config: !include_from config.yml                    # Must contain 'config' key
train_loader, val_loader: !include_from loaders.yml # Must contain both keys
```

#### Dynamic Paths
Use variables in file paths:
```yaml
environment: production
config: !include_from configs/${environment}/api.yml
```

## 2. Python Integration

### Import Modules (`!import`)
Import Python classes and functions:

```yaml
datetime: !import datetime.datetime
Path: !import pathlib.Path
```

### Create Objects (`!@`)
Instantiate Python objects directly:

```yaml
# Simple objects
current_time: !@datetime.datetime 2023 12 25 10 30

# Complex objects with parameters
database: !@psycopg2.connect
  host: localhost
  port: 5432
  database: myapp
  user: admin
```

### Dynamic Object Creation (`!$@`)
Create objects with variable interpolation:

```yaml
model_type: Linear
activation: ReLU

# Variable in class name
layer: !$torch.nn.@model_type
  in_features: 784
  out_features: 128

# Variable as entire path
activation_fn: !$@activation

# Complex neural network example
network:
  layers:
    - !$torch.nn.@model_type:
        in_features: 784
        out_features: 256
    - !$torch.nn.@activation
    - !$torch.nn.@model_type:
        in_features: 256
        out_features: 10
```

## 3. Variable Interpolation

### Basic References (`${...}`)
Reference other configuration values:

```yaml
app:
  name: MyApp
  version: 1.0
  title: ${app.name} v${app.version}  # Result: "MyApp v1.0"
  
database:
  host: localhost
  port: 5432
  url: postgresql://${database.host}:${database.port}/mydb
```

### Mathematical Operations
Perform calculations within configurations:

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

**Supported Operations:**
- **Math**: `+`, `-`, `*`, `/`, `//`, `%`, `**`
- **Bitwise**: `&`, `|`, `^`, `~`, `<<`, `>>`
- **Comparison**: `==`, `!=`, `<`, `<=`, `>`, `>=`, `in`
- **Logical**: `and`, `or`, `not`

### Conditional Logic
Dynamic configuration based on conditions:

```yaml
app:
  environment: production
  debug: ${app.environment == 'development'}  # false
  
database:
  pool_size: ${50 if app.environment == 'production' else 10}
  host: ${'prod.db.com' if app.environment == 'production' else 'localhost'}
  
features:
  cache_enabled: ${app.environment in ['production', 'staging']}
  rate_limiting: ${app.environment != 'development'}
```

## 4. Environment & External Data

### Environment Variables (`!env`)
Inject environment variables with optional defaults:

```yaml
# Simple usage
api_key: !env API_KEY
database_url: !env DATABASE_URL

# With defaults (using 'var' or 'name')
api_key: !env {var: API_KEY, default: "development-key"}
debug_mode: !env {name: DEBUG, default: false}
port: !env {var: PORT, default: 8000}
```

### Merging Strategies
Control how data is combined:

```yaml
# Default: Deep merge (recursively merges dictionaries)
base_config:
  database:
    host: localhost
    port: 5432

# Extend lists instead of replacing
existing_items: [1, 2, 3]
more_items: !extend [4, 5, 6]  # Result: [1, 2, 3, 4, 5, 6]

# Replace entire dictionaries
old_settings:
  debug: false
  verbose: true
new_settings: !patch {debug: true}  # Completely replaces old_settings
```

## 5. Command Line Integration

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

## Complete Example

Here's a comprehensive example showing multiple features together:

```yaml
# config.yml
include!:
  - database.yml
  - logging.yml

app:
  name: MyApp
  environment: ${ENV:-development}
  debug: ${app.environment == 'development'}
  version: 1.0.0
  title: ${app.name} v${app.version}

# Dynamic model creation
model_type: Linear
optimizer_class: torch.optim.Adam

model: !$torch.nn.@model_type
  in_features: 784
  out_features: ${128 if app.environment == 'production' else 64}

optimizer: !$@optimizer_class
  lr: 0.001

# Environment-specific settings  
database:
  pool_size: ${50 if app.environment == 'production' else 10}
  host: !env {name: DB_HOST, default: localhost}

# External configuration
middleware: !include_from middleware/${app.environment}.yml

# Extended configuration
base_features: [auth, logging]
features: !extend [monitoring, caching]

# Runtime objects
logger: !@logging.getLogger ${app.name}
start_time: !@datetime.datetime.now
```

This example demonstrates file inclusion, variable interpolation, conditional logic, environment variables, dynamic object creation with both `!$torch.nn.@variable` and `!$@variable` patterns, and list extension all working together.
