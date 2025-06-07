"""Tests for !include_from positional include functionality."""

import tempfile
from pathlib import Path
from io import StringIO

import pytest

from pyamlo import load_config
from pyamlo.merge import IncludeError
from pyamlo.tags import IncludeFromSpec, construct_include_from, ConfigLoader, TagError
from yaml import ScalarNode, MappingNode


def test_include_from_basic_functionality(tmp_path):
    """Test basic !include_from functionality with positional includes."""
    
    # Create a file to include
    included_content = """
_middleware:
  cache:
    enabled: true
    ttl: 3600
  monitoring:
    enabled: true
    port: 9090
"""
    included_file = tmp_path / "middleware.yml"
    included_file.write_text(included_content.strip())
    
    # Create main config with !include_from
    main_content = f"""
app:
  name: MyApp
  version: 1.0

_middleware: !include_from {included_file}

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
    assert "_middleware" in config  # From included file
    assert "database" in config
    
    # Verify content
    assert config["app"]["name"] == "MyApp"
    assert config["_middleware"]["cache"]["enabled"] is True
    assert config["_middleware"]["monitoring"]["port"] == 9090
    assert config["database"]["host"] == "localhost"
    
    # Verify key order is preserved
    keys = list(config.keys())
    expected_order = ["app", "_middleware", "database"]
    assert keys == expected_order


def test_include_from_with_relative_paths(tmp_path):
    """Test !include_from with relative paths."""
    
    # Create subdirectory
    subdir = tmp_path / "configs"
    subdir.mkdir()
    
    # Create included file in subdirectory
    included_content = """
_shared_config:
  debug: true
  log_level: INFO
"""
    included_file = subdir / "shared.yml"
    included_file.write_text(included_content.strip())
    
    # Create main config that references relative path
    main_content = """
app:
  name: TestApp

_shared_config: !include_from configs/shared.yml

database:
  host: localhost
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    config = load_config(str(main_file))
    
    assert "_shared_config" in config
    assert config["_shared_config"]["debug"] is True


def test_include_from_file_not_found(tmp_path):
    """Test error handling when included file doesn't exist."""
    
    main_content = """
app:
  name: TestApp

_missing: !include_from nonexistent.yml

database:
  host: localhost
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    with pytest.raises(IncludeError, match="Include file not found"):
        load_config(str(main_file))


def test_include_from_multiple_positions(tmp_path):
    """Test multiple !include_from tags at different positions."""
    
    # Create first included file
    first_content = """
_cache_config:
  type: redis
  host: localhost
"""
    first_file = tmp_path / "cache.yml"
    first_file.write_text(first_content.strip())
    
    # Create second included file  
    second_content = """
_logging_config:
  level: INFO
  handlers: [console, file]
"""
    second_file = tmp_path / "logging.yml"
    second_file.write_text(second_content.strip())
    
    # Create main config with multiple includes
    main_content = f"""
app:
  name: MultiIncludeApp

_cache_config: !include_from {first_file}

database:
  host: db.example.com

_logging_config: !include_from {second_file}

monitoring:
  enabled: true
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    config = load_config(str(main_file))
    
    # Verify all content is present
    assert "app" in config
    assert "_cache_config" in config
    assert "database" in config
    assert "_logging_config" in config
    assert "monitoring" in config
    
    # Verify correct order
    keys = list(config.keys())
    expected_order = ["app", "_cache_config", "database", "_logging_config", "monitoring"]
    assert keys == expected_order


def test_include_from_construct_function():
    """Test the construct_include_from function directly."""
    
    # Test valid usage
    loader = ConfigLoader("")
    node = ScalarNode("!include_from", "test.yml")
    result = construct_include_from(loader, node)
    
    assert isinstance(result, IncludeFromSpec)
    assert result.path == "test.yml"
    
    # Test invalid usage (non-scalar node)
    mapping_node = MappingNode("!include_from", [])
    with pytest.raises(TagError, match="!include_from must be used with a file path"):
        construct_include_from(loader, mapping_node)


