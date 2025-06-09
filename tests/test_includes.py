import pytest
from pathlib import Path
from yaml import MappingNode, ScalarNode
from yaml.constructor import ConstructorError

from pyamlo import load_config
from pyamlo.include import IncludeError, load_raw, _load_include
from pyamlo.tags import ConfigLoader, construct_include


def test_include_and_merging():
    """Test that includes work correctly with merging."""
    config_path = Path(__file__).parent / "configs" / "main.yaml"
    config = load_config(config_path)
    
    assert config["app"]["name"] == "BaseApp"
    assert config["app"]["version"] == "2.0"
    assert config["list"] == [1, 2, 3, 4, 5]
    assert config["dict"] == {"b": 3, "c": 4}


def test_load_raw_file_not_found():
    with pytest.raises(IncludeError):
        load_raw("nonexistent_file.yaml")


def test_load_include_invalid():
    with pytest.raises(IncludeError):
        _load_include(123)


def test_load_file_yaml_error(tmp_path):
    badfile = tmp_path / "bad.yaml"
    badfile.write_text(": this is not valid yaml: [")
    with pytest.raises(IncludeError):
        load_raw(str(badfile))


def test_include_construction():
    loader = ConfigLoader("")
    node = ScalarNode("!include", "test.yml")
    result = construct_include(loader, node)
    assert result.path == "test.yml"


def test_include_error():
    node = MappingNode("!include", [])
    with pytest.raises(
        ConstructorError, match="expected a scalar node, but found mapping"
    ):
        construct_include(ConfigLoader(""), node)


def test_construct_include_error():
    loader = ConfigLoader("")
    node = MappingNode("!include", [])
    with pytest.raises(
        ConstructorError, match="expected a scalar node, but found mapping"
    ):
        construct_include(loader, node)
