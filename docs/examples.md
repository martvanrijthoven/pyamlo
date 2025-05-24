# Examples

## Minimal Example
```yaml
app:
  name: MinimalApp
  version: 1.0
```

## Multi-file Include
```yaml
_includes:
  - base.yaml
  - override.yaml
```

## Environment Variable with Default
```yaml
api_key: !env {var: API_KEY, default: "not-set"}
```

## Python Object Instantiation
```yaml
log_path: !@pathlib.Path /var/log/myapp.log
```

## Referencing an Instance by ID
```yaml
main_db: !@mydb.Database
  dsn: ${db_url}

worker: !@myapp.Worker
  db: ${main_db}
```

## Full ML Pipeline Example
See [API Reference](api.md) for a full machine learning pipeline config.
