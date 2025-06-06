"""Tests for !include_at positional include functionality."""

import tempfile
from pathlib import Path
from io import StringIO

import pytest

from pyamlo import load_config
from pyamlo.merge import IncludeError
from pyamlo.tags import IncludeAtSpec, construct_include_at, ConfigLoader, TagError
from yaml import ScalarNode, MappingNode


def test_include_at_basic_functionality(tmp_path):
    """Test basic !include_at functionality with positional includes."""
    
    # Create a file to include
    included_content = """
cache:
  enabled: true
  ttl: 3600

monitoring:
  enabled: true
  port: 9090
"""
    included_file = tmp_path / "middleware.yml"
    included_file.write_text(included_content.strip())
    
    # Create main config with !include_at
    main_content = f"""
app:
  name: MyApp
  version: 1.0

_middleware: !include_at {included_file}

database:
  host: localhost
  port: 5432
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    # Load and verify
    config = load_config(str(main_file))
    
    # Verify the content is included at the right position
    assert "app" in config
    assert "cache" in config  # From included file
    assert "monitoring" in config  # From included file
    assert "database" in config
    
    # Verify the _middleware key is not present (it should be consumed)
    assert "_middleware" not in config
    
    # Verify content
    assert config["app"]["name"] == "MyApp"
    assert config["cache"]["enabled"] is True
    assert config["monitoring"]["port"] == 9090
    assert config["database"]["host"] == "localhost"
    
    # Verify key order is preserved
    keys = list(config.keys())
    expected_order = ["app", "cache", "monitoring", "database"]
    assert keys == expected_order


def test_include_at_with_relative_paths(tmp_path):
    """Test !include_at with relative paths."""
    
    # Create subdirectory
    subdir = tmp_path / "configs"
    subdir.mkdir()
    
    # Create included file in subdirectory
    included_content = """
shared:
  debug: true
  log_level: INFO
"""
    included_file = subdir / "shared.yml"
    included_file.write_text(included_content.strip())
    
    # Create main config that references relative path
    main_content = """
app:
  name: TestApp

_shared_config: !include_at configs/shared.yml

database:
  host: localhost
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    config = load_config(str(main_file))
    
    assert "shared" in config
    assert config["shared"]["debug"] is True
    assert "_shared_config" not in config


def test_include_at_file_not_found(tmp_path):
    """Test error handling when included file doesn't exist."""
    
    main_content = """
app:
  name: TestApp

_missing: !include_at nonexistent.yml

database:
  host: localhost
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    with pytest.raises(IncludeError, match="Include file not found"):
        load_config(str(main_file))


def test_include_at_multiple_positions(tmp_path):
    """Test multiple !include_at tags at different positions."""
    
    # Create first included file
    first_content = """
cache:
  type: redis
  host: localhost
"""
    first_file = tmp_path / "cache.yml"
    first_file.write_text(first_content.strip())
    
    # Create second included file  
    second_content = """
logging:
  level: INFO
  handlers: [console, file]
"""
    second_file = tmp_path / "logging.yml"
    second_file.write_text(second_content.strip())
    
    # Create main config with multiple includes
    main_content = f"""
app:
  name: MultiIncludeApp

_cache_config: !include_at {first_file}

database:
  host: db.example.com

_logging_config: !include_at {second_file}

monitoring:
  enabled: true
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    config = load_config(str(main_file))
    
    # Verify all content is present
    assert "app" in config
    assert "cache" in config
    assert "database" in config
    assert "logging" in config
    assert "monitoring" in config
    
    # Verify include keys are not present
    assert "_cache_config" not in config
    assert "_logging_config" not in config
    
    # Verify correct order
    keys = list(config.keys())
    expected_order = ["app", "cache", "database", "logging", "monitoring"]
    assert keys == expected_order


def test_include_at_construct_function():
    """Test the construct_include_at function directly."""
    
    # Test valid usage
    loader = ConfigLoader("")
    node = ScalarNode("!include_at", "test.yml")
    result = construct_include_at(loader, node)
    
    assert isinstance(result, IncludeAtSpec)
    assert result.path == "test.yml"
    
    # Test invalid usage (non-scalar node)
    mapping_node = MappingNode("!include_at", [])
    with pytest.raises(TagError, match="!include_at must be used with a file path"):
        construct_include_at(loader, mapping_node)


def test_include_at_with_base_path():
    """Test that base paths are properly set and used."""
    spec = IncludeAtSpec("test.yml")
    assert spec._base_path is None
    
    spec.set_base_path("/path/to/config.yml")
    assert spec._base_path == "/path/to/config.yml"


