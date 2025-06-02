# PYAMLO

> ⚠️ **Development Status**: This project is in development. APIs may change without warning.

[![PyPI](https://img.shields.io/pypi/v/pyamlo?color=0&label=pypi%20package)](https://pypi.org/project/pyamlo/)
[![Tests](https://github.com/martvanrijthoven/pyamlo/actions/workflows/test.yml/badge.svg)](https://github.com/martvanrijthoven/pyamlo/actions/workflows/test.yml)
[![Codecov](https://codecov.io/gh/martvanrijthoven/pyamlo/branch/main/graph/badge.svg)](https://codecov.io/gh/martvanrijthoven/pyamlo)
[![docs](https://github.com/martvanrijthoven/pyamlo/actions/workflows/docs.yml/badge.svg)](https://github.com/martvanrijthoven/pyamlo/actions/workflows/docs.yml)
[![License](https://img.shields.io/github/license/martvanrijthoven/pyamlo)](https://github.com/martvanrijthoven/pyamlo/blob/main/LICENSE)

`PYAMLO` is a  YAML configuration loader for Python, designed for advanced configuration scenarios. It supports file inclusion, deep merging, environment variable injection, variable interpolation, and direct Python object instantiation from YAML and object instance referencing including their properties.

## Features

- **Includes:** Merge multiple YAML files using `include!`.
- **Merging:** Deep merge dictionaries, extend lists (`!extend`), and patch/replace dictionaries (`!patch`).
- **Environment Variables:** Substitute values using `!env VAR_NAME` or `!env {var: NAME, default: ...}`.
- **Variable Interpolation:** Reference other configuration values using `${path.to.value}` syntax.
- **Math Expressions:** Perform calculations directly in YAML using `${2 + 3 * 4}`, `${workers * scaling_factor}`, etc.
- **Object Instantiation:** Create Python objects directly from YAML using `!@module.path.ClassName` or `!@module.path.func`
- **Instance Referencing:** Use `${instance}` to reference instantiated objects and their properties. Or `${instance.attr}` to reference attributes of instantiated objects.

## Example

```yaml
include!:
  - examples/base.yml
  - examples/override.yml

testenv: !env MY_TEST_VAR

app:
  name: TestApp
  version: "2.0"
  workers: 4

database:
  pool_size: ${app.workers * 2}           # 4 * 2 = 8
  timeout: ${app.workers + 5}             # 4 + 5 = 9
  max_connections: ${2 ** app.workers}    # 2^4 = 16

paths:
  base: !@pathlib.Path /opt/${app.name}
  data: !@pathlib.Path
    - ${paths.base}
    - data.yml

hostdefault: !@pyamlo.call "${services.main.as_dict}" 

info:
  base_path: ${paths.base}
  data_name: ${paths.data.name}

logs:
  - !@pathlib.Path /logs/${app.name}/main.log
  - !@pathlib.Path /logs/${app.name}/${services.main.host}.log
```

## Installation

```bash
pip install pyamlo
```

## Usage

### Basic Usage
```python
from pyamlo import load_config

config = load_config("examples/test_config.yaml")
print(config)

```
See for more details on the [examples documentation](https://martvanrijthoven.github.io/pyamlo/examples/).

## Development
- **installation:**  
  - `pip install -e ".[test,docs]"`

- **tests:**  
  - `hatch run test:run`

- **docs:**
  - `hatch run docs:build`
  - `hatch run docs:serve`

- **black/ruff/mypy:**
  - `hatch run check:all`