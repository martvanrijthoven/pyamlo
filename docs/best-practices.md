# Best Practices

## Using Environment Variables
- Always provide a default for non-critical env vars:
  ```yaml
  db_url: !env {var: DATABASE_URL, default: "sqlite:///default.db"}
  ```

## Avoiding Common Pitfalls
- Do not use `!patch` unless you want to fully replace a dictionary.
- Use `!extend` only on lists.
- Use `${...}` for referencing both config values and object attributes.

## Testing Configs
- Use PYAMLO in your test suite to validate all config files load and resolve as expected.
- Example pytest:
  ```python
  import pytest
  from pyamlo import load_config
  @pytest.mark.parametrize("fname", ["prod.yaml", "dev.yaml"])
  def test_config_loads(fname):
      with open(fname) as f:
          cfg, _ = load_config(f)
      assert "app" in cfg
  ```

---
