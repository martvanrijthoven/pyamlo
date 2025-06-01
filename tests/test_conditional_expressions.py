"""Tests for conditional expressions in variable interpolation."""

from pathlib import Path
import pytest

from pyamlo import load_config
from pyamlo.resolve import Resolver
from pyamlo.tags import ResolutionError
from pyamlo.expressions import ExpressionError


def test_basic_comparison_operations():
    """Test basic comparison operations."""
    resolver = Resolver()
    resolver.instances["a"] = 10
    resolver.instances["b"] = 5
    resolver.instances["c"] = 10
    
    # Equal
    assert resolver.resolve("${a == c}") is True
    assert resolver.resolve("${a == b}") is False
    
    # Not equal
    assert resolver.resolve("${a != b}") is True
    assert resolver.resolve("${a != c}") is False
    
    # Greater than
    assert resolver.resolve("${a > b}") is True
    assert resolver.resolve("${b > a}") is False
    
    # Less than
    assert resolver.resolve("${b < a}") is True
    assert resolver.resolve("${a < b}") is False
    
    # Greater than or equal
    assert resolver.resolve("${a >= c}") is True
    assert resolver.resolve("${a >= b}") is True
    assert resolver.resolve("${b >= a}") is False
    
    # Less than or equal
    assert resolver.resolve("${b <= a}") is True
    assert resolver.resolve("${a <= c}") is True
    assert resolver.resolve("${a <= b}") is False


def test_string_comparisons():
    """Test comparisons with string values."""
    resolver = Resolver()
    resolver.instances["env"] = "production"
    resolver.instances["debug_env"] = "development"
    resolver.instances["name"] = "test_app"
    
    # String equality
    assert resolver.resolve("${env == 'production'}") is True
    assert resolver.resolve("${env == 'development'}") is False
    
    # String inequality
    assert resolver.resolve("${env != 'development'}") is True
    assert resolver.resolve("${env != 'production'}") is False
    
    # String comparison with variables
    assert resolver.resolve("${env == debug_env}") is False
    assert resolver.resolve("${env != debug_env}") is True


def test_logical_operations():
    """Test logical and/or/not operations."""
    resolver = Resolver()
    resolver.instances["is_prod"] = True
    resolver.instances["is_debug"] = False
    resolver.instances["workers"] = 4
    resolver.instances["max_workers"] = 8
    
    # AND operations
    assert resolver.resolve("${is_prod and workers > 2}") is True
    assert resolver.resolve("${is_debug and workers > 2}") is False
    assert resolver.resolve("${is_prod and workers > 10}") is False
    
    # OR operations
    assert resolver.resolve("${is_prod or is_debug}") is True
    assert resolver.resolve("${is_debug or workers > 2}") is True
    assert resolver.resolve("${is_debug or workers > 10}") is False
    
    # NOT operations
    assert resolver.resolve("${not is_debug}") is True
    assert resolver.resolve("${not is_prod}") is False
    assert resolver.resolve("${not (workers > 10)}") is True


def test_python_ternary_conditionals():
    """Test Python's ternary conditional expressions (value_if_true if condition else value_if_false)."""
    resolver = Resolver()
    resolver.instances["env"] = "production"
    resolver.instances["debug"] = False
    resolver.instances["workers"] = 4
    
    # Basic ternary
    assert resolver.resolve("${'INFO' if env == 'production' else 'DEBUG'}") == "INFO"
    assert resolver.resolve("${'DEBUG' if env == 'development' else 'INFO'}") == "INFO"
    
    # Numeric ternary
    assert resolver.resolve("${8 if env == 'production' else 2}") == 8
    assert resolver.resolve("${2 if env == 'development' else 8}") == 8
    
    # Ternary with variables
    assert resolver.resolve("${workers * 2 if env == 'production' else workers}") == 8
    assert resolver.resolve("${workers * 2 if env == 'development' else workers}") == 4
    
    # Boolean ternary
    assert resolver.resolve("${True if not debug else False}") is True
    assert resolver.resolve("${False if debug else True}") is True


def test_nested_conditional_expressions():
    """Test nested and complex conditional expressions."""
    resolver = Resolver()
    resolver.instances["app"] = {"env": "production", "scaling": True}
    resolver.instances["base_workers"] = 2
    
    # Nested object access in conditionals
    assert resolver.resolve("${4 if app.env == 'production' else 2}") == 4
    assert resolver.resolve("${base_workers * 4 if app.scaling else base_workers}") == 8
    
    # Complex nested conditions
    result = resolver.resolve("${base_workers * 4 if app.env == 'production' and app.scaling else base_workers}")
    assert result == 8
    
    # Nested ternary
    result = resolver.resolve("${8 if app.env == 'production' else (4 if app.env == 'staging' else 2)}")
    assert result == 8


def test_conditional_expressions_in_strings():
    """Test conditional expressions within string interpolation."""
    resolver = Resolver()
    resolver.instances["env"] = "production"
    resolver.instances["feature_enabled"] = True
    resolver.instances["version"] = "1.2.3"
    
    # String with conditional
    result = resolver.resolve("Log level: ${'INFO' if env == 'production' else 'DEBUG'}")
    assert result == "Log level: INFO"
    
    # Multiple conditionals in string
    result = resolver.resolve("App v${version} - ${'prod' if env == 'production' else 'dev'} mode")
    assert result == "App v1.2.3 - prod mode"
    
    # Feature toggle in string
    result = resolver.resolve("Features: ${'enabled' if feature_enabled else 'disabled'}")
    assert result == "Features: enabled"


