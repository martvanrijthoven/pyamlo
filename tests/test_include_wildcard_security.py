import pytest
from io import StringIO
from pathlib import Path
import tempfile

from pyamlo import load_config
from pyamlo.security import SecurityPolicy


class TestIncludeWildcardSecurity:
    """Test wildcard support in include path security policies."""

    def test_wildcard_patterns_restrictive_mode(self, tmp_path):
        """Test wildcard patterns work in restrictive mode."""
        # Create test files
        (tmp_path / "configs").mkdir()
        (tmp_path / "configs" / "dev.yml").write_text("dev_config: true")
        (tmp_path / "configs" / "prod.yml").write_text("prod_config: true")
        (tmp_path / "other").mkdir()
        (tmp_path / "other" / "file.yml").write_text("other_config: true")
        
        policy = SecurityPolicy()
        policy.allowed_include_paths.add(str(tmp_path / "configs" / "*.yml"))
        
        # Should allow files matching the pattern
        yaml_content = f"""
data: !include {tmp_path / "configs" / "dev.yml"}
"""
        config = load_config(StringIO(yaml_content), security_policy=policy)
        assert config["data"]["dev_config"] is True
        
        # Should deny files not matching the pattern
        yaml_content_denied = f"""
data: !include {tmp_path / "other" / "file.yml"}
"""
        with pytest.raises(PermissionError, match="not allowed by security policy"):
            load_config(StringIO(yaml_content_denied), security_policy=policy)

    def test_wildcard_patterns_permissive_mode(self, tmp_path):
        """Test wildcard patterns work in permissive mode with restrictions."""
        # Create test files
        (tmp_path / "configs").mkdir()
        (tmp_path / "configs" / "allowed.yml").write_text("allowed_config: true")
        (tmp_path / "restricted").mkdir()
        (tmp_path / "restricted" / "secret.yml").write_text("secret_config: true")
        
        policy = SecurityPolicy(restrictive=False)
        policy.allowed_include_paths = {str(tmp_path / "configs" / "*")}  # Only allow configs/*
        
        # Should allow files matching the pattern
        yaml_content = f"""
data: !include {tmp_path / "configs" / "allowed.yml"}
"""
        config = load_config(StringIO(yaml_content), security_policy=policy)
        assert config["data"]["allowed_config"] is True
        
        # Should deny files not matching the pattern (restrictive allowlist)
        yaml_content_denied = f"""
data: !include {tmp_path / "restricted" / "secret.yml"}
"""
        with pytest.raises(PermissionError, match="not allowed by security policy"):
            load_config(StringIO(yaml_content_denied), security_policy=policy)

    def test_multiple_wildcard_patterns(self, tmp_path):
        """Test multiple wildcard patterns."""
        # Create test directory structure
        (tmp_path / "configs" / "env").mkdir(parents=True)
        (tmp_path / "templates").mkdir()
        (tmp_path / "secrets").mkdir()
        
        (tmp_path / "configs" / "app.yml").write_text("app_config: true")
        (tmp_path / "configs" / "env" / "dev.yml").write_text("dev_config: true")
        (tmp_path / "templates" / "base.yml").write_text("template_config: true")
        (tmp_path / "secrets" / "keys.yml").write_text("secret_keys: true")
        
        policy = SecurityPolicy()
        policy.allowed_include_paths.add(str(tmp_path / "configs" / "*.yml"))
        policy.allowed_include_paths.add(str(tmp_path / "configs" / "*" / "*.yml"))
        policy.allowed_include_paths.add(str(tmp_path / "templates" / "*.yml"))
        
        # Test first pattern: configs/*.yml
        yaml_content1 = f"""
data: !include {tmp_path / "configs" / "app.yml"}
"""
        config = load_config(StringIO(yaml_content1), security_policy=policy)
        assert config["data"]["app_config"] is True
        
        # Test second pattern: configs/*/*.yml
        yaml_content2 = f"""
data: !include {tmp_path / "configs" / "env" / "dev.yml"}
"""
        config = load_config(StringIO(yaml_content2), security_policy=policy)
        assert config["data"]["dev_config"] is True
        
        # Test third pattern: templates/*.yml
        yaml_content3 = f"""
data: !include {tmp_path / "templates" / "base.yml"}
"""
        config = load_config(StringIO(yaml_content3), security_policy=policy)
        assert config["data"]["template_config"] is True
        
        # Should deny files not matching any pattern
        yaml_content_denied = f"""
data: !include {tmp_path / "secrets" / "keys.yml"}
"""
        with pytest.raises(PermissionError, match="not allowed by security policy"):
            load_config(StringIO(yaml_content_denied), security_policy=policy)

    def test_question_mark_wildcard(self, tmp_path):
        """Test single character wildcard (?) pattern."""
        # Create test files
        (tmp_path / "configs").mkdir()
        (tmp_path / "configs" / "a1.yml").write_text("a1_config: true")
        (tmp_path / "configs" / "b2.yml").write_text("b2_config: true")
        (tmp_path / "configs" / "abc.yml").write_text("abc_config: true")
        
        policy = SecurityPolicy()
        policy.allowed_include_paths.add(str(tmp_path / "configs" / "??.yml"))
        
        # Should allow 2-character filenames
        yaml_content1 = f"""
data: !include {tmp_path / "configs" / "a1.yml"}
"""
        config = load_config(StringIO(yaml_content1), security_policy=policy)
        assert config["data"]["a1_config"] is True
        
        yaml_content2 = f"""
data: !include {tmp_path / "configs" / "b2.yml"}
"""
        config = load_config(StringIO(yaml_content2), security_policy=policy)
        assert config["data"]["b2_config"] is True
        
        # Should deny 3-character filename
        yaml_content_denied = f"""
data: !include {tmp_path / "configs" / "abc.yml"}
"""
        with pytest.raises(PermissionError, match="not allowed by security policy"):
            load_config(StringIO(yaml_content_denied), security_policy=policy)

    def test_bracket_character_class_wildcard(self, tmp_path):
        """Test character class [abc] wildcard pattern."""
        # Create test files
        (tmp_path / "configs").mkdir()
        (tmp_path / "configs" / "app.yml").write_text("app_config: true")
        (tmp_path / "configs" / "api.yml").write_text("api_config: true")
        (tmp_path / "configs" / "auth.yml").write_text("auth_config: true")
        (tmp_path / "configs" / "database.yml").write_text("db_config: true")
        
        policy = SecurityPolicy()
        policy.allowed_include_paths.add(str(tmp_path / "configs" / "a*.yml"))
        
        # Should allow files starting with 'a'
        yaml_content1 = f"""
data: !include {tmp_path / "configs" / "app.yml"}
"""
        config = load_config(StringIO(yaml_content1), security_policy=policy)
        assert config["data"]["app_config"] is True
        
        yaml_content2 = f"""
data: !include {tmp_path / "configs" / "api.yml"}
"""
        config = load_config(StringIO(yaml_content2), security_policy=policy)
        assert config["data"]["api_config"] is True
        
        # Should deny files not starting with 'a'
        yaml_content_denied = f"""
data: !include {tmp_path / "configs" / "database.yml"}
"""
        with pytest.raises(PermissionError, match="not allowed by security policy"):
            load_config(StringIO(yaml_content_denied), security_policy=policy)

    def test_include_from_with_wildcards(self, tmp_path):
        """Test that wildcard patterns work with !include_from as well."""
        # Create test directory and files
        (tmp_path / "configs").mkdir()
        (tmp_path / "configs" / "database.yml").write_text("""
db_config:
  host: localhost
  port: 5432
""")
        
        policy = SecurityPolicy()
        policy.allowed_include_paths.add(str(tmp_path / "configs" / "*.yml"))
        
        yaml_content = f"""
app:
  name: TestApp

db_config: !include_from {tmp_path / "configs" / "database.yml"}
"""
        config = load_config(StringIO(yaml_content), security_policy=policy)
        assert config["db_config"]["host"] == "localhost"
        assert config["db_config"]["port"] == 5432

    def test_absolute_vs_relative_path_wildcards(self, tmp_path):
        """Test wildcard patterns with absolute vs relative paths."""
        # Create test files
        (tmp_path / "configs").mkdir()
        config_file = tmp_path / "configs" / "test.yml"
        config_file.write_text("test_config: true")
        
        # Test with wildcard that includes the resolved absolute path
        policy = SecurityPolicy()
        policy.allowed_include_paths.add(str(tmp_path / "configs" / "*.yml"))
        
        # Create main config in tmp_path with absolute path include
        main_content = f"""
app:
  name: WildcardTest

data: !include {config_file}
"""
        main_file = tmp_path / "main.yml"
        main_file.write_text(main_content)
        
        # Should work when the absolute path matches the pattern
        config = load_config(str(main_file), security_policy=policy)
        assert config["data"]["test_config"] is True

    def test_no_wildcard_fallback(self, tmp_path):
        """Test that exact path matching still works when no wildcards are used."""
        # Create test file
        config_file = tmp_path / "exact.yml"
        config_file.write_text("exact_config: true")
        
        policy = SecurityPolicy()
        policy.allowed_include_paths.add(str(config_file))  # Exact path, no wildcards
        
        yaml_content = f"""
data: !include {config_file}
"""
        config = load_config(StringIO(yaml_content), security_policy=policy)
        assert config["data"]["exact_config"] is True
        
        # Other files should still be denied
        other_file = tmp_path / "other.yml"
        other_file.write_text("other_config: true")
        
        yaml_content_denied = f"""
data: !include {other_file}
"""
        with pytest.raises(PermissionError, match="not allowed by security policy"):
            load_config(StringIO(yaml_content_denied), security_policy=policy)

    def test_empty_allowed_paths_permissive(self, tmp_path):
        """Test that empty allowed_include_paths allows everything in permissive mode."""
        config_file = tmp_path / "any.yml"
        config_file.write_text("any_config: true")
        
        policy = SecurityPolicy(restrictive=False)
        # allowed_include_paths is empty, so should allow everything
        
        yaml_content = f"""
data: !include {config_file}
"""
        config = load_config(StringIO(yaml_content), security_policy=policy)
        assert config["data"]["any_config"] is True

    def test_empty_allowed_paths_restrictive(self, tmp_path):
        """Test that empty allowed_include_paths denies everything in restrictive mode."""
        config_file = tmp_path / "any.yml"
        config_file.write_text("any_config: true")
        
        policy = SecurityPolicy()  # restrictive=True by default
        # allowed_include_paths is empty, so should deny everything
        
        yaml_content = f"""
data: !include {config_file}
"""
        with pytest.raises(PermissionError, match="not allowed by security policy"):
            load_config(StringIO(yaml_content), security_policy=policy)
