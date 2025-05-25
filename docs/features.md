# Features

PYAMLO enhances standard YAML loading with several powerful features designed to handle complex configurations.

## Includes (`_includes`)
- Structure your configuration across multiple files using the `_includes` key.
- Files are deep-merged in order, with later files overriding earlier ones.

## Merging Strategies
- **Deep Merge**: Recursively merges dictionaries.
- **List Extension (`!extend`)**: Appends to lists.
- **Dictionary Replacement (`!patch`)**: Replaces dictionaries.

## Environment Variables (`!env`)
- Inject environment variables directly into your config.
- Supports default values: `!env {var: NAME, default: ...}`

## Python Object Instantiation (`!@`)
- Instantiate Python classes or call functions directly from YAML.
- Supports positional, keyword, and scalar arguments.

## Variable Interpolation (`${...}`)
- Reference other config values, including instantiated objects and their properties.

---
