"""Tests for Python dictionary as configuration source."""

import pytest
from pyamlo import load_config
from pyamlo.security import SecurityPolicy


def test_single_dict_source():
    """Test loading configuration from a single dictionary."""
    config_dict = {
        "app": {
            "name": "TestApp",
            "version": "1.0"
        },
        "database": {
            "host": "localhost",
            "port": 5432
        }
    }
    
    result = load_config(config_dict)
    
    assert result["app"]["name"] == "TestApp"
    assert result["app"]["version"] == "1.0"
    assert result["database"]["host"] == "localhost"
    assert result["database"]["port"] == 5432


def test_multiple_dict_sources():
    """Test loading configuration from multiple dictionaries."""
    base_config = {
        "app": {
            "name": "BaseApp",
            "debug": False
        },
        "database": {
            "host": "localhost"
        }
    }
    
    override_config = {
        "app": {
            "debug": True,
            "version": "2.0"
        },
        "database": {
            "port": 5432
        }
    }
    
    result = load_config([base_config, override_config])
    
    assert result["app"]["name"] == "BaseApp"
    assert result["app"]["debug"] is True
    assert result["app"]["version"] == "2.0"
    assert result["database"]["host"] == "localhost"
    assert result["database"]["port"] == 5432


def test_mixed_sources_file_and_dict(tmp_path):
    """Test loading configuration from both file and dictionary sources."""
    yaml_file = tmp_path / "config.yaml"
    yaml_file.write_text("""
app:
  name: FileApp
  workers: 4

database:
  host: file_host
""")
    
    dict_config = {
        "app": {
            "debug": True,
            "version": "3.0"
        },
        "database": {
            "port": 3306
        }
    }
    
    result = load_config([str(yaml_file), dict_config])
    
    assert result["app"]["name"] == "FileApp"
    assert result["app"]["workers"] == 4
    assert result["app"]["debug"] is True
    assert result["app"]["version"] == "3.0"
    assert result["database"]["host"] == "file_host"
    assert result["database"]["port"] == 3306


def test_dict_with_interpolation():
    """Test dictionary source with variable interpolation."""
    config_dict = {
        "app": {
            "name": "TestApp",
            "workers": 4
        },
        "database": {
            "pool_size": "${app.workers * 2}",
            "timeout": "${app.workers + 5}"
        }
    }
    
    result = load_config(config_dict)
    
    assert result["app"]["workers"] == 4
    assert result["database"]["pool_size"] == 8
    assert result["database"]["timeout"] == 9


def test_dict_with_object_instantiation():
    """Test dictionary source with object instantiation."""
    config_dict = {
        "paths": {
            "base": "!@pathlib.Path /tmp/test",
            "data": "!@pathlib.Path /tmp/test/data.txt"
        }
    }
    
    result = load_config(config_dict)
    
    assert str(result["paths"]["base"]) == "/tmp/test"
    assert str(result["paths"]["data"]) == "/tmp/test/data.txt"


def test_empty_dict_source():
    """Test loading configuration from an empty dictionary."""
    result = load_config({})
    assert result == {}


def test_dict_with_security_policy():
    """Test dictionary source with restrictive security policy."""
    config_dict = {
        "safe": {
            "value": "test"
        },
        "unsafe": {
            "path": "!@pathlib.Path /tmp"
        }
    }
    
    restrictive_policy = SecurityPolicy(restrictive=True)
    
    # Should work with non-restrictive policy
    result = load_config(config_dict)
    assert str(result["unsafe"]["path"]) == "/tmp"
    
    # Should fail with restrictive policy
    with pytest.raises(Exception):
        load_config(config_dict, security_policy=restrictive_policy)


def test_nested_dict_merging():
    """Test deep merging of nested dictionaries."""
    config1 = {
        "app": {
            "name": "App1",
            "features": {
                "auth": True,
                "logging": False
            }
        }
    }
    
    config2 = {
        "app": {
            "version": "2.0",
            "features": {
                "logging": True,
                "metrics": True
            }
        }
    }
    
    result = load_config([config1, config2])
    
    assert result["app"]["name"] == "App1"
    assert result["app"]["version"] == "2.0"
    assert result["app"]["features"]["auth"] is True
    assert result["app"]["features"]["logging"] is True
    assert result["app"]["features"]["metrics"] is True