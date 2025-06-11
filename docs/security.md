# Security

PYAMLO provides a comprehensive security system to control access to system resources and protect against potentially dangerous operations. The security system is designed to be both powerful and easy to use, with sensible defaults for different use cases.

## Overview

The `SecurityPolicy` class controls four main areas:

- **Environment Variables**: Access to `!env` tags
- **Module Imports**: Python object instantiation with `!@` and `!$@` tags  
- **File Includes**: File system access via `include!`, `!include`, and `!include_from`
- **Expression Evaluation**: Mathematical and logical expressions in `${...}`

## Quick Start

### Restrictive Mode (Default)
By default, PYAMLO operates in restrictive mode where everything is denied unless explicitly allowed:

```python
from pyamlo import load_config
from pyamlo.security import SecurityPolicy

# Create restrictive policy
policy = SecurityPolicy()
policy.allowed_imports.add("pathlib.Path")
policy.allowed_env_vars.add("API_KEY")
policy.allowed_include_paths.add("/safe/configs/*.yml")

config = load_config("config.yml", security_policy=policy)
```

### Permissive Mode
In permissive mode, everything is allowed except what's explicitly blocked:

```python
# Create permissive policy
policy = SecurityPolicy(restrictive=False)
policy.allowed_imports = {"os.system", "subprocess.*"}  # Block dangerous modules
policy.allowed_env_vars = {"PASSWORD"}  # Block sensitive env vars

config = load_config("config.yml", security_policy=policy)
```

## Environment Variables

Control access to environment variables via the `!env` tag.

### Restrictive Mode
Only explicitly allowed environment variables can be accessed:

```python
policy = SecurityPolicy()
policy.allowed_env_vars.add("API_KEY")
policy.allowed_env_vars.add("DATABASE_URL") 
```

**config.yml**
```yaml
# ✅ Allowed
api_key: !env API_KEY
db_url: !env DATABASE_URL

# ❌ Denied - PermissionError
secret: !env SECRET_TOKEN
```

### Permissive Mode
All environment variables are accessible unless blocked:

```python
policy = SecurityPolicy(restrictive=False)
policy.allowed_env_vars = {"SECRET_TOKEN", "PASSWORD"}  # Block these
```

## Module Imports

Control Python object instantiation and module imports.

### Basic Usage

```python
policy = SecurityPolicy()
policy.allowed_imports.add("pathlib.Path")
policy.allowed_imports.add("collections.Counter")
```

**config.yml**
```yaml
# ✅ Allowed
path: !@pathlib.Path /tmp/data
counter: !@collections.Counter [1, 2, 3, 3]

# ❌ Denied - PermissionError  
process: !@subprocess.Popen ["ls"]
```

### Wildcard Patterns

Use wildcards to allow entire modules or namespaces:

```python
policy = SecurityPolicy()
policy.allowed_imports.add("collections.*")      # All collections modules
policy.allowed_imports.add("torch.nn.*")         # All PyTorch neural network modules
policy.allowed_imports.add("pathlib.?ath")       # Path or similar (? = single char)
policy.allowed_imports.add("numpy.*")            # All numpy modules
```

**config.yml**
```yaml
# ✅ All allowed due to wildcards
counter: !@collections.Counter [1, 2, 3]
deque: !@collections.deque [4, 5, 6]
linear: !@torch.nn.Linear
  in_features: 10
  out_features: 5
conv: !@torch.nn.Conv2d
  in_channels: 3
  out_channels: 64
  kernel_size: 3
path: !@pathlib.Path /data
pure_path: !@pathlib.PurePath /other
array: !@numpy.array [1, 2, 3]
zeros: !@numpy.zeros [5, 5]
```

### Character Classes
Use bracket notation for more precise control:

```python
policy.allowed_imports.add("[cp]*.*")  # Modules starting with 'c' or 'p'
```

### Dynamic Object Creation
Control `!$@` (interpolated) object creation:

```python
policy = SecurityPolicy()
policy.allowed_imports.add("collections.*")
policy.allow_expressions = True  # Needed for variable resolution
```

**config.yml**
```yaml
container_type: Counter
data: !@collections.$container_type [1, 1, 2, 3]

# Or with full interpolation
target_class: collections.Counter
data2: !@$target_class [4, 5, 6]
```

## File Includes

Control file system access for configuration includes.

### Path Restrictions

```python
policy = SecurityPolicy()
policy.allowed_include_paths.add("/app/configs/*.yml")
policy.allowed_include_paths.add("/app/templates/**/*.yaml")
```

**config.yml**
```yaml
# ✅ Allowed
base: !include /app/configs/base.yml
database: !include_from /app/configs/database.yml

include!:
  - /app/templates/api/routes.yaml

# ❌ Denied - outside allowed paths
secrets: !include /etc/secrets.yml
```

### Wildcard Patterns for Includes

```python
policy = SecurityPolicy()
policy.allowed_include_paths.add("configs/*.yml")         # Direct children
policy.allowed_include_paths.add("configs/**/*.yml")      # All descendants  
policy.allowed_include_paths.add("templates/[abc]*.yml")  # Files starting with a, b, or c
policy.allowed_include_paths.add("env/???.yml")           # Exactly 3-character names
```

### Relative vs Absolute Paths
The security system works with resolved absolute paths, so patterns should account for the full path:

```python
import os
base_dir = os.path.abspath(".")
policy.allowed_include_paths.add(f"{base_dir}/configs/*.yml")
```

## Expression Evaluation

Control mathematical and logical expressions in `${...}` syntax.

### Restrictive Mode (Default)
Expressions are disabled by default in restrictive mode:

```python
policy = SecurityPolicy()  # restrictive=True by default
# policy.allow_expressions = False (implicit)
```