def test_complex_config_with_conditionals():
    """Test a complete config using conditional expressions."""
    data = {
        "environment": "production",
        "feature_flags": {
            "new_ui": True,
            "beta_features": False
        },
        "app": {
            "workers": "${8 if environment == 'production' else 2}",
            "log_level": "${'INFO' if environment == 'production' else 'DEBUG'}",
            "cache_enabled": "${True if environment != 'development' else False}",
            "ui_version": "${'v2' if feature_flags.new_ui else 'v1'}"
        },
        "database": {
            "pool_size": "${20 if environment == 'production' else 5}",
            "ssl_required": "${True if environment == 'production' else False}",
            "timeout": "${30 if environment == 'production' else 10}"
        },
        "monitoring": {
            "enabled": "${True if environment != 'development' else False}",
            "level": "${'detailed' if environment == 'production' else 'basic'}"
        }
    }
    
    resolver = Resolver()
    result = resolver.resolve(data)
    
    # Verify all conditional expressions were resolved correctly
    assert result["app"]["workers"] == 8
    assert result["app"]["log_level"] == "INFO"
    assert result["app"]["cache_enabled"] is True
    assert result["app"]["ui_version"] == "v2"
    assert result["database"]["pool_size"] == 20
    assert result["database"]["ssl_required"] is True
    assert result["database"]["timeout"] == 30
    assert result["monitoring"]["enabled"] is True
    assert result["monitoring"]["level"] == "detailed"


def test_conditional_expression_errors():
    """Test error handling for invalid conditional expressions."""
    resolver = Resolver()
    resolver.instances["env"] = "production"
    resolver.instances["number"] = 42
    
    # Invalid syntax
    with pytest.raises(ExpressionError, match="Invalid expression"):
        resolver.resolve("${env == 'production' ? 'yes' : 'no'}")  # Wrong syntax for Python
    
    # Unknown variable in condition
    with pytest.raises(ResolutionError, match="Unknown variable"):
        resolver.resolve("${unknown_var == 'test'}")
    
    # Invalid comparison
    with pytest.raises(ExpressionError, match="Invalid expression"):
        resolver.resolve("${env === 'production'}")  # Triple equals not valid in Python


def test_mixed_math_and_conditional_expressions():
    """Test expressions that combine math and conditional logic."""
    resolver = Resolver()
    resolver.instances["env"] = "production"
    resolver.instances["base_workers"] = 2
    resolver.instances["scaling_factor"] = 3
    
    # Math within conditional
    assert resolver.resolve("${base_workers * scaling_factor if env == 'production' else base_workers}") == 6
    
    # Conditional math result
    assert resolver.resolve("${(base_workers * 4) if env == 'production' else (base_workers + 1)}") == 8
    
    # Complex expression
    result = resolver.resolve("${base_workers * scaling_factor + 2 if env == 'production' and base_workers > 1 else 1}")
    assert result == 8


def test_boolean_conditionals():
    """Test conditionals with boolean values."""
    resolver = Resolver()
    resolver.instances["is_enabled"] = True
    resolver.instances["is_debug"] = False
    resolver.instances["count"] = 0
    resolver.instances["name"] = ""
    
    # Direct boolean evaluation
    assert resolver.resolve("${is_enabled}") is True
    assert resolver.resolve("${is_debug}") is False
    
    # Boolean in conditionals
    assert resolver.resolve("${'on' if is_enabled else 'off'}") == "on"
    assert resolver.resolve("${'on' if is_debug else 'off'}") == "off"
    
    # Truthiness of different types
    assert resolver.resolve("${'has_value' if count else 'empty'}") == "empty"  # 0 is falsy
    assert resolver.resolve("${'has_value' if name else 'empty'}") == "empty"  # empty string is falsy


def test_yaml_file_with_conditionals():
    config_path = Path(__file__).parent / "configs" / "conditionals.yml"
    config = load_config(str(config_path))

    # Verify all conditional expressions were resolved correctly
    assert config["app"]["workers"] == 8
    assert config["app"]["log_level"] == "INFO"
    assert config["app"]["debug_enabled"] is False  # debug_mode is False and env is production
    
    assert config["database"]["host"] == "prod-db.example.com"
    assert config["database"]["port"] == 5432
    assert config["database"]["ssl"] is True
    assert config["database"]["pool_size"] == 20
    
    assert config["cache"]["enabled"] is True
    assert config["cache"]["ttl"] == 3600
    assert config["cache"]["provider"] == "redis"
    
    assert config["monitoring"]["enabled"] is True  # analytics=True and env!=development
    assert config["monitoring"]["dashboard"] == "new"  # new_dashboard=True
    assert config["monitoring"]["api_monitoring"] is False  # beta_api=False
    
    assert config["services"]["external_api"]["enabled"] is True  # not debug_mode
    assert config["services"]["external_api"]["timeout"] == 30
    assert config["services"]["external_api"]["retries"] == 3


def test_environment_based_conditionals():
    """Test common pattern of environment-based configuration."""
    resolver = Resolver()
    resolver.instances["ENV"] = "staging"
    
    # Multi-environment conditionals
    log_level = resolver.resolve("${'ERROR' if ENV == 'production' else ('WARN' if ENV == 'staging' else 'DEBUG')}")
    assert log_level == "WARN"
    
    # Database selection
    db_name = resolver.resolve("${'prod_db' if ENV == 'production' else ('stage_db' if ENV == 'staging' else 'dev_db')}")
    assert db_name == "stage_db"
    
    # Resource allocation
    memory = resolver.resolve("${4096 if ENV == 'production' else (2048 if ENV == 'staging' else 512)}")
    assert memory == 2048
