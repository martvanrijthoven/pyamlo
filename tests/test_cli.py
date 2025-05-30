"""Tests for CLI override functionality."""
import sys
from io import StringIO

import pytest

from pyamlo import load_config
from pyamlo.cli import OverrideError, parse_cli_overrides, process_cli
from pyamlo.tags import ExtendSpec, PatchSpec


def test_parse_cli_overrides_basic():
    result = parse_cli_overrides(["pyamlo.app.name=TestApp", "pyamlo.debug=true"])
    assert result["app"]["name"] == "TestApp"
    assert result["debug"] is True
    
    result = parse_cli_overrides(["other.setting=value", "pyamlo.debug=true"])
    assert "other" not in result
    assert result["debug"] is True


def test_parse_cli_overrides_with_special_tags():
    result = parse_cli_overrides(["pyamlo.items=!extend [4,5]"])
    assert isinstance(result["items"], ExtendSpec)
    assert result["items"].items == [4, 5]

    result = parse_cli_overrides(["pyamlo.config=!patch {debug: true}"])
    assert isinstance(result["config"], PatchSpec)
    assert result["config"].mapping == {"debug": True}


def test_load_config_with_overrides():
    yaml_content = """
app:
  name: BaseApp
items: [1, 2, 3]
settings:
  debug: false
  options:
    a: 1
    """
    
    config = load_config(
        StringIO(yaml_content), 
        overrides=["pyamlo.app.name=TestApp"]
    )
    assert config["app"]["name"] == "TestApp"
    
    config = load_config(
        StringIO(yaml_content), 
        overrides=["pyamlo.items=!extend [4,5]"]
    )
    assert config["items"] == [1, 2, 3, 4, 5]
    
    config = load_config(
        StringIO(yaml_content), 
        overrides=['pyamlo.settings=!patch {"debug": true, "options": {"b": 2}}']
    )
    assert config["settings"]["debug"] is True
    assert config["settings"]["options"] == {"b": 2}


def test_invalid_override_format():
    with pytest.raises(OverrideError):
        parse_cli_overrides(["invalid"])

    with pytest.raises(OverrideError):
        parse_cli_overrides(["key:value"])


def test_process_cli_empty():
    config = {"app": {"name": "TestApp"}}
    result = process_cli(config, None)
    assert result == config
    result = process_cli(config, [])
    assert result == config


def test_integration_with_includes():
    """Test CLI overrides working with included files."""
    yaml_content = """
include!:
  - tests/configs/base.yaml
debug: false
    """
    config = load_config(
        StringIO(yaml_content),
        overrides=["pyamlo.debug=true", "pyamlo.app.name=OverrideApp"]
    )
    assert config["debug"] is True
    assert config["app"]["name"] == "OverrideApp"


def test_cli_with_sys_argv(monkeypatch):
    """Test processing of sys.argv arguments."""
    yaml_content = """
app:
  name: BaseApp
  debug: false
    """

    test_args = [
        "script.py",
        "--verbose",
        "pyamlo.app.name=TestApp",
        "pyamlo.app.debug=true",
        "--output=test.log"
    ]
    monkeypatch.setattr(sys, "argv", test_args)
    pyamlo_args = [arg for arg in sys.argv[1:] if arg.startswith("pyamlo.")]
    config = load_config(StringIO(yaml_content), overrides=pyamlo_args)
    assert config["app"]["name"] == "TestApp"
    assert config["app"]["debug"] is True


def test_cli_complex_values_with_sys_argv(monkeypatch):
    """Test processing of complex sys.argv arguments with special tags."""
    yaml_content = """
items: [1, 2, 3]
settings:
  debug: false
  options: {}
    """

    test_args = [
        "script.py",
        "pyamlo.items=!extend [4,5]",
        'pyamlo.settings=!patch {"debug": true, "options": {"timeout": 30}}'
    ]
    monkeypatch.setattr(sys, "argv", test_args)
    
    pyamlo_args = [arg for arg in sys.argv[1:] if arg.startswith("pyamlo.")]
    config = load_config(StringIO(yaml_content), overrides=pyamlo_args)
    assert config["items"] == [1, 2, 3, 4, 5]
    assert config["settings"]["debug"] is True
    assert config["settings"]["options"] == {"timeout": 30}


