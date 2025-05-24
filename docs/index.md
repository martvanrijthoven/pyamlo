# Yamlo Documentation

Welcome to the official documentation for **yamlo**.

Yamlo is a flexible YAML configuration loader for Python, designed for advanced configuration scenarios. It supports file inclusion, deep merging, environment variable injection, variable interpolation, and direct Python object instantiation from YAML.

---

## Quick Start

```bash
pip install yamlo
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

You can load and resolve it using yamlo:

```python
from yamlo import load_config
with open("config.yaml") as f:
    config, instances = load_config(f)
print(config['greeting'])  # Hello, MyWebApp!
print(config['database_url'])  # postgres://web.local:8080/maindb
```

---

## Why Yamlo?

- **Composable configs**: Use `_includes` to merge multiple YAML files.
- **Powerful merging**: Deep merge, extend lists, or patch dicts.
- **Python objects**: Instantiate classes/functions directly from YAML.
- **Environment aware**: Inject environment variables and use defaults.
- **Instance tracking**: Reference objects by ID for advanced workflows.

---

## Next Steps

- [Features](features.md)
- [API Reference](api.md)
- [Best Practices](best-practices.md)
- [FAQ](faq.md)
- [Examples](examples.md)




