# Yamlo: Flexible YAML Configuration Loader

[![PyPI - Version](https://img.shields.io/pypi/v/yamlo)](https://pypi.org/project/yamlo/) # Add after publishing
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/yamlo)](https://pypi.org/project/yamlo/) # Add after publishing
[![Tests](https://github.com/your-username/yamlo/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/yamlo/actions/workflows/ci.yml) # CHANGE THIS
[![License](https://img.shields.io/pypi/l/yamlo)](./LICENSE) # Add after publishing

`yamlo` provides a way to load YAML configuration files with enhanced features like:

* **Includes:** Merge multiple YAML files using `_includes`.
* **Merging:** Deep merge dictionaries, extend lists (`!extend`), and replace dictionaries (`!patch`).
* **Environment Variables:** Substitute values using `!env VAR_NAME` or `!env {var: NAME, default: ...}`.
* **Variable Interpolation:** Reference other configuration values using `${path.to.value}` syntax.
* **Object Instantiation:** Create Python objects directly from YAML using `!@module.path.ClassName` with arguments and keyword arguments. Store instances with IDs for later reference.

## Installation

```bash
# Using uv (recommended)
uv pip install yamlo

# Using pip
pip install yamlo