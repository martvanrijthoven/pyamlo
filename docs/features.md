# Features

PYAMLO enhances standard YAML loading with several powerful features designed to handle complex configurations.



## Includes (`include!`)
- Structure your configuration across multiple files using the `include!` key.
- Files are deep-merged in order, with later files overriding earlier ones.


## Multiple Config Files
- Load and merge multiple configuration files in a single call.
- Each file processes `!include` directives independently relative to its own location.
- Files are merged in order with later files overriding earlier ones.
- Perfect for environment-specific overrides, user customizations, and modular configurations.

```python
# Load base config, then environment-specific, then user overrides
config = load_config(['base.yaml', 'production.yaml', 'user-override.yaml'])
```

## Merging Strategies
- **Deep Merge**: Recursively merges dictionaries.
- **List Extension (`!extend`)**: Appends to lists.
- **Dictionary Replacement (`!patch`)**: Replaces dictionaries.

## Environment Variables (`!env`)
- Inject environment variables directly into your config.
- Supports default values: `!env {var: NAME, default: ...}`

## Python Module Import (`!import`)
- Import Python modules, classes, or functions without instantiation.

## Python Object Instantiation (`!@`)
- Instantiate Python classes or call functions directly from YAML.
- Supports positional, keyword, and scalar arguments.

## Variable Interpolation (`${...}`)
- Reference other config values, including instantiated objects and their properties.

## CLI Overrides
Override configuration values via command-line arguments using the `pyamlo.` prefix:

```bash
# Single config with overrides
python -m pyamlo config.yml pyamlo.app.name=MyApp pyamlo.database.host=localhost

# Multiple configs with overrides (configs are merged first, then overrides applied)
python -m pyamlo base.yml production.yml pyamlo.debug=true pyamlo.database.pool_size=20

# Use with special tags
python -m pyamlo config.yml 'pyamlo.items=!extend [4,5]' 'pyamlo.settings=!patch {"debug": true}'
```

### Order of Operations
1. **Include Processing**: Each config file processes its own `!include` directives
2. **Config Merging**: Multiple config files are merged in order (left to right)
3. **CLI Overrides**: Command-line overrides are applied last
4. **Resolution**: Variable interpolation and object instantiation occur

CLI overrides support all YAML features and take precedence over file-based configuration.