def test_include_at_with_string_io():
    """Test !include_at functionality with StringIO sources."""
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create included file
        included_content = """
middleware:
  cors: true
  timeout: 30
"""
        included_file = tmp_path / "middleware.yml"
        included_file.write_text(included_content.strip())
        
        # Create main config content
        main_content = f"""
app:
  name: StringIOApp

_middleware: !include_at {included_file}

database:
  host: localhost
"""
        
        # Test with StringIO
        config = load_config(StringIO(main_content))
        
        assert "middleware" in config
        assert config["middleware"]["cors"] is True
        assert "_middleware" not in config


def test_include_at_with_variable_interpolation(tmp_path):
    """Test !include_at with variable interpolation in file paths."""
    
    # Create included file
    included_content = """
database:
  host: ${env}_db.example.com
  port: 5432
  ssl: true
"""
    included_file = tmp_path / "prod_db.yml"
    included_file.write_text(included_content.strip())
    
    # Create main config with variable interpolation in include path
    main_content = f"""
env: prod
app:
  name: VarApp

_db_config: !include_at ${{env}}_db.yml

monitoring:
  enabled: true
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    config = load_config(str(main_file))
    
    # Verify content is included and variables are interpolated
    assert "database" in config
    assert config["database"]["host"] == "prod_db.example.com"
    assert config["database"]["ssl"] is True
    assert "_db_config" not in config


def test_include_at_with_nested_variable_interpolation(tmp_path):
    """Test !include_at with nested variable references."""
    
    # Create included file
    included_content = """
api:
  base_url: https://${subdomain}.${domain}/api
  version: v1
"""
    included_file = tmp_path / "api_config.yml"
    included_file.write_text(included_content.strip())
    
    # Create main config with multiple variables
    main_content = f"""
domain: example.com
subdomain: api
service_type: api

_api_settings: !include_at ${{service_type}}_config.yml

app:
  name: NestedVarApp
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    config = load_config(str(main_file))
    
    # Verify nested interpolation works
    assert "api" in config
    assert config["api"]["base_url"] == "https://api.example.com/api"
    assert "_api_settings" not in config


def test_include_at_with_missing_variable(tmp_path):
    """Test error handling when variable is missing for interpolation."""
    
    # Create main config with undefined variable
    main_content = """
app:
  name: MissingVarApp

_config: !include_at ${undefined_var}_config.yml

database:
  host: localhost
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    # Should raise an error for undefined variable
    with pytest.raises(IncludeError, match="Unresolved variables"):
        load_config(str(main_file))


def test_include_at_with_complex_path_interpolation(tmp_path):
    """Test !include_at with complex path interpolation patterns."""
    
    # Create subdirectories
    env_dir = tmp_path / "configs" / "production"
    env_dir.mkdir(parents=True)
    
    # Create included file in nested directory
    included_content = """
redis:
  host: prod-redis.internal
  port: 6379
  cluster: true
"""
    included_file = env_dir / "cache.yml"
    included_file.write_text(included_content.strip())
    
    # Create main config with complex path interpolation
    main_content = """
environment: production
service: cache

app:
  name: ComplexPathApp

_cache_config: !include_at configs/${environment}/${service}.yml

monitoring:
  enabled: true
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    config = load_config(str(main_file))
    
    # Verify complex path interpolation works
    assert "redis" in config
    assert config["redis"]["host"] == "prod-redis.internal"
    assert config["redis"]["cluster"] is True
    assert "_cache_config" not in config


def test_include_at_variable_interpolation_within_included_files(tmp_path):
    """Test that variable interpolation works within included files."""
    
    # Create included file with variables
    included_content = """
service:
  name: ${app_name}-service
  port: ${service_port}
  replicas: 3

database:
  url: postgresql://${db_user}:${db_pass}@${db_host}:5432/${db_name}
"""
    included_file = tmp_path / "service.yml"
    included_file.write_text(included_content.strip())
    
    # Create main config
    main_content = f"""
app_name: myapp
service_port: 8080
db_user: admin
db_pass: secret123
db_host: db.internal
db_name: myapp_prod

_service_config: !include_at service.yml

monitoring:
  enabled: true
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    config = load_config(str(main_file))
    
    # Verify variables in included file are interpolated
    assert "service" in config
    assert config["service"]["name"] == "myapp-service"
    assert config["service"]["port"] == 8080
    assert config["database"]["url"] == "postgresql://admin:secret123@db.internal:5432/myapp_prod"
    assert "_service_config" not in config


def test_include_at_with_recursive_includes(tmp_path):
    """Test !include_at working within traditionally included files."""
    
    # Create the deepest included file
    deep_content = """
metrics:
  prometheus: true
  port: 9090