def test_cli_with_quotes_in_sys_argv(monkeypatch):
    """Test handling of quoted values in sys.argv."""
    yaml_content = """
message: Hello
settings:
  path: /default/path
    """
    
    test_args = [
        "script.py",
        'pyamlo.message=Hello World!',  # Space in value
        'pyamlo.settings.path=/path/with spaces/test'  # Path with spaces
    ]
    monkeypatch.setattr(sys, "argv", test_args)
    
    pyamlo_args = [arg for arg in sys.argv[1:] if arg.startswith("pyamlo.")]
    config = load_config(StringIO(yaml_content), overrides=pyamlo_args)
    assert config["message"] == "Hello World!"
    assert config["settings"]["path"] == "/path/with spaces/test"


def test_use_cli_parameter(monkeypatch):
    """Test the use_cli=True parameter reads from sys.argv."""
    yaml_content = """
app:
  name: BaseApp
  debug: false
    """
    
    test_args = [
        "script.py",
        "pyamlo.app.name=TestApp",
        "pyamlo.app.debug=true",
        "pyamlo.new_setting=hello"
    ]
    monkeypatch.setattr(sys, "argv", test_args)
    config = load_config(StringIO(yaml_content), use_cli=True)
    
    assert config["app"]["name"] == "TestApp"
    assert config["app"]["debug"] is True
    assert config["new_setting"] == "hello"


def test_use_cli_with_explicit_overrides(monkeypatch):
    """Test that manual overrides and CLI overrides work together, with manual taking precedence when they conflict."""
    yaml_content = """
app:
  name: BaseApp
  version: 1.0
    """
    
    test_args = ["script.py", "pyamlo.app.version=2.0", "pyamlo.app.debug=true"]
    monkeypatch.setattr(sys, "argv", test_args)
    
    config = load_config(
        StringIO(yaml_content), 
        overrides=["pyamlo.app.name=FromExplicit"],
        use_cli=True
    )
    
    # Manual override takes precedence for name, CLI provides version and debug
    assert config["app"]["name"] == "FromExplicit"  # from manual overrides (first)
    assert config["app"]["version"] == 2.0  # from CLI (parsed as float)
    assert config["app"]["debug"] is True  # from CLI


def test_use_cli_false_ignores_argv(monkeypatch):
    """Test that use_cli=False ignores sys.argv."""
    yaml_content = """
app:
  name: BaseApp
    """
    
    test_args = ["script.py", "pyamlo.app.name=ShouldBeIgnored"]
    monkeypatch.setattr(sys, "argv", test_args)
    config = load_config(StringIO(yaml_content), use_cli=False)
    
    assert config["app"]["name"] == "BaseApp"


def test_use_cli_script_example():
    """Test a realistic script usage example."""
    yaml_content = """
database:
  host: localhost
  port: 5432
  
app:
  name: MyApp
  debug: false
    """
    
    config = load_config(
        StringIO(yaml_content),
        overrides=["pyamlo.app.debug=true", "pyamlo.database.host=production-db"]
    )
    
    assert config["app"]["debug"] is True
    assert config["database"]["host"] == "production-db"
    assert config["database"]["port"] == 5432  # unchanged


def test_use_cli_with_complex_overrides(monkeypatch):
    """Test use_cli with complex YAML tag overrides."""
    yaml_content = """
items: [1, 2, 3]
settings:
  debug: false
    """
    
    test_args = [
        "script.py",
        "pyamlo.items=!extend [4,5]",
        'pyamlo.settings=!patch {"debug": true, "timeout": 30}'
    ]
    monkeypatch.setattr(sys, "argv", test_args)
    
    config = load_config(StringIO(yaml_content), use_cli=True)
    
    assert config["items"] == [1, 2, 3, 4, 5]
    assert config["settings"]["debug"] is True
    assert config["settings"]["timeout"] == 30
