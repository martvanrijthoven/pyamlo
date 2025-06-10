import pytest
from io import StringIO
from pathlib import Path

from pyamlo import load_config
from pyamlo.security import SecurityPolicy


class TestObjectCreationSecurity:
    """Test security policies for !@ and !$@ object creation tags."""

    def test_callspec_tag_denied_by_default(self):
        """Test that !@ tag is denied by default restrictive security policy."""
        policy = SecurityPolicy()  # Default restrictive mode
        yaml_content = """
path: !@pathlib.Path /tmp/test
counter: !@collections.Counter 
 - [1, 2, 3]
"""
        with pytest.raises(PermissionError, match="Import of module .* is not allowed by security policy"):
            load_config(StringIO(yaml_content), security_policy=policy)

    def test_callspec_tag_allowed_when_permitted(self):
        """Test that !@ tag works when imports are explicitly allowed."""
        policy = SecurityPolicy()
        policy.allowed_imports.add("pathlib.Path")
        policy.allowed_imports.add("collections.Counter")
        
        yaml_content = """
path: !@pathlib.Path /tmp/test
counter: !@collections.Counter 
 - [1, 2, 3]
"""
        config = load_config(StringIO(yaml_content), security_policy=policy)
        
        assert isinstance(config["path"], Path)
        assert str(config["path"]) == "/tmp/test"
        from collections import Counter
        assert config["counter"] == Counter([1, 2, 3])

    def test_callspec_tag_partial_allow(self):
        """Test that only explicitly allowed imports work with !@ tag."""
        policy = SecurityPolicy()
        policy.allowed_imports.add("pathlib.Path")
        # Note: collections.Counter is NOT added
        
        yaml_content = """
path: !@pathlib.Path /tmp/test
counter: !@collections.Counter 
 - [1, 2, 3]
"""
        with pytest.raises(PermissionError, match="Import of module 'collections.Counter' is not allowed"):
            load_config(StringIO(yaml_content), security_policy=policy)

    def test_interpolated_callspec_tag_denied_by_default(self):
        """Test that !$@ tag is denied by default restrictive security policy."""
        policy = SecurityPolicy()  # Default restrictive mode
        yaml_content = """
layer_type: Linear
model: !$torch.nn.@layer_type
  in_features: 10
  out_features: 5
"""
        with pytest.raises(PermissionError, match="Import of module .* is not allowed by security policy"):
            load_config(StringIO(yaml_content), security_policy=policy)

    def test_interpolated_callspec_tag_allowed_when_permitted(self):
        """Test that !$@ tag works when imports are explicitly allowed."""
        policy = SecurityPolicy()
        policy.allowed_imports.add("collections.Counter")
        
        yaml_content = """
collection_type: Counter
my_counter: !$collections.@collection_type 
 - [1, 1, 2, 3]
"""
        config = load_config(StringIO(yaml_content), security_policy=policy)
        
        from collections import Counter
        assert config["my_counter"] == Counter([1, 1, 2, 3])

    def test_interpolated_callspec_dynamic_path_security(self):
        """Test that !$@ tag checks the resolved dynamic path."""
        policy = SecurityPolicy()
        policy.allowed_imports.add("pathlib.Path")
        # Note: os.path is NOT allowed
        
        yaml_content = """
path_module: os.path
bad_path: !$@path_module.join /tmp test
good_path: !$pathlib.@path_type /tmp/test
path_type: Path
"""
        # This should fail because os.path.join is not allowed
        with pytest.raises(PermissionError, match="Import of module 'os.path.join' is not allowed"):
            load_config(StringIO(yaml_content), security_policy=policy)

    def test_object_creation_with_complex_args(self):
        """Test object creation with complex arguments under security policy."""
        policy = SecurityPolicy()
        policy.allowed_imports.add("datetime.datetime")
        
        yaml_content = """
my_datetime: !@datetime.datetime
  - 2023
  - 12
  - 25
  - 10
  - 30
  - 0
"""
        config = load_config(StringIO(yaml_content), security_policy=policy)
        
        from datetime import datetime
        assert isinstance(config["my_datetime"], datetime)
        assert config["my_datetime"].year == 2023
        assert config["my_datetime"].month == 12
        assert config["my_datetime"].day == 25

    def test_object_creation_kwargs_security(self):
        """Test object creation with keyword arguments under security policy."""
        policy = SecurityPolicy()
        policy.allowed_imports.add("complex")
        
        yaml_content = """
complex_num: !@complex
  real: 3
  imag: 4
"""
        config = load_config(StringIO(yaml_content), security_policy=policy)
        assert config["complex_num"] == complex(3, 4)

    def test_nested_object_creation_security(self):
        """Test nested object creation with security policies."""
        policy = SecurityPolicy()
        policy.allowed_imports.add("pathlib.Path")
        policy.allowed_imports.add("collections.Counter")
        
        yaml_content = """
data:
  path: !@pathlib.Path /tmp/nested
  stats: !@collections.Counter 
   - [1, 2, 2, 3]
"""
        config = load_config(StringIO(yaml_content), security_policy=policy)
        
        assert isinstance(config["data"]["path"], Path)
        assert str(config["data"]["path"]) == "/tmp/nested"
        from collections import Counter
        assert config["data"]["stats"] == Counter([1, 2, 2, 3])

    def test_permissive_mode_allows_object_creation(self):
        """Test that permissive mode allows object creation by default."""
        policy = SecurityPolicy(restrictive=False)
        
        yaml_content = """
path: !@pathlib.Path /tmp/test
counter: !@collections.Counter 
 - [1, 2, 3]
"""
        config = load_config(StringIO(yaml_content), security_policy=policy)
        
        assert isinstance(config["path"], Path)
        assert str(config["path"]) == "/tmp/test"
        from collections import Counter
        assert config["counter"] == Counter([1, 2, 3])

    def test_permissive_mode_with_restrictions(self):
        """Test that permissive mode can still have specific restrictions."""
        policy = SecurityPolicy(restrictive=False)
        policy.allowed_imports = {"pathlib.Path"}  # Only allow Path
        
        yaml_content = """
path: !@pathlib.Path /tmp/test
counter: !@collections.Counter 
 - [1, 2, 3]
"""
        # Should fail because Counter is restricted in permissive mode with specific allowlist
        with pytest.raises(PermissionError, match="Import of module 'collections.Counter' is not allowed"):
            load_config(StringIO(yaml_content), security_policy=policy)

    def test_interpolated_callspec_with_variable_resolution(self):
        """Test !$@ tag with complex variable resolution under security."""
        policy = SecurityPolicy()
        policy.allowed_imports.add("collections.Counter")
        policy.allowed_imports.add("collections.defaultdict")
        policy.allow_expressions = True  # Allow expressions for variable resolution
        
        yaml_content = """
base_module: collections
container_type: Counter
use_default: false
my_container: !$@base_module.@container_type 
 - [1, 2, 2, 3]
"""
        config = load_config(StringIO(yaml_content), security_policy=policy)
        
        from collections import Counter
        assert config["my_container"] == Counter([1, 2, 2, 3])

    def test_dangerous_imports_blocked(self):
        """Test that dangerous imports are blocked even when trying different approaches."""
        policy = SecurityPolicy()
        
        dangerous_yaml_content = """
# Try to import potentially dangerous modules
os_module: !@os.system "echo hello"
subprocess_call: !$subprocess.@method "ls"
method: call
"""
        with pytest.raises(PermissionError):
            load_config(StringIO(dangerous_yaml_content), security_policy=policy)

    def test_malformed_interpolated_path(self):
        """Test error handling for malformed interpolated paths."""
        policy = SecurityPolicy()
        policy.allowed_imports.add("collections.Counter")
        
        yaml_content = """
# Missing variable that would be interpolated
bad_counter: !$collections.@missing_var 
 - [1, 2, 3]
"""
        # This should fail during resolution, not security check
        with pytest.raises(Exception):  # Could be ResolutionError or similar
            load_config(StringIO(yaml_content), security_policy=policy)

    def test_security_policy_inheritance_object_creation(self):
        """Test that security policies are properly inherited in object creation contexts."""
        policy = SecurityPolicy()
        policy.allowed_imports.add("pathlib.Path")
        
        yaml_content = """
paths:
  - !@pathlib.Path /tmp/test1
  - !@pathlib.Path /tmp/test2
  - !@collections.Counter 
    - [1, 2]
"""
        with pytest.raises(PermissionError, match="Import of module 'collections.Counter' is not allowed"):
            load_config(StringIO(yaml_content), security_policy=policy)