"""
    deep_file = tmp_path / "metrics.yml"
    deep_file.write_text(deep_content.strip())
    
    # Create middle include file that uses include_at
    middle_content = f"""
middleware:
  cors: true
  rate_limit: 100

_metrics: !include_at metrics.yml

security:
  auth_required: true
"""
    middle_file = tmp_path / "middleware.yml"
    middle_file.write_text(middle_content.strip())
    
    # Create main config with traditional include
    main_content = f"""
app:
  name: RecursiveApp

middleware: !include {middle_file}

database:
  host: localhost
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    config = load_config(str(main_file))
    
    # Verify all levels of inclusion work
    assert "app" in config
    assert "middleware" in config
    assert "metrics" in config["middleware"]  # From include_at within included file
    assert "middleware" in config["middleware"]  # Original middleware content
    assert "security" in config["middleware"]
    assert "database" in config
    
    # Verify include_at key is consumed within the middleware section
    assert "_metrics" not in config["middleware"]
    
    # Verify content
    assert config["middleware"]["middleware"]["cors"] is True
    assert config["middleware"]["metrics"]["prometheus"] is True
    assert config["middleware"]["security"]["auth_required"] is True


def test_include_at_error_handling_invalid_yaml(tmp_path):
    """Test error handling when included file contains invalid YAML."""
    
    # Create file with invalid YAML
    invalid_content = """
invalid: yaml content
  - missing proper indentation
    nested: but wrong
"""
    invalid_file = tmp_path / "invalid.yml"
    invalid_file.write_text(invalid_content)
    
    # Create main config
    main_content = f"""
app:
  name: InvalidYamlApp

_invalid: !include_at invalid.yml

database:
  host: localhost
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    # Should handle YAML parsing errors gracefully
    with pytest.raises((IncludeError, Exception)):  # Could be various YAML parsing errors
        load_config(str(main_file))


def test_include_at_preserves_order_with_mixed_content(tmp_path):
    """Test that !include_at preserves order when mixed with regular content."""
    
    # Create multiple include files
    first_content = "first:\n  value: 1"
    second_content = "second:\n  value: 2"
    third_content = "third:\n  value: 3"
    
    first_file = tmp_path / "first.yml"
    second_file = tmp_path / "second.yml"  
    third_file = tmp_path / "third.yml"
    
    first_file.write_text(first_content)
    second_file.write_text(second_content)
    third_file.write_text(third_content)
    
    # Create main config with mixed include_at and regular content
    main_content = f"""
start:
  marker: begin

_first: !include_at first.yml

middle1:
  regular: content1

_second: !include_at second.yml

middle2:
  regular: content2

_third: !include_at third.yml

end:
  marker: finish
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    config = load_config(str(main_file))
    
    # Verify order is preserved
    keys = list(config.keys())
    expected_order = ["start", "first", "middle1", "second", "middle2", "third", "end"]
    assert keys == expected_order
    
    # Verify include keys are not present
    for key in ["_first", "_second", "_third"]:
        assert key not in config
    
    # Verify content
    assert config["first"]["value"] == 1
    assert config["second"]["value"] == 2
    assert config["third"]["value"] == 3
    assert config["middle1"]["regular"] == "content1"


def test_include_at_improved_error_messages(tmp_path):
    """Test improved error messages for include_at failures."""
    
    # Test unresolved variables with helpful context
    main_content = """
app:
  name: TestApp

_config: !include_at configs/${environment}/${missing_var}.yml

database:
  host: localhost
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    with pytest.raises(IncludeError, match=r"Unresolved variables.*missing_var.*Available.*app"):
        load_config(str(main_file))


def test_include_at_file_not_found_with_resolution_info(tmp_path):
    """Test file not found error with variable resolution information."""
    
    main_content = """
env: production
service: api

_config: !include_at configs/${env}/${service}.yml
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    with pytest.raises(IncludeError, match=r"Include file not found.*configs/production/api\.yml"):
        load_config(str(main_file))


def test_include_at_invalid_tag_usage():
    """Test error handling for invalid !include_at tag usage."""
    
    # Test with mapping instead of scalar
    yaml_content = """
app:
  name: TestApp

_config: !include_at
  path: config.yml
  invalid: true
"""
    
    with pytest.raises(TagError, match=r"!include_at must be used with a file path.*line \d+"):
        load_config(StringIO(yaml_content))


def test_include_at_empty_path():
    """Test error handling for empty file path."""
    
    yaml_content = """
app:
  name: TestApp

_config: !include_at ""
"""
    
    with pytest.raises(TagError, match=r"!include_at requires a non-empty file path.*line \d+"):
        load_config(StringIO(yaml_content))
