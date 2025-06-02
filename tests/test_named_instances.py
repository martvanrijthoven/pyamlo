"""Test named instances feature and namespace resolution."""

import pytest
from io import StringIO
from pyamlo import load_config
from pyamlo.resolve import Resolver


def test_basic_named_instances():
    """Test basic named instances with explicit IDs."""
    yaml_content = """
database: !@dict
  id: "primary_db"
  host: "localhost"
  port: 5432

cache: !@dict
  id: "redis_cache"
  host: "cache.example.com"
  port: 6379

# Reference by explicit ID
app:
  db_connection: "${primary_db.host}:${primary_db.port}"
  cache_url: "${redis_cache.host}:${redis_cache.port}"

# Reference by path
local_db_host: "${database.host}"
"""
    
    config = load_config(StringIO(yaml_content))
    
    assert config["app"]["db_connection"] == "localhost:5432"
    assert config["app"]["cache_url"] == "cache.example.com:6379"
    assert config["local_db_host"] == "localhost"


def test_namespace_resolution_priority():
    """Test that context takes precedence over instances."""
    yaml_content = """
# Create a named instance
server: !@dict
  id: "config"
  value: "from_instance"

# Create structured data with same key
config:
  value: "from_context"

# This should resolve from context, not instance
result: "${config.value}"
"""
    
    config = load_config(StringIO(yaml_content))
    
    # Should get value from context (structured data), not instance
    assert config["result"] == "from_context"


def test_instances_fallback():
    """Test that instances are used when context doesn't have the key."""
    yaml_content = """
database: !@dict
  id: "unique_db_id"
  host: "db.example.com"

# Reference by ID (not available in context)
connection: "${unique_db_id.host}"
"""
    
    config = load_config(StringIO(yaml_content))
    
    assert config["connection"] == "db.example.com"


def test_instances_with_includes():
    """Test that named instances work correctly with includes."""
    # Test with actual multiple config loading
    base_yaml = """
shared_db: !@dict
  id: "main_database"
  host: "base-host"
  port: 5432

app:
  name: "BaseApp"
"""
    
    override_yaml = """
# Override the app name in context
app:
  name: "ProductionApp"
  # Reference the named instance from base
  db_url: "${main_database.host}:${main_database.port}"
"""
    
    # Load multiple configs together (like including)
    config = load_config([StringIO(base_yaml), StringIO(override_yaml)])
    
    assert config["app"]["name"] == "ProductionApp"
    assert config["app"]["db_url"] == "base-host:5432"


def test_id_conflicts():
    """Test behavior when multiple objects have the same ID."""
    yaml_content = """
obj1: !@dict
  id: "shared_id"
  value: "first"

obj2: !@dict
  id: "shared_id" 
  value: "second"

# Should get the last one (typical dict behavior)
result: "${shared_id.value}"
"""
    
    config = load_config(StringIO(yaml_content))
    
    # Should get the last instance with that ID
    assert config["result"] == "second"


def test_resolver_instances_dict():
    """Test that resolver properly stores named instances."""
    resolver = Resolver()
    
    yaml_data = {
        "database": {
            "_type": "CallSpec",
            "path": "dict",
            "args": [],
            "kwargs": {"host": "localhost", "port": 5432},
            "id": "primary_db"
        }
    }
    
    # Manually create CallSpec for testing
    from pyamlo.tags import CallSpec
    call_spec = CallSpec("dict", [], {"host": "localhost", "port": 5432}, "primary_db")
    
    result = resolver.resolve(call_spec, "database")
    
    # Check that instance was stored with the ID
    assert "primary_db" in resolver.instances
    assert resolver.instances["primary_db"]["host"] == "localhost"
    assert resolver.instances["primary_db"]["port"] == 5432


def test_complex_cross_references():
    """Test complex cross-references between named instances."""
    yaml_content = """
db_config: !@dict
  id: "database"
  host: "db.example.com"
  port: 5432

cache_config: !@dict
  id: "cache"
  host: "cache.example.com"  
  port: 6379

app_config: !@dict
  id: "application"
  db_url: "${database.host}:${database.port}"
  cache_url: "${cache.host}:${cache.port}"
  name: "MyApp"

# Reference the application config
final:
  app_name: "${application.name}"
  services:
    database: "${application.db_url}"
    cache: "${application.cache_url}"
"""
    
    config = load_config(StringIO(yaml_content))
    
    assert config["final"]["app_name"] == "MyApp"
    assert config["final"]["services"]["database"] == "db.example.com:5432"
    assert config["final"]["services"]["cache"] == "cache.example.com:6379"


def test_named_instances_vs_path_references():
    """Test that both ID and path references work for the same object."""
    yaml_content = """
services:
  database: !@dict
    id: "db_service"
    host: "localhost"
    port: 5432

# Reference by ID
by_id: "${db_service.host}"

# Reference by path  
by_path: "${services.database.host}"
"""
    
    config = load_config(StringIO(yaml_content))
    
    assert config["by_id"] == "localhost"
    assert config["by_path"] == "localhost"
    
    # Both should reference the same object
    assert config["by_id"] == config["by_path"]


def test_namespace_resolution_edge_cases():
    """Test edge cases in namespace resolution."""
    yaml_content = """
# Edge case: context key that shadows an instance ID
server: !@dict
  id: "app"  # Instance with ID "app"
  type: "instance"

app:  # Context key "app"
  type: "context"

# Should resolve from context, not instance
result: "${app.type}"
"""
    
    config = load_config(StringIO(yaml_content))
    
    # Context should take precedence
    assert config["result"] == "context"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
