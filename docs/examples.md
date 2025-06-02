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
main_db: !@mydb.Database
  dsn: ${db_url}
  pool_size: 10

worker: !@myapp.Worker
  db: ${main_db}
```
Reference the actual Python object via `${main_db}` elsewhere in the config.


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