def test_include_from_with_base_path():
    """Test that base paths are properly set and used."""
    spec = IncludeFromSpec("test.yml")
    assert spec._base_path is None
    
    spec.set_base_path("/path/to/config.yml")
    assert spec._base_path == "/path/to/config.yml"


def test_include_from_with_string_io():
    """Test !include_from functionality with StringIO sources."""
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create included file
        included_content = """
_middleware:
  cors: true
  timeout: 30
"""
        included_file = tmp_path / "middleware.yml"
        included_file.write_text(included_content.strip())
        
        # Create main config content
        main_content = f"""
app:
  name: StringIOApp

_middleware: !include_from {included_file}

database:
  host: localhost
"""
        
        # Test with StringIO
        config = load_config(StringIO(main_content))
        
        assert "_middleware" in config
        assert config["_middleware"]["cors"] is True


def test_include_from_with_variable_interpolation(tmp_path):
    """Test !include_from with variable interpolation in file paths."""
    
    # Create included file
    included_content = """
_db_config:
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

_db_config: !include_from ${{env}}_db.yml

monitoring:
  enabled: true
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    config = load_config(str(main_file))
    
    # Verify content is included and variables are interpolated
    assert "_db_config" in config
    assert config["_db_config"]["host"] == "prod_db.example.com"
    assert config["_db_config"]["ssl"] is True


def test_include_from_with_nested_variable_interpolation(tmp_path):
    """Test !include_from with nested variable references."""
    
    # Create included file
    included_content = """
_api_settings:
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

_api_settings: !include_from ${{service_type}}_config.yml

app:
  name: NestedVarApp
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    config = load_config(str(main_file))
    
    # Verify nested interpolation works
    assert "_api_settings" in config
    assert config["_api_settings"]["base_url"] == "https://api.example.com/api"


def test_include_from_with_missing_variable(tmp_path):
    """Test error handling when variable is missing for interpolation."""
    
    # Create main config with undefined variable
    main_content = """
app:
  name: MissingVarApp

_config: !include_from ${undefined_var}_config.yml

database:
  host: localhost
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    # Should raise an error for undefined variable
    with pytest.raises(IncludeError, match="Unresolved variables"):
        load_config(str(main_file))


def test_include_from_with_complex_path_interpolation(tmp_path):
    """Test !include_from with complex path interpolation patterns."""
    
    # Create subdirectories
    env_dir = tmp_path / "configs" / "production"
    env_dir.mkdir(parents=True)
    
    # Create included file in nested directory
    included_content = """
_cache_config:
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

_cache_config: !include_from configs/${environment}/${service}.yml

monitoring:
  enabled: true
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    config = load_config(str(main_file))
    
    # Verify complex path interpolation works
    assert "_cache_config" in config
    assert config["_cache_config"]["host"] == "prod-redis.internal"
    assert config["_cache_config"]["cluster"] is True


def test_include_from_variable_interpolation_within_included_files(tmp_path):
    """Test that variable interpolation works within included files."""
    
    # Create included file with variables
    included_content = """
_service_config:
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

_service_config: !include_from service.yml

monitoring:
  enabled: true
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    config = load_config(str(main_file))
    
    # Verify variables in included file are interpolated
    assert "_service_config" in config
    assert config["_service_config"]["service"]["name"] == "myapp-service"
    assert config["_service_config"]["service"]["port"] == 8080
    assert config["_service_config"]["database"]["url"] == "postgresql://admin:secret123@db.internal:5432/myapp_prod"


def test_include_from_with_recursive_includes(tmp_path):
    """Test !include_from working within traditionally included files."""
    
    # Create the deepest included file
    deep_content = """
_metrics:
  prometheus: true
  port: 9090
"""
    deep_file = tmp_path / "metrics.yml"
    deep_file.write_text(deep_content.strip())
    
    # Create middle include file that uses include_from
    middle_content = f"""
middleware:
  cors: true
  rate_limit: 100

