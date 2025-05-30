"""Tests for CLI override functionality."""
import sys
from io import StringIO

import pytest

from pyamlo import load_config
from pyamlo.cli import OverrideError, parse_cli_overrides, process_cli
from pyamlo.tags import ExtendSpec, PatchSpec


def test_parse_cli_overrides_basic():
    # Test pyamlo. prefixed arguments
    result = parse_cli_overrides(["pyamlo.app.name=TestApp", "pyamlo.debug=true"])
    assert result["app"]["name"] == "TestApp"
    assert result["debug"] is True
    
    # Test that non-pyamlo arguments are ignored
    result = parse_cli_overrides(["other.setting=value", "pyamlo.debug=true"])
    assert "other" not in result
    assert result["debug"] is True


def test_parse_cli_overrides_with_special_tags():
    # Test !extend tag
    result = parse_cli_overrides(["pyamlo.items=!extend [4,5]"])
    assert isinstance(result["items"], ExtendSpec)
    assert result["items"].items == [4, 5]

    # Test !patch tag
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
    
    # Test basic override
    config = load_config(
        StringIO(yaml_content), 
        cli_overrides=["pyamlo.app.name=TestApp"]
    )
    assert config["app"]["name"] == "TestApp"
    
    # Test extending a list
    config = load_config(
        StringIO(yaml_content), 
        cli_overrides=["pyamlo.items=!extend [4,5]"]
    )
    assert config["items"] == [1, 2, 3, 4, 5]
    
    # Test patching a dict
    config = load_config(
        StringIO(yaml_content), 
        cli_overrides=['pyamlo.settings=!patch {"debug": true, "options": {"b": 2}}']
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
        cli_overrides=["pyamlo.debug=true", "pyamlo.app.name=OverrideApp"]
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
    
    # Mock sys.argv
    test_args = [
        "script.py",
        "--verbose",
        "pyamlo.app.name=TestApp",
        "pyamlo.app.debug=true",
        "--output=test.log"
    ]
    monkeypatch.setattr(sys, "argv", test_args)
    
    # Filter out non-pyamlo arguments before passing to load_config
    pyamlo_args = [arg for arg in sys.argv[1:] if arg.startswith("pyamlo.")]
    config = load_config(StringIO(yaml_content), cli_overrides=pyamlo_args)
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
    
    # Mock sys.argv with complex arguments
    test_args = [
        "script.py",
        "pyamlo.items=!extend [4,5]",
        'pyamlo.settings=!patch {"debug": true, "options": {"timeout": 30}}'
    ]
    monkeypatch.setattr(sys, "argv", test_args)
    
    # Filter out non-pyamlo arguments before passing to load_config
    pyamlo_args = [arg for arg in sys.argv[1:] if arg.startswith("pyamlo.")]
    config = load_config(StringIO(yaml_content), cli_overrides=pyamlo_args)
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
    
    # Mock sys.argv with quoted values
    test_args = [
        "script.py",
        'pyamlo.message=Hello World!',  # Space in value
        'pyamlo.settings.path=/path/with spaces/test'  # Path with spaces
    ]
    monkeypatch.setattr(sys, "argv", test_args)
    
    # Filter out non-pyamlo arguments before passing to load_config
    pyamlo_args = [arg for arg in sys.argv[1:] if arg.startswith("pyamlo.")]
    config = load_config(StringIO(yaml_content), cli_overrides=pyamlo_args)
    assert config["message"] == "Hello World!"
    assert config["settings"]["path"] == "/path/with spaces/test"
