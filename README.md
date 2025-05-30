# PYAMLO: YAML Configuration Loader

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
pip install pyamlo
```

## Usage

### Basic Usage
```python
from pyamlo import load_config

# Single config file
config = load_config("examples/test_config.yaml")
print(config)

# Multiple config files (later files override earlier ones)
config = load_config(["base.yaml", "override.yaml", "local.yaml"])
```

### Command Line Interface
```bash
# Single config file
python -m pyamlo config.yaml

# Multiple config files with CLI overrides
python -m pyamlo base.yaml override.yaml pyamlo.app.name=MyApp pyamlo.debug=true
```

### Order of Operations
PYAMLO processes configuration in the following order:
1. **For each config file**: Load and process `!include` directives (relative to that file's location)
2. **Merge multiple configs**: Later files override earlier ones using deep merge
3. **Apply CLI overrides**: Override specific values from command line
4. **Resolve variables and instantiate objects**: Process `${...}` interpolation and `!@` tags

## Quick Examples

### Multiple Config Files
```python
from pyamlo import load_config

# Load and merge multiple configs
config = load_config(['base.yaml', 'environment.yaml', 'local.yaml'])

# Each file processes includes independently, then they're merged
# Later files override earlier ones
```

### Command Line Usage
```bash
# Single config with overrides
python -m pyamlo config.yaml pyamlo.app.name=MyApp pyamlo.debug=true

# Multiple configs with overrides
python -m pyamlo base.yaml override.yaml pyamlo.database.host=localhost

# Override nested values
python -m pyamlo config.yaml pyamlo.database.connection.timeout=30

# Extend lists
python -m pyamlo config.yaml 'pyamlo.items=!extend [4,5]'

# Patch dictionaries  
python -m pyamlo config.yaml 'pyamlo.settings=!patch {"debug": true}'
```

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