_metrics: !include_from metrics.yml

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
    assert "_metrics" in config["middleware"]  # From include_from within included file
    assert "middleware" in config["middleware"]  # Original middleware content
    assert "security" in config["middleware"]
    assert "database" in config
    
    # Verify content
    assert config["middleware"]["middleware"]["cors"] is True
    assert config["middleware"]["_metrics"]["prometheus"] is True
    assert config["middleware"]["security"]["auth_required"] is True


def test_include_from_error_handling_invalid_yaml(tmp_path):
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

_invalid: !include_from invalid.yml

database:
  host: localhost
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    # Should handle YAML parsing errors gracefully
    with pytest.raises((IncludeError, Exception)):  # Could be various YAML parsing errors
        load_config(str(main_file))


def test_include_from_preserves_order_with_mixed_content(tmp_path):
    """Test that !include_from preserves order when mixed with regular content."""
    
    # Create multiple include files
    first_content = "_first:\n  value: 1"
    second_content = "_second:\n  value: 2"
    third_content = "_third:\n  value: 3"
    
    first_file = tmp_path / "first.yml"
    second_file = tmp_path / "second.yml"  
    third_file = tmp_path / "third.yml"
    
    first_file.write_text(first_content)
    second_file.write_text(second_content)
    third_file.write_text(third_content)
    
    # Create main config with mixed include_from and regular content
    main_content = f"""
start:
  marker: begin

_first: !include_from first.yml

middle1:
  regular: content1

_second: !include_from second.yml

middle2:
  regular: content2

_third: !include_from third.yml

end:
  marker: finish
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    config = load_config(str(main_file))
    
    # Verify order is preserved
    keys = list(config.keys())
    expected_order = ["start", "_first", "middle1", "_second", "middle2", "_third", "end"]
    assert keys == expected_order
    
    # Verify content
    assert config["_first"]["value"] == 1
    assert config["_second"]["value"] == 2
    assert config["_third"]["value"] == 3
    assert config["middle1"]["regular"] == "content1"


def test_include_from_improved_error_messages(tmp_path):
    """Test improved error messages for include_from failures."""
    
    # Test unresolved variables with helpful context
    main_content = """
app:
  name: TestApp

_config: !include_from configs/${environment}/${missing_var}.yml

database:
  host: localhost
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    with pytest.raises(IncludeError, match=r"Unresolved variables.*missing_var.*Available.*app"):
        load_config(str(main_file))


def test_include_from_file_not_found_with_resolution_info(tmp_path):
    """Test file not found error with variable resolution information."""
    
    main_content = """
env: production
service: api

_config: !include_from configs/${env}/${service}.yml
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    with pytest.raises(IncludeError, match=r"Include file not found.*configs/production/api\.yml"):
        load_config(str(main_file))


def test_include_from_invalid_tag_usage():
    """Test error handling for invalid !include_from tag usage."""
    
    # Test with mapping instead of scalar
    yaml_content = """
app:
  name: TestApp

_config: !include_from
  path: config.yml
  invalid: true
"""
    
    with pytest.raises(TagError, match=r"!include_from must be used with a file path.*line \d+"):
        load_config(StringIO(yaml_content))


def test_include_from_empty_path():
    """Test error handling for empty file path."""
    
    yaml_content = """
app:
  name: TestApp

_config: !include_from ""
"""
    
    with pytest.raises(TagError, match=r"!include_from requires a non-empty file path.*line \d+"):
        load_config(StringIO(yaml_content))


def test_include_from_key_validation_success(tmp_path):
    """Test that !include_from validates keys correctly when they match expectations."""
    
    # Create included file with expected keys only
    included_content = """
train_loader:
  batch_size: 64
  shuffle: true

val_loader:
  batch_size: 32
  shuffle: false

# Helper key starting with underscore is allowed
_shared_config:
  timeout: 30
"""
    included_file = tmp_path / "loaders.yml"
    included_file.write_text(included_content.strip())
    
    # Create main config with expected keys specified
    main_content = f"""
app:
  name: ValidationApp

train_loader, val_loader: !include_from {included_file}

