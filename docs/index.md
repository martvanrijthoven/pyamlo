# PYAMLO Documentation

!!! warning "Development Status"
    PYAMLO is currently in development. The API is not stable and may change without notice.

**PYAMLO** is an advanced YAML configuration loader for Python that supports file inclusion, deep merging, environment variable injection, variable interpolation, and direct object instantiation.

## Why PYAMLO?

- **Composable configs**: Use `include!` to merge multiple YAML files
- **Powerful merging**: Deep merge, extend lists, or patch dictionaries  
- **Environment aware**: Inject environment variables with defaults
- **Python objects**: Instantiate classes and functions directly from YAML
- **Variable interpolation**: Reference config values, combine strings, and access object properties with `${...}`


## Quick Start

```bash
pip install pyamlo
```

**config.yaml:**
```yaml
app:
  name: MyWebApp
  port: 8080
  host: web.local
greeting: Hello, ${app.name}!
database_url: postgres://${app.host}:${app.port}/maindb
```

**Python:**
```python
from pyamlo import load_config

config = load_config("config.yaml")
print(config['greeting'])      # Hello, MyWebApp!
print(config['database_url'])  # postgres://web.local:8080/maindb
```