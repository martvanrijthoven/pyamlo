# Examples

## Minimal Example
```yaml
app:
  name: MinimalApp
  version: 1.0
```

## Multi-file Include
```yaml
_includes:
  - base.yaml
  - override.yaml
```

## Environment Variable with Default
```yaml
api_key: !env {var: API_KEY, default: "not-set"}
```

## Python Object Instantiation
```yaml
log_path: !@pathlib.Path /var/log/myapp.log
```

**Parameters:**
- `stream`: A file-like object (e.g., from `open('config.yaml')`).

**Returns:**
- `config`: The fully resolved configuration dictionary.
- `instances`: A dictionary of Python objects instantiated via `!@` tags (internal tracking, not user-facing).

**Basic Example:**
```python
from yamlo import load_config
with open('examples/test_config.yaml') as f:
    config, instances = load_config(f)
```

---

## Advanced Usage

### Dynamic Includes and Environment-Driven Configs
```yaml
_includes:
  - base.yaml
  - !env {var: EXTRA_CONFIG, default: 'optional.yaml'}
```
Dynamically include files based on environment variables.

### Deep Merging, List Extension, and Patching
```yaml
users:
  admins: ["root"]
  guests: ["guest1"]

_includes:
  - override.yaml
```
Where `override.yaml` contains:
```yaml
users:
  admins: !extend ["admin1", "admin2"]
  guests: !patch ["guest2"]
```
Result: `admins` is `["root", "admin1", "admin2"]`, `guests` is `["guest2"]`.

### Python Object Instantiation
```yaml
main_db: !@mydb.Database
  dsn: ${db_url}
  pool_size: 10

worker: !@myapp.Worker
  db: ${main_db}
```
Reference the actual Python object via `${main_db}` elsewhere in the config.

### Function Calls and Attribute Interpolation
```yaml
now: !@datetime.datetime.now

log_path: !@pathlib.Path
  - /logs
  - ${now.year}
  - ${now.month}
  - app.log
```
Creates a log path with the current year and month.

### Advanced Variable Interpolation
Supports nested and attribute-based interpolation:
```yaml
pipeline:
  step1: !@myapp.Step
    name: preprocess
  step2: !@myapp.Step
    name: train
    depends_on: ${pipeline.step1}
  step3: !@myapp.Step
    name: evaluate
    depends_on: ${pipeline.train}
```

### Full Example: ML Pipeline
```yaml
_includes:
  - base.yaml
  - !env {var: EXTRA_CONFIG, default: 'ml_override.yaml'}

experiment:
  name: "exp1"
  started: !@datetime.datetime.now

paths:
  root: !@pathlib.Path /mnt/data/${experiment.name}
  logs: !@pathlib.Path ${paths.root}/logs

model:
  type: resnet50
  weights: !env {var: MODEL_WEIGHTS, default: null}

train:
  dataset: !@myml.load_dataset
    path: ${paths.root}/train
    batch_size: 32
  optimizer: !@torch.optim.Adam
    lr: 0.001
  epochs: 10

callbacks:
  - !@myml.EarlyStopping
      patience: 5
  - !@myml.ModelCheckpoint
      path: ${paths.logs}/best.pt
```

---
