import pytest
from io import StringIO
from pathlib import Path

from pyamlo import load_config
from pyamlo.security import SecurityPolicy


class TestImportWildcardSecurity:
    """Test wildcard support in import security policies."""

    def test_import_wildcard_patterns_restrictive_mode(self):
        """Test wildcard patterns work in restrictive mode for imports."""
        policy = SecurityPolicy()
        policy.allowed_imports.add("collections.*")
        policy.allowed_imports.add("pathlib.Path")
        
        # Should allow modules matching the pattern
        yaml_content = """
path: !@pathlib.Path
  - /tmp/test
counter: !@collections.Counter 
  - [1, 2, 3]
defaultdict_factory: !@collections.defaultdict
"""
        config = load_config(StringIO(yaml_content), security_policy=policy)
        assert isinstance(config["path"], Path)
        from collections import Counter, defaultdict
        assert config["counter"] == Counter([1, 2, 3])
        assert isinstance(config["defaultdict_factory"], defaultdict)
        
        # Should deny modules not matching any pattern
        yaml_content_denied = """
dt: !@datetime.datetime
  - 2023
  - 1 
  - 1
"""
        with pytest.raises(PermissionError, match="not allowed by security policy"):
            load_config(StringIO(yaml_content_denied), security_policy=policy)

    def test_import_wildcard_patterns_permissive_mode(self):
        """Test wildcard patterns work in permissive mode for imports."""
        policy = SecurityPolicy(restrictive=False)
        # In permissive mode, allowed_imports acts as a blocklist
        policy.allowed_imports = {"pathlib.*"}  # Block pathlib.* modules
        
        # Should allow modules not in the blocked list
        yaml_content_allowed = """
counter: !@collections.Counter
  - [1, 2, 3]
"""
        config = load_config(StringIO(yaml_content_allowed), security_policy=policy)
        from collections import Counter
        assert config["counter"] == Counter([1, 2, 3])
        
        # Should deny modules matching the blocked pattern 
        yaml_content_denied = """
path: !@pathlib.Path
  - /tmp/test
"""
        with pytest.raises(PermissionError, match="not allowed by security policy"):
            load_config(StringIO(yaml_content_denied), security_policy=policy)

    def test_multiple_import_wildcard_patterns(self):
        """Test multiple wildcard patterns for imports."""
        policy = SecurityPolicy()
        policy.allowed_imports.add("collections.*")
        policy.allowed_imports.add("pathlib.*")
        policy.allowed_imports.add("datetime.datetime")
        policy.allowed_imports.add("torch.nn.*")
        
        # Test collections.* pattern
        yaml_content1 = """
counter: !@collections.Counter 
  - [1, 2, 3]
deque: !@collections.deque
  - [1, 2, 3]
"""
        config = load_config(StringIO(yaml_content1), security_policy=policy)
        from collections import Counter, deque
        assert config["counter"] == Counter([1, 2, 3])
        assert list(config["deque"]) == [1, 2, 3]
        
        # Test pathlib.* pattern
        yaml_content2 = """
path: !@pathlib.Path
  - /tmp/test
pure_path: !@pathlib.PurePath
  - /tmp/pure
"""
        config = load_config(StringIO(yaml_content2), security_policy=policy)
        assert isinstance(config["path"], Path)
        from pathlib import PurePath
        assert isinstance(config["pure_path"], PurePath)
        
        # Test exact match (datetime.datetime)
        yaml_content3 = """
dt: !@datetime.datetime
  - 2023
  - 12
  - 25
"""
        config = load_config(StringIO(yaml_content3), security_policy=policy)
        from datetime import datetime
        assert isinstance(config["dt"], datetime)
        assert config["dt"].year == 2023
        
        # Should deny modules not matching any pattern
        yaml_content_denied = """
random_num: !@random.randint
  - 1
  - 10
"""
        with pytest.raises(PermissionError, match="not allowed by security policy"):
            load_config(StringIO(yaml_content_denied), security_policy=policy)

    def test_single_character_wildcard_imports(self):
        """Test single character wildcard (?) pattern for imports."""
        policy = SecurityPolicy()
        policy.allowed_imports.add("o?.path")  # Should match os.path
        
        # Should allow os.path
        # Note: os.path methods are tricky to test directly, let's use a different example
        policy = SecurityPolicy()
        policy.allowed_imports.add("???.*")  # 3-character module names
        
        yaml_content = """
path: !@sys.path  # sys has 3 characters
"""
        # sys.path is not callable, let's test with a better example
        policy.allowed_imports.clear()
        policy.allowed_imports.add("??.*")  # 2-character module prefixes
        
        yaml_content = """
path: !@os.getcwd
"""
        # os.getcwd would match os.* but let's be more specific
        # Actually, let's test with an exact pattern that we know works
        policy.allowed_imports.clear()
        policy.allowed_imports.add("collections.?*")  # collections.C*, collections.d*, etc.
        
        yaml_content = """
counter: !@collections.Counter 
 - [1, 2, 3]
"""
        config = load_config(StringIO(yaml_content), security_policy=policy)
        from collections import Counter
        assert config["counter"] == Counter([1, 2, 3])

    def test_nested_module_wildcards(self):
        """Test wildcard patterns with nested modules."""
        policy = SecurityPolicy()
        policy.allowed_imports.add("torch.nn.*")
        policy.allowed_imports.add("tensorflow.keras.layers.*")
        
        # These are hypothetical - we don't actually have torch/tensorflow in test env
        # So let's test with real modules that have nested structure
        policy.allowed_imports.clear()
        policy.allowed_imports.add("xml.etree.*")
        
        yaml_content = """
# xml.etree.ElementTree would match xml.etree.*
# But since it's not typically called directly, let's use a different example
tree: !@xml.etree.ElementTree.Element
  - "root"
"""
        # ElementTree.Element is callable
        config = load_config(StringIO(yaml_content), security_policy=policy)
        import xml.etree.ElementTree as ET
        assert isinstance(config["tree"], ET.Element)

    def test_interpolated_imports_with_wildcards(self):
        """Test that wildcard patterns work with interpolated imports (!$@)."""
        policy = SecurityPolicy()
        policy.allowed_imports.add("collections.*")
        policy.allow_expressions = True  # Allow variable resolution
        
        yaml_content = """
module_path: collections.Counter
my_counter: !$@module_path
  - [1, 1, 2, 3]
"""
        config = load_config(StringIO(yaml_content), security_policy=policy)
        from collections import Counter
        assert config["my_counter"] == Counter([1, 1, 2, 3])

    def test_exact_import_vs_wildcard(self):
        """Test that exact imports still work alongside wildcards."""
        policy = SecurityPolicy()
        policy.allowed_imports.add("pathlib.Path")  # Exact match
        policy.allowed_imports.add("collections.*")  # Wildcard
        
        yaml_content = """
path: !@pathlib.Path
  - /tmp/test
counter: !@collections.Counter 
  - [1, 2, 3]
deque: !@collections.deque
  - [4, 5, 6]
"""
        config = load_config(StringIO(yaml_content), security_policy=policy)
        
        assert isinstance(config["path"], Path)
        from collections import Counter, deque
        assert config["counter"] == Counter([1, 2, 3])
        assert list(config["deque"]) == [4, 5, 6]
        
        # Should deny pathlib.PurePath (not exact match for pathlib.Path)
        yaml_content_denied = """
pure_path: !@pathlib.PurePath
  - /tmp/pure
"""
        with pytest.raises(PermissionError, match="not allowed by security policy"):
            load_config(StringIO(yaml_content_denied), security_policy=policy)

    def test_no_wildcard_fallback_imports(self):
        """Test that exact import matching still works when no wildcards are used."""
        policy = SecurityPolicy()
        policy.allowed_imports.add("pathlib.Path")
        policy.allowed_imports.add("collections.Counter")
        
        yaml_content = """
path: !@pathlib.Path
  - /tmp/test
counter: !@collections.Counter 
  - [1, 2, 3]
"""
        config = load_config(StringIO(yaml_content), security_policy=policy)
        
        assert isinstance(config["path"], Path)
        from collections import Counter
        assert config["counter"] == Counter([1, 2, 3])
        
        # Should deny other collections modules
        yaml_content_denied = """
deque: !@collections.deque
  - [1, 2, 3]
"""
        with pytest.raises(PermissionError, match="not allowed by security policy"):
            load_config(StringIO(yaml_content_denied), security_policy=policy)

    def test_empty_allowed_imports_restrictive(self):
        """Test that empty allowed_imports denies everything in restrictive mode."""
        policy = SecurityPolicy(restrictive=True) 
        
        yaml_content = """
path: !@pathlib.Path
  - /tmp/test
"""
        with pytest.raises(PermissionError, match="not allowed by security policy"):
            load_config(StringIO(yaml_content), security_policy=policy)

    def test_empty_allowed_imports_permissive(self):
        """Test that empty allowed_imports allows everything in permissive mode."""
        policy = SecurityPolicy(restrictive=False)
        # allowed_imports is empty, so should allow everything
        
        yaml_content = """
path: !@pathlib.Path
  - /tmp/test
"""
        config = load_config(StringIO(yaml_content), security_policy=policy)
        assert isinstance(config["path"], Path)

    def test_complex_wildcard_patterns(self):
        """Test more complex wildcard patterns for imports."""
        policy = SecurityPolicy(restrictive=True)
        policy.allowed_imports.add("*.*")  # Allow any module.submodule
        
        yaml_content = """
path: !@pathlib.Path
  - /tmp/test
counter: !@collections.Counter 
  - [1, 2, 3]
"""
        config = load_config(StringIO(yaml_content), security_policy=policy)
        
        assert isinstance(config["path"], Path)
        from collections import Counter
        assert config["counter"] == Counter([1, 2, 3])
        
        # But should deny top-level modules if we change the pattern
        policy.allowed_imports.clear()
        policy.allowed_imports.add("*.*.*")  # Require at least 3 parts
        
        yaml_content_denied = """
path: !@pathlib.Path
  - /tmp/test  # Only 2 parts: pathlib.Path
"""
        with pytest.raises(PermissionError, match="not allowed by security policy"):
            load_config(StringIO(yaml_content_denied), security_policy=policy)

    def test_character_class_wildcards_imports(self):
        """Test character class patterns like [abc] for imports."""
        policy = SecurityPolicy(restrictive=True)
        policy.allowed_imports.add("[cp]*.*")  # Allow modules starting with 'c' or 'p'
        
        yaml_content = """
path: !@pathlib.Path
  - /tmp/test  # starts with 'p'
counter: !@collections.Counter   # starts with 'c'
  - [1, 2, 3]
"""
        config = load_config(StringIO(yaml_content), security_policy=policy)
        
        assert isinstance(config["path"], Path)
        from collections import Counter
        assert config["counter"] == Counter([1, 2, 3])
        
        # Should deny modules not starting with 'c' or 'p'
        yaml_content_denied = """
dt: !@datetime.datetime
  - 2023
  - 1
  - 1  # starts with 'd'
"""
        with pytest.raises(PermissionError, match="not allowed by security policy"):
            load_config(StringIO(yaml_content_denied), security_policy=policy)
