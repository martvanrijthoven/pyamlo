# Examples

Quick examples of PYAMLO's core features. For a comprehensive real-world example, see the [PyTorch Ignite Tutorial](pytorch-ignite.md).

## Basic Configuration
```yaml
app:
  name: MinimalApp
  version: 1.0
```

## File Inclusion
```yaml
include!:
  - base.yaml
  - override.yaml
```

## Positional Include
Place file contents at specific positions:

```yaml
app:
  name: MyApp
middleware: !include_at middleware.yml
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

!!! note "Key Validation"
    Included files must contain keys matching the assignment target. Keys starting with underscore are always allowed as helper keys.

### Dynamic Include Paths
```yaml
environment: production
service_type: api
config: !include_at configs/${environment}/${service_type}.yml
```

## Environment Variables
```yaml
api_key: !env {var: API_KEY, default: "not-set"}
database_url: !env DATABASE_URL
```

## Python Integration
```yaml
# Import classes
datetime: !import datetime.datetime

# Instantiate objects
log_path: !@pathlib.Path /var/log/myapp.log
current_time: !@pyamlo.call ${datetime.now}
```

## Advanced Features

### Merging Strategies
```yaml
include!:
  - base.yaml

users:
  admin: !patch 
    user: root
    id: 1
  guests: !extend ["guest2"]
```

**base.yaml:**
```yaml
users:
  admin:
    name: root
    value: 1
  guests: ["guest1"]
```

**Result:** `admin` becomes `{'user': 'root', 'id': 1}`, `guests` becomes `["guest1", "guest2"]`.

### Object References
```yaml
# Create objects and reference them
main_db: !@mydb.Database
  dsn: ${db_url}
  pool_size: 10

worker: !@myapp.Worker
  db: ${main_db}

app:
  db_connection: ${main_db}
  worker_instance: ${worker}
```

### Variable Interpolation
```yaml
pipeline:
  preprocess: !@ml.PreprocessStep
    name: preprocess
  train: !@ml.TrainStep
    name: train
    inputs: ${pipeline.preprocess.outputs}
  evaluate: !@ml.EvaluateStep
    name: evaluate
    inputs: ${pipeline.train.outputs}
```

## Configuration Overrides

### Programmatic
```python
from pyamlo import load_config

config = load_config("config.yaml", overrides=[
    "pyamlo.app.name=NewApp",
    "pyamlo.database.host=localhost"
])
```

### Command Line
```bash
python -m pyamlo config.yaml pyamlo.app.name=NewApp pyamlo.database.host=localhost
```

### Automatic CLI Reading
```python
from pyamlo import load_config
config = load_config("config.yaml", use_cli=True)
```

## Complete Example

For a comprehensive example demonstrating PYAMLO's capabilities in a real machine learning project, see the [PyTorch Ignite Tutorial](pytorch-ignite.md). This example shows:

- **Modular Configuration**: Split complex ML pipelines into focused, reusable components
- **Automatic Device Detection**: Conditional CUDA/CPU configuration  
- **Object Instantiation**: Creating PyTorch models, optimizers, and training engines from YAML
- **Variable Interpolation**: Sharing objects and values across configuration files
- **Advanced Patterns**: Environment variables, conditional logic, and command-line overrides