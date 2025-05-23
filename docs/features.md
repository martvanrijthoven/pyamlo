# Features

Yamlo enhances standard YAML loading with several powerful features designed to handle complex configurations.

## Includes (`_includes`)

You can structure your configuration across multiple files using the `_includes` key. Yamlo will merge these files before processing the rest of the current file.

* **Format:** `_includes` should be a list at the top level of your YAML file.
* **Merging:** Files are deep-merged in the order they appear in the list. Values from later files (including the file containing `_includes`) override values from earlier files.
* **Paths:** Simple string paths are treated as relative to the current working directory by default (or relative to the including file if `yamlo`'s include logic is modified).
* **Package Resources:** You can include files relative to an installed Python package using a `[filepath, package_prefix]` tuple (experimental, behavior might depend on package structure).

**Example:**

```yaml title="base.yaml"
# Common settings
database:
  host: db.prod.local
  port: 5432
  user: prod_user

logging:
  level: INFO
```

```yaml title="development.yaml"
# Override specific settings for development
_includes:
  - base.yaml # Include common settings first

database:
  host: db.dev.local # Override host
  user: dev_user   # Override user
  # port remains 5432 from base.yaml

logging:
  level: DEBUG # Override logging level

app:
  feature_flags:
    new_dashboard: true
```

Loading `development.yaml` would result in a merged configuration containing settings from both files, with development values taking precedence.

## Merging Strategies

By default, Yamlo performs a deep merge for dictionaries when processing includes or resolving nested structures. However, you can control merging behavior for specific keys using `!extend` and `!patch`.

### Default: Deep Merge (Dictionaries)

When dictionaries with the same key exist in included files or are defined multiple times, their contents are recursively merged.

### List Appending (`!extend`)

Use `!extend` on a list value to append its items to the list defined in a previously included file (or the base definition).

```yaml title="base.yaml"
users:
  admins: ['root']
```

```yaml title="override.yaml"
_includes:
  - base.yaml

users:
  admins: !extend ['admin1', 'admin2'] # Append to base list
```

Loading `override.yaml` results in `cfg['users']['admins']` being `['root', 'admin1', 'admin2']`.

### Dictionary Replacement (`!patch`)

Use `!patch` on a dictionary value to completely replace the dictionary defined for that key in previously included files, instead of deep-merging.

```yaml title="base.yaml"
service_config:
  timeout: 30
  retries: 3
  cache:
    enabled: true
    ttl: 3600
```

```yaml title="override.yaml"
_includes:
  - base.yaml

service_config: !patch # Replace the entire service_config dict
  timeout: 60        # Only timeout is defined now
  new_option: "abc"
```

Loading `override.yaml` results in `cfg['service_config']` being `{'timeout': 60, 'new_option': 'abc'}`. The `retries` and `cache` keys from `base.yaml` are gone.

## Environment Variables (`!env`)

You can directly insert the value of environment variables into your configuration.

* **Simple:** `!env VAR_NAME`
    * Reads the value of `VAR_NAME`.
    * Raises a `ResolutionError` if the variable is not set.
* **With Default:** `!env {var: VAR_NAME, default: fallback_value}` or `!env {name: VAR_NAME, default: fallback_value}`
    * Reads the value of `VAR_NAME`.
    * Uses `fallback_value` if the variable is not set. `fallback_value` can be any YAML type (string, number, boolean, null).

**Example:**

```yaml
api_key: !env API_SECRET_KEY # Fails if not set
database_url: !env {var: DATABASE_URL, default: "postgres://localhost/defaultdb"}
feature_enabled: !env {var: ENABLE_BETA, default: false} # Default boolean
max_connections: !env {var: MAX_CONN, default: null} # Default null
```

## Object Instantiation (`!@`)

Yamlo can instantiate Python objects directly from your configuration using the `!@` tag followed by the full Python path to a class or function.

* **Syntax:** `!@full.python.path.to.Callable`
* **Arguments:**
    * **Keyword Arguments:** Provide a mapping after the tag:
        ```yaml
        db_conn: !@mypackage.db.DatabaseConnection
          dsn: ${database_url} # Interpolation works here too!
          timeout: 15
        ```
        This calls `mypackage.db.DatabaseConnection(dsn=resolved_url, timeout=15)`.
    * **Positional Arguments:** Provide a sequence (list) after the tag:
        ```yaml
        data_path: !@pathlib.Path
          - /data
          - processed
          - ${app.name}
        ```
        This calls `pathlib.Path('/data', 'processed', resolved_app_name)`.
    * **Single Scalar Argument:** Provide a scalar value directly:
        ```yaml
        retry_delay: !@float 0.5
        ```
        This calls `float(0.5)`.
* **Instance Tracking (`id`):** When using the mapping syntax for arguments, you can add an `id: unique_instance_name` key. The created object instance will be stored in the `instances` dictionary returned by `load_config` and can be referenced in later interpolations using `${unique_instance_name}`.

**Example with Instance Tracking:**

```yaml
# In test_config.yaml [cite: uploaded:test_config.yaml]
app:
  name: TestApp
  version: "2.0"

services:
  main: !@yamlo.Repository # Assume yamlo.Repository exists [cite: uploaded:resolver.py]
    id: main # Store this instance with id 'main'
    host: main.${app.name}.svc # Interpolate app name
    port: 9000
  secondary: !@yamlo.Repository
    id: secondary # Store this instance with id 'secondary'
    host: secondary.${app.name}.svc
    port: ${services.main.port} # Interpolate attribute from *resolved* main service

pipeline:
  composite:
    first: ${services.main.host} # Interpolate attribute of resolved 'main' service
    second: ${services.secondary} # Reference the *entire* 'secondary' instance object
```

When loading this:
* `cfg['services']['main']` will be a `Repository` instance.
* `instances['main']` will be the *same* `Repository` instance.
* `cfg['pipeline']['composite']['first']` will be the string `"main.TestApp.svc"`.
* `cfg['pipeline']['composite']['second']` will be the actual `Repository` instance stored in `instances['secondary']`.

## Variable Interpolation (`${...}`)

Reference other values within the configuration using the `${path.to.value}` syntax. Interpolation happens *after* includes and merging but *during* the resolution phase, allowing references to values defined earlier in the resolution process, including attributes of instantiated objects.

* **Syntax:** `${key.subkey[index].attribute}` or `${instance_id.attribute}`
* **Resolution Order:** Yamlo attempts to resolve values as it traverses the configuration tree. You can generally reference values defined "above" or "before" the current point in the YAML structure. References to instantiated objects (using their `id`) are resolved via the `instances` dictionary.
* **Full String vs. Substring:**
    * If the *entire* string is an interpolation (e.g., `value: ${path.to.obj}`), the resolved value retains its original type (e.g., an object, list, int).
    * If the interpolation is part of a larger string (e.g., `url: http://${host}:${port}/path`), the resolved values are converted to strings and substituted.

**Example:**

```yaml
app:
  name: MyService
  port: 8080

paths:
  base: /var/log/${app.name} # -> /var/log/MyService (string)

endpoints:
  health: http://localhost:${app.port}/health # -> http://localhost:8080/health (string)

main_log: !@pathlib.Path ${paths.base}.log # -> Path('/var/log/MyService.log') (Path object)
```