**config.yml**
```yaml
# ❌ All denied - PermissionError
port: ${8000 + 100}
debug: ${env == 'development'}
workers: ${cpu_count * 2}
```

### Enabling Expressions

```python
policy = SecurityPolicy()
policy.allow_expressions = True
```

**config.yml**
```yaml
# ✅ All allowed
base_port: 8000
port: ${base_port + 100}
env: development  
debug: ${env == 'development'}
cpu_count: 4
workers: ${cpu_count * 2}
database_url: postgresql://localhost:${port}/mydb
```

### Permissive Mode
Expressions are enabled by default in permissive mode:

```python
policy = SecurityPolicy(restrictive=False)
# policy.allow_expressions = True (implicit)
```

## Complete Examples

### Machine Learning Pipeline

```python
from pyamlo.security import SecurityPolicy

# Allow ML libraries and common utilities
policy = SecurityPolicy()
policy.allowed_imports.update([
    "torch.*", "torch.nn.*", "torch.optim.*",
    "sklearn.*", "numpy.*", "pandas.*",
    "pathlib.Path", "collections.*"
])
policy.allowed_env_vars.update([
    "CUDA_VISIBLE_DEVICES", "WANDB_API_KEY", 
    "DATA_DIR", "MODEL_DIR"
])
policy.allowed_include_paths.add("configs/**/*.yml")
policy.allow_expressions = True

config = load_config("ml_config.yml", security_policy=policy)
```

**ml_config.yml**
```yaml
# Environment and paths
data_dir: !env {var: DATA_DIR, default: "./data"}
model_dir: !env {var: MODEL_DIR, default: "./models"}
device: !env {var: CUDA_VISIBLE_DEVICES, default: "cpu"}

# Model configuration
model: !@torch.nn.Sequential
  - !@torch.nn.Linear
    in_features: 784
    out_features: 128
  - !@torch.nn.ReLU
  - !@torch.nn.Linear  
    in_features: 128
    out_features: 10

# Training settings
batch_size: 32
learning_rate: 0.001
epochs: ${50 if device != "cpu" else 10}

optimizer: !@torch.optim.Adam
  params: ${model.parameters()}
  lr: ${learning_rate}

# Data loading
train_data: !@torch.utils.data.DataLoader
  dataset: ${dataset}
  batch_size: ${batch_size}
  shuffle: true
```

### Web Application

```python
# Secure web app configuration
policy = SecurityPolicy()
policy.allowed_imports.update([
    "pathlib.Path", "datetime.datetime",
    "logging.*", "collections.*"
])
policy.allowed_env_vars.update([
    "DATABASE_URL", "SECRET_KEY", "REDIS_URL", 
    "API_HOST", "API_PORT", "DEBUG"
])
policy.allowed_include_paths.update([
    "configs/*.yml", "environments/*.yml"
])
policy.allow_expressions = True

config = load_config("app_config.yml", security_policy=policy)
```

**app_config.yml**
```yaml
# Base configuration
include!:
  - configs/database.yml
  - configs/logging.yml

# Environment-specific
env: !env {var: ENVIRONMENT, default: "development"}
debug: !env {var: DEBUG, default: "false"}

# Server settings
host: !env {var: API_HOST, default: "localhost"}
port: !env {var: API_PORT, default: "8000"}
workers: ${4 if env == "production" else 1}

# Security
secret_key: !env SECRET_KEY
session_timeout: ${3600 if env == "production" else 300}

# Database
database_url: !env DATABASE_URL
pool_size: ${20 if env == "production" else 5}

# Logging
log_level: ${{"production": "INFO", "staging": "DEBUG"}.get(env, "DEBUG")}
log_file: !@pathlib.Path
  - logs
  - ${env}.log
```

### Development vs Production

```python
def create_dev_policy():
    """Permissive policy for development"""
    policy = SecurityPolicy(restrictive=False)
    # Block only dangerous operations
    policy.allowed_imports = {"os.system", "subprocess.*", "eval", "exec"}
    return policy

def create_prod_policy():
    """Restrictive policy for production"""
    policy = SecurityPolicy(restrictive=True)
    # Allow only specific, safe operations
    policy.allowed_imports.update([
        "pathlib.Path", "datetime.*", "json.*",
        "logging.*", "collections.*"
    ])
    policy.allowed_env_vars.update([
        "DATABASE_URL", "API_KEY", "LOG_LEVEL"
    ])
    policy.allowed_include_paths.add("/app/configs/*.yml")
    policy.allow_expressions = True
    return policy

# Use based on environment
import os
if os.getenv("ENVIRONMENT") == "production":
    policy = create_prod_policy()
else:
    policy = create_dev_policy()

config = load_config("config.yml", security_policy=policy)
```

## Common Patterns

### Safe Scientific Computing

```python
policy = SecurityPolicy()
policy.allowed_imports.update([
    "numpy.*", "scipy.*", "pandas.*", "matplotlib.*",
    "sklearn.*", "torch.*", "tensorflow.*",
    "pathlib.Path", "datetime.*", "collections.*"
])
policy.allowed_env_vars.update([
    "DATA_PATH", "OUTPUT_PATH", "CUDA_VISIBLE_DEVICES"
])
policy.allow_expressions = True
```

### Configuration Management Only

```python
# No Python object creation, just configuration
policy = SecurityPolicy()
policy.allowed_imports.clear()  # No object instantiation
policy.allowed_env_vars.update(["ENV", "DEBUG", "PORT", "HOST"])
policy.allowed_include_paths.add("configs/**/*.yml")
policy.allow_expressions = True
```

### Completely Locked Down

```python
# Maximum security - only basic config loading
policy = SecurityPolicy()
# Everything remains empty - no imports, env vars, includes, or expressions
config = load_config("config.yml", security_policy=policy)
```