class TestObjectCreationEdgeCases:
    """Test edge cases and error conditions for object creation security."""
    
    def test_empty_import_path(self):
        """Test behavior with empty import paths."""
        policy = SecurityPolicy()
        
        yaml_content = """
empty_import: !@ ""
"""
        with pytest.raises(Exception):  # Should fail during import resolution
            load_config(StringIO(yaml_content), security_policy=policy)

    def test_nonexistent_module_import(self):
        """Test behavior when trying to import nonexistent modules."""
        policy = SecurityPolicy()
        policy.allowed_imports.add("nonexistent.module.Class")
        
        yaml_content = """
bad_import: !@nonexistent.module.Class
"""
        with pytest.raises(Exception):  # Should fail during import resolution
            load_config(StringIO(yaml_content), security_policy=policy)

    def test_builtin_types_security(self):
        """Test security for builtin types."""
        policy = SecurityPolicy()
        policy.allowed_imports.add("builtins.list")
        policy.allowed_imports.add("builtins.dict")
        
        yaml_content = """
my_list: !@builtins.list 
 - [1, 2, 3]
my_dict: !@builtins.dict
  key: value
"""
        config = load_config(StringIO(yaml_content), security_policy=policy)
        
        assert config["my_list"] == [1, 2, 3]
        assert config["my_dict"] == {"key": "value"}
