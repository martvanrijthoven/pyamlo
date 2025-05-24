import pytest
from yamlo import load_config
from pathlib import Path
from yaml import ScalarNode, MappingNode
from yamlo.tags import (
    construct_env, ConfigLoader, TagError, ResolutionError
)

# def test_env_vars(tmp_path):
#     src = Path(__file__).parent / "configs" / "env.yaml"
#     config_path = tmp_path / "env.yaml"
#     config_path.write_text(src.read_text())
#     with open(config_path, "r") as f:
#         config = load_config(f)
#     assert config["db_user"] == "yamlo_user"
#     assert config["db_pass"] == "yamlo_pass"
#     assert config["my_var"] == "yamlo_env"

def test_construct_env_missing():
    node = ScalarNode(tag='!env', value='SURELY_NOT_SET')
    with pytest.raises(ResolutionError):
        construct_env(ConfigLoader(''), node)

def test_construct_env_wrong_type():
    class DummyNode:
        start_mark = 'dummy'
    with pytest.raises(TagError):
        construct_env(ConfigLoader(''), DummyNode())

def test_construct_env_mapping_missing_and_no_default():
    # Correct MappingNode construction: value is a list of (key, value) pairs
    node = MappingNode(
        tag='!env',
        value=[
            (ScalarNode(tag='tag:yaml.org,2002:str', value='var'), 
             ScalarNode(tag='tag:yaml.org,2002:str', value='SURELY_NOT_SET'))
        ]
    )
    with pytest.raises(ResolutionError):
        construct_env(ConfigLoader(''), node)

def test_env_tag_errors():
    loader = ConfigLoader("")
    
    # Test environment variable not set
    scalar_node = ScalarNode("!env", "NONEXISTENT_VAR")
    with pytest.raises(ResolutionError, match="Environment variable .* not set"):
        construct_env(loader, scalar_node)
    
    # Test mapping without default
    mapping_node = MappingNode("!env", [
        (ScalarNode("tag:yaml.org,2002:str", "var"), 
         ScalarNode("tag:yaml.org,2002:str", "NONEXISTENT_VAR"))
    ])
    with pytest.raises(ResolutionError, match="Environment variable .* not set and no default provided"):
        construct_env(loader, mapping_node)
