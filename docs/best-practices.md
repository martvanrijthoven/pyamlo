# Best Practices

## Organizing Configurations
- Use `_includes` to split configs by environment, secrets, or team.
- Keep secrets and environment-specific values in separate files, loaded only in relevant environments.

## Using Environment Variables
- Always provide a default for non-critical env vars:
  ```yaml
  db_url: !env {var: DATABASE_URL, default: "sqlite:///default.db"}
  ```

## Instance IDs
- Use `id:` for all important objects/functions you want to reference elsewhere.
- Example:
  ```yaml
  main_db: !@mydb.Database
    dsn: ${db_url}
    id: main_db
  ```

## Avoiding Common Pitfalls
- Do not use `!patch` unless you want to fully replace a dictionary.
- Use `!extend` only on lists.
- Use `${...}` for referencing both config values and object attributes.

## Testing Configs
- Use yamlo in your test suite to validate all config files load and resolve as expected.
- Example pytest:
  ```python
  import pytest
  from yamlo import load_config
  @pytest.mark.parametrize("fname", ["prod.yaml", "dev.yaml"])
  def test_config_loads(fname):
      with open(fname) as f:
          cfg, _ = load_config(f)
      assert "app" in cfg
  ```

---

See [FAQ](faq.md) for troubleshooting and [API Reference](api.md) for more details.
