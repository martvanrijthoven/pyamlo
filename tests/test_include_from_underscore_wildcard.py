"""Tests for _ wildcard functionality in !include_from."""

import tempfile
from pathlib import Path
from io import StringIO

import pytest

from pyamlo import load_config


def test_underscore_wildcard_basic(tmp_path):
    """Test that _ wildcard replaces with entire file content."""
    
    # Create a file with multiple keys (no '_' key inside)
    included_content = """
name: test_app
version: 1.0
database:
  host: localhost
  port: 5432
features:
  auth: true
  logging: false
"""
    included_file = tmp_path / "config.yml"
    included_file.write_text(included_content.strip())
    
    # Create main config using _ wildcard
    main_content = f"""
stage:
  steps:
    my_step:
      _: !include_from {included_file}
    
other_config:
  value: 42
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    # Load and verify
    config = load_config(str(main_file))
    
    # Verify structure - _ should be replaced with entire content
    assert "stage" in config
    assert "steps" in config["stage"]
    assert "my_step" in config["stage"]["steps"]
    
    # The _ key should be replaced with the entire included file content
    step_content = config["stage"]["steps"]["my_step"]
    
    # Should contain all keys from included file directly (not under '_')
    assert "name" in step_content
    assert "version" in step_content
    assert "database" in step_content
    assert "features" in step_content
    
    # Most importantly, the _ key itself should NOT be present
    assert "_" not in step_content
    
    # Verify values
    assert step_content["name"] == "test_app"
    assert step_content["version"] == 1.0
    assert step_content["database"]["host"] == "localhost"
    assert step_content["database"]["port"] == 5432
    assert step_content["features"]["auth"] is True
    assert step_content["features"]["logging"] is False
    
    # Verify other config still exists
    assert config["other_config"]["value"] == 42


def test_underscore_wildcard_with_interpolation(tmp_path):
    """Test _ wildcard with variable interpolation."""
    
    # Create included file with interpolated values
    included_content = """
app_name: ${env}_application
database:
  host: ${db_host}
  port: 5432
  url: "postgresql://${db_host}:5432/${env}_db"
"""
    included_file = tmp_path / "config.yml"
    included_file.write_text(included_content.strip())
    
    # Create main config with variables and _ wildcard
    main_content = f"""
env: production
db_host: prod-db.internal

stage:
  steps:
    my_step:
      _: !include_from {included_file}
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    config = load_config(str(main_file))
    
    step_content = config["stage"]["steps"]["my_step"]
    
    # Verify interpolation worked
    assert step_content["app_name"] == "production_application"
    assert step_content["database"]["host"] == "prod-db.internal"
    assert step_content["database"]["url"] == "postgresql://prod-db.internal:5432/production_db"
    
    # Verify _ key is not present
    assert "_" not in step_content


def test_regular_include_from_still_works(tmp_path):
    """Test that regular !include_from (non-_) still works as before."""
    
    # Create included file with specific key
    included_content = """
train_loader:
  batch_size: 64
  shuffle: true

val_loader:
  batch_size: 32
  shuffle: false

_helper:
  internal: config
"""
    included_file = tmp_path / "loaders.yml"
    included_file.write_text(included_content.strip())
    
    # Create main config using specific key (not _)
    main_content = f"""
model:
  type: cnn

train_loader: !include_from {included_file}

optimizer:
  lr: 0.001
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    config = load_config(str(main_file))
    
    # Should only get the train_loader key content, not entire file
    assert "train_loader" in config
    assert config["train_loader"]["batch_size"] == 64
    assert config["train_loader"]["shuffle"] is True
    
    # Should NOT contain other keys from included file
    assert "val_loader" not in config
    assert "_helper" not in config
    
    # Other main config should still be there
    assert config["model"]["type"] == "cnn"
    assert config["optimizer"]["lr"] == 0.001


def test_underscore_wildcard_multiple_files(tmp_path):
    """Test _ wildcard with multiple included files."""
    
    # Create first included file
    first_content = """
database:
  host: db1.example.com
  port: 5432
logging:
  level: INFO
"""
    first_file = tmp_path / "first.yml"
    first_file.write_text(first_content.strip())
    
    # Create second included file
    second_content = """
