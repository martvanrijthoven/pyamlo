# PYAMLO: YAML Configuration Loader

[![PyPI](https://img.shields.io/pypi/v/pyamlo?color=0&label=pypi%20package)](https://pypi.org/project/pyamlo/)
[![Tests](https://github.com/martvanrijthoven/pyamlo/actions/workflows/test.yml/badge.svg)](https://github.com/martvanrijthoven/pyamlo/actions/workflows/test.yml)
[![License](https://img.shields.io/github/license/martvanrijthoven/pyamlo)](https://github.com/martvanrijthoven/pyamlo/blob/main/LICENSE)

`PYAMLO` is a  YAML configuration loader for Python, designed for advanced configuration scenarios. It supports file inclusion, deep merging, environment variable injection, variable interpolation, and direct Python object instantiation from YAML and object instance referencing including their properties.

## Features

- **Includes:** Merge multiple YAML files using `_includes`.
- **Merging:** Deep merge dictionaries, extend lists (`!extend`), and patch/replace dictionaries (`!patch`).
- **Environment Variables:** Substitute values using `!env VAR_NAME` or `!env {var: NAME, default: ...}`.
- **Variable Interpolation:** Reference other configuration values using `${path.to.value}` syntax.
- **Object Instantiation:** Create Python objects directly from YAML using `!@module.path.ClassName` or `!@module.path.func`
- **Instance Referencing:** Use `${instance}` to reference instantiated objects and their properties. Or `${instance.attr}` to reference attributes of instantiated objects.

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
  main: !@pyamlo.SystemInfo
  secondary: !@pyamlo.SystemInfo

hostdefault: !@pyamlo.call "${services.main.as_dict}" 

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

```python
from pyamlo import load_config

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