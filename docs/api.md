# API Reference

This section details the public API of the `yamlo` package.

## `load_config`

::: yamlo.config.load_config
    handler: python
    options:
      show_root_heading: false
      show_source: false # Optional: Set true to show source code

## Exceptions

Yamlo uses a hierarchy of custom exceptions to signal different configuration errors. All inherit from `yamlo.errors.ConfigError`.

::: yamlo.errors.ConfigError
    handler: python
    options:
      show_root_heading: true
      heading_level: 3
      members: false # Only show class docstring

::: yamlo.errors.IncludeError
    handler: python
    options:
      show_root_heading: true
      heading_level: 3
      members: false

::: yamlo.errors.MergeError
    handler: python
    options:
      show_root_heading: true
      heading_level: 3
      members: false

::: yamlo.errors.TagError
    handler: python
    options:
      show_root_heading: true
      heading_level: 3
      members: false

::: yamlo.errors.ResolutionError
    handler: python
    options:
      show_root_heading: true
      heading_level: 3
      members: false