model:
  type: cnn
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    # Should succeed without error
    config = load_config(str(main_file))
    
    assert "train_loader" in config
    assert "val_loader" in config
    assert config["train_loader"]["batch_size"] == 64
    assert config["val_loader"]["batch_size"] == 32
    assert "_shared_config" in config  # Underscore keys are included


def test_include_from_key_validation_failure(tmp_path):
    """Test that !include_from raises error when included file has unexpected keys."""
    
    # Create included file with unexpected key
    included_content = """
train_loader:
  batch_size: 64
  shuffle: true

val_loader:
  batch_size: 32
  shuffle: false

# This key is not expected and should cause validation error
unexpected_key:
  value: "should cause error"

# Helper key starting with underscore is allowed
_helper:
  config: value  
"""
    included_file = tmp_path / "loaders.yml"
    included_file.write_text(included_content.strip())
    
    # Create main config with expected keys specified
    main_content = f"""
app:
  name: ValidationApp

train_loader, val_loader: !include_from {included_file}

model:
  type: cnn
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    # Should raise IncludeError about unexpected key
    with pytest.raises(IncludeError, match="unexpected_key.*Expected keys.*train_loader.*val_loader"):
        load_config(str(main_file))


def test_include_from_key_validation_missing_expected(tmp_path):
    """Test that !include_from handles missing expected keys gracefully."""
    
    # Create included file missing one expected key
    included_content = """
train_loader:
  batch_size: 64
  shuffle: true

# val_loader is missing but should be allowed (not strict requirement)

_helper:
  config: value  
"""
    included_file = tmp_path / "loaders.yml"
    included_file.write_text(included_content.strip())
    
    # Create main config with expected keys specified
    main_content = f"""
app:
  name: ValidationApp

train_loader, val_loader: !include_from {included_file}

model:
  type: cnn
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    # Should succeed (missing keys are allowed, only extra unexpected keys cause errors)
    config = load_config(str(main_file))
    
    assert "train_loader" in config
    assert "val_loader" not in config  # Missing from included file, so not in result


def test_include_from_single_key_validation(tmp_path):
    """Test that !include_from validates single key without comma syntax."""
    
    # Create included file with matching key
    included_content = """
config:
  database_url: postgres://localhost
  timeout: 30

_helper:
  internal: true
"""
    included_file = tmp_path / "config.yml"
    included_file.write_text(included_content.strip())
    
    # Create main config using single key syntax
    main_content = f"""
app:
  name: SingleKeyApp

config: !include_from {included_file}

model:
  type: cnn
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    # Should succeed
    config = load_config(str(main_file))
    
    assert "config" in config
    assert config["config"]["database_url"] == "postgres://localhost"
    assert "_helper" in config


def test_include_from_single_key_validation_failure(tmp_path):
    """Test that !include_from validates single key and fails with wrong key."""
    
    # Create included file with wrong key
    included_content = """
wrong_key:
  value: 1

_helper:
  internal: true
"""
    included_file = tmp_path / "config.yml"
    included_file.write_text(included_content.strip())
    
    # Create main config expecting "config" but file contains "wrong_key"
    main_content = f"""
app:
  name: SingleKeyApp

config: !include_from {included_file}

model:
  type: cnn
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    # Should fail validation
    with pytest.raises(IncludeError, match="wrong_key.*Expected keys.*config"):
        load_config(str(main_file))


def test_include_from_single_key_validation_multiple_keys_failure(tmp_path):
    """Test that !include_from single key validation fails when file has multiple unexpected keys."""
    
    # Create included file with multiple keys but only one expected
    included_content = """
config:
  database_url: postgres://localhost

unexpected_key:
  value: 1

another_unexpected:
  value: 2

_helper:
  internal: true
"""
    included_file = tmp_path / "config.yml"
    included_file.write_text(included_content.strip())
    
    # Create main config expecting only "config"
    main_content = f"""
app:
  name: SingleKeyApp

config: !include_from {included_file}

model:
  type: cnn
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    # Should fail validation
    with pytest.raises(IncludeError, match="another_unexpected.*unexpected_key.*Expected keys.*config"):
        load_config(str(main_file))
