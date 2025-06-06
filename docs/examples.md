# Examples

This page provides quick examples of PYAMLO's core features. For a comprehensive, real-world example, see the [PyTorch Ignite Tutorial](pytorch-ignite.md) which demonstrates a complete machine learning training pipeline using modular configuration.

## Minimal Example
```yaml
app:
  name: MinimalApp
  version: 1.0
```

## Multi-file Include
```yaml
include!:
  - base.yaml
  - override.yaml
```

## Positional Include (`!include_at`)
Place file contents at specific positions in your configuration:

```yaml
app:
  name: MyApp
  version: 1.0

# Include middleware config at this exact position
middleware: !include_at middleware.yml

database:
  host: localhost
  port: 5432
```

Where `middleware.yml` contains:
```yaml
middleware:
  cache:
    enabled: true
    ttl: 3600
  monitoring:
    enabled: true
    port: 9090
```

Result merges the contents at the position of `middleware`:
```yaml
app:
  name: MyApp
  version: 1.0
middleware:
  cache:
    enabled: true
    ttl: 3600
  monitoring:
    enabled: true
    port: 9090
database:
  host: localhost
  port: 5432
```

> **Note:** Included files must contain keys matching the assignment target. Keys starting with underscore are always allowed as helper keys.

### Variable Interpolation in Include Paths
```yaml
environment: production
service_type: api

# Dynamic path based on variables
config: !include_at configs/${environment}/${service_type}.yml
```

This resolves to `configs/production/api.yml`.

## Environment Variable with Default
```yaml
api_key: !env {var: API_KEY, default: "not-set"}
```

## Python Module Import
```yaml
# Import a class
datetime: !import datetime.datetime

# use the imported class
current_time: !@pyamlo.call ${datetime.now}
```

## Python Object Instantiation
```yaml
log_path: !@pathlib.Path /var/log/myapp.log
```

---

## Advanced Usage
.

### Deep Merging, Dict Patching and List Extension
```yaml
include!:
  - base.yaml

users:
  admin: !patch 
    user: root
    id: 1
  guests: !extend ["guest2"]

```
Where `base.yaml` contains:
```yaml
users:
  admin:
    name: root
    value: 1
  guests: ["guest1"]
```
Result: `admin` is `{'user': 'root', 'id': 1}`, `guests` is `["guest1", "guest2"]`.

### Python Object Instantiation
```yaml
# Use hierarchical path references
main_db: !@mydb.Database
  dsn: ${db_url}
  pool_size: 10

worker: !@myapp.Worker
  db: ${main_db}

# References follow YAML structure
app:
  db_connection: ${main_db}
  worker_instance: ${worker}
```

Reference Python objects via `${main_db}` elsewhere in the config.


### Advanced Variable Interpolation

!!! note
    The `ml` module used in this example is fictional and used for demonstration purposes only. It illustrates how you might structure a machine learning pipeline configuration using PYAMLO's variable interpolation features.

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

## Overrides

```python
from pyamlo import load_config
config = load_config("config.yaml", overrides=[
    "pyamlo.app.name=NewApp",
    "pyamlo.database.host=localhost"
])
``` 

## CLI Overrides

````bash
python -m pyamlo config.yaml pyamlo.app.name=NewApp pyamlo.database.host=localhost
````

```python
from pyamlo import load_config
config = load_config("config.yaml", use_cli=True)
```

## Complete Examples

### PyTorch Ignite Training Pipeline

For a comprehensive example demonstrating PYAMLO's capabilities in a real machine learning project, see the [PyTorch Ignite Tutorial](pytorch-ignite.md). This example shows:

- **Modular Configuration**: Split complex ML pipelines into focused, reusable components
- **Automatic Device Detection**: Conditional CUDA/CPU configuration
- **Object Instantiation**: Creating PyTorch models, optimizers, and training engines from YAML
- **Variable Interpolation**: Sharing objects and values across configuration files
- **Advanced Patterns**: Environment variables, conditional logic, and command-line overrides

The tutorial includes both monolithic and modular approaches, demonstrating how to scale from simple prototypes to complex ML configurations.