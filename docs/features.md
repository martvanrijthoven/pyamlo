# Features

Yamlo enhances standard YAML loading with several powerful features designed to handle complex configurations.

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

## Variable Interpolation (`${...}`)
- Reference other config values, including attributes of instantiated objects.

## Python Object Instantiation (`!@`)
- Instantiate Python classes or call functions directly from YAML.
- Supports positional, keyword, and scalar arguments.
- Track instances by ID for later reference.

## Instance Tracking
- Store and reference instantiated objects by ID for advanced workflows.

---

See [API Reference](api.md) for advanced usage and examples.
