# Yamlo: Flexible YAML Configuration Loader

[![PyPI - Version](https://img.shields.io/pypi/v/yamlo)](https://pypi.org/project/yamlo/) <!-- Add after publishing -->
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/yamlo)](https://pypi.org/project/yamlo/) <!-- Add after publishing -->
[![Tests](https://github.com/your-username/yamlo/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/yamlo/actions/workflows/ci.yml) <!-- CHANGE THIS -->
[![License](https://img.shields.io/pypi/l/yamlo)](./LICENSE) <!-- Add after publishing -->

`yamlo` is a flexible YAML configuration loader for Python, designed for advanced configuration scenarios. It supports file inclusion, deep merging, environment variable injection, variable interpolation, and direct Python object instantiation from YAML.

## Features

- **Includes:** Merge multiple YAML files using `_includes`.
- **Merging:** Deep merge dictionaries, extend lists (`!extend`), and patch/replace dictionaries (`!patch`).
- **Environment Variables:** Substitute values using `!env VAR_NAME` or `!env {var: NAME, default: ...}`.
- **Variable Interpolation:** Reference other configuration values using `${path.to.value}` syntax.
- **Object Instantiation:** Create Python objects directly from YAML using `!@module.path.ClassName` or `!@module.path.func`. Store instances with IDs for later reference.

## Example

```yaml
_includes:
  - examples/base.yml
  - examples/override.yml

testenv: !env MY_TEST_VAR

app:
  name: TestApp
  version: "2.0"

paths:
  base: !@pathlib.Path /opt/${app.name}
  data: !@pathlib.Path
    - ${paths.base}
    - data

services:
  main: !@yamlo.SystemInfo
  secondary: !@yamlo.SystemInfo

hostdefault: !@yamlo.call "${services.main.as_dict}" 

pipeline:
  composite:
    first: ${services.main.host}
    second: ${services.secondary}

logs:
  - !@pathlib.Path /logs/${app.name}/main.log
  - !@pathlib.Path /logs/${app.name}/${services.main.host}.log
```

## Installation

```bash
# Using uv (recommended)
uv pip install .[test,docs]

# Using pip
pip install .[test,docs]
```

## Usage

After installation, you can use the CLI:

```bash
yamlo examples/test_config.yaml
```

Or use as a Python library:

```python
from yamlo import load_config

config = load_config("examples/test_config.yaml")
print(config)
```

## Development

- **Run tests:**  
  `pytest`

- **Build docs:**  
  `mkdocs serve`

- **Build package:**  
  `hatch build`

## License

See [LICENSE](LICENSE).