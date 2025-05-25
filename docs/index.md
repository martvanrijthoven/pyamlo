# PYAMLO Documentation

Welcome to the official documentation for **PYAMLO**.

PYAMLO is a  YAML configuration loader for Python, designed for advanced configuration scenarios. It supports file inclusion, deep merging, environment variable injection, variable interpolation, and direct Python object instantiation from YAML.

---


## Why PYAMLO?

- **Composable configs**: Use `_includes` to merge multiple YAML files.
- **Powerful merging**: Deep merge, extend lists, or patch dicts.
- **Environment aware**: Inject environment variables and use defaults.
- **Python objects**: Instantiate classes/functions directly from YAML
- **Interpolation**: 
    - **Variables**: Use `${var}` to reference other config values.
    - **Strings**: Use `${var}_my_string` to reference other config values combined with strings.
    - **Instances**: Use `${object.property}` to reference instantiated objects and their properties.


---


## Quick Start

```bash
pip install pyamlo
# or, for development
uv pip install .[test,docs]
```

Given a simple YAML file `config.yaml`:

```yaml
app:
  name: MyWebApp
  port: 8080
  host: web.local
greeting: Hello, ${app.name}!
database_url: postgres://${app.host}:${app.port}/maindb
```

You can load and resolve it using PYAMLO:

```python
from pyamlo import load_config
with open("config.yaml") as f:
    config, instances = load_config(f)
print(config['greeting'])  # Hello, MyWebApp!
print(config['database_url'])  # postgres://web.local:8080/maindb
```



---