cache:
  type: redis
  host: cache.example.com
monitoring:
  enabled: true
"""
    second_file = tmp_path / "second.yml"
    second_file.write_text(second_content.strip())
    
    # Create main config with multiple _ wildcards
    main_content = f"""
app:
  name: MultiWildcardApp

stage1:
  _: !include_from {first_file}

stage2:
  _: !include_from {second_file}

final_config:
  complete: true
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    config = load_config(str(main_file))
    
    # Verify first stage got content from first file
    assert "database" in config["stage1"]
    assert "logging" in config["stage1"]
    assert config["stage1"]["database"]["host"] == "db1.example.com"
    assert config["stage1"]["logging"]["level"] == "INFO"
    assert "_" not in config["stage1"]
    
    # Verify second stage got content from second file
    assert "cache" in config["stage2"]
    assert "monitoring" in config["stage2"]
    assert config["stage2"]["cache"]["type"] == "redis"
    assert config["stage2"]["monitoring"]["enabled"] is True
    assert "_" not in config["stage2"]
    
    # Verify other config still exists
    assert config["app"]["name"] == "MultiWildcardApp"
    assert config["final_config"]["complete"] is True


def test_underscore_wildcard_with_nested_structure(tmp_path):
    """Test _ wildcard in deeply nested structures."""
    
    # Create included file
    included_content = """
service:
  name: user-service
  version: 2.1.0
  endpoints:
    health: /health
    metrics: /metrics
database:
  driver: postgresql
  pool_size: 10
"""
    included_file = tmp_path / "service.yml"
    included_file.write_text(included_content.strip())
    
    # Create main config with deeply nested _ wildcard
    main_content = f"""
environment: production
services:
  backend:
    components:
      user_service:
        _: !include_from {included_file}
      auth_service:
        name: auth-service
        version: 1.0.0
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    config = load_config(str(main_file))
    
    # Navigate to deeply nested structure
    user_service = config["services"]["backend"]["components"]["user_service"]
    
    # Verify content was merged at the right level
    assert "service" in user_service
    assert "database" in user_service
    assert user_service["service"]["name"] == "user-service"
    assert user_service["service"]["version"] == "2.1.0"
    assert user_service["database"]["driver"] == "postgresql"
    assert "_" not in user_service
    
    # Verify other service is unaffected
    auth_service = config["services"]["backend"]["components"]["auth_service"]
    assert auth_service["name"] == "auth-service"
    assert auth_service["version"] == "1.0.0"


def test_underscore_wildcard_empty_file(tmp_path):
    """Test _ wildcard with empty included file."""
    
    # Create empty included file (empty YAML dict)
    included_file = tmp_path / "empty.yml"
    included_file.write_text("{}")
    
    # Create main config
    main_content = f"""
app:
  name: EmptyTest

stage:
  _: !include_from {included_file}
  other_key: value
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    config = load_config(str(main_file))
    
    # Empty file should not add any keys, but other keys should remain
    assert "other_key" in config["stage"]
    assert config["stage"]["other_key"] == "value"
    assert "_" not in config["stage"]


def test_underscore_wildcard_file_with_underscore_key(tmp_path):
    """Test that _ wildcard works even when included file has a '_' key."""
    
    # Create included file that actually has a '_' key
    included_content = """
regular_key: regular_value
_: underscore_value
another_key: another_value
"""
    included_file = tmp_path / "with_underscore.yml"
    included_file.write_text(included_content.strip())
    
    # Create main config using _ wildcard
    main_content = f"""
app:
  name: UnderscoreKeyTest

stage:
  _: !include_from {included_file}
"""
    main_file = tmp_path / "main.yml"
    main_file.write_text(main_content.strip())
    
    config = load_config(str(main_file))
    
    # All keys from included file should be present at stage level
    assert "regular_key" in config["stage"]
    assert "_" in config["stage"]  # The original _ key from included file
    assert "another_key" in config["stage"]
    
    # Verify values
    assert config["stage"]["regular_key"] == "regular_value"
    assert config["stage"]["_"] == "underscore_value"
    assert config["stage"]["another_key"] == "another_value"