import pathlib
from collections import Counter
from pathlib import Path

from yaml import ScalarNode

from pyamlo import load_config
from pyamlo.merge import deep_merge
from pyamlo.tags import CallSpec, ConfigLoader, PatchSpec, construct_callspec


def test_object_instantiation():
    config_path = Path(__file__).parent / "configs" / "objects.yaml"
    config = load_config(config_path)
    assert isinstance(config["path"], pathlib.Path)
    assert str(config["path"]) == "/tmp/test"
    assert config["counter"] == Counter([1, 1, 1, 4, 5])
    assert config["complex"] == complex(2, 3)


def test_object_instantiation_with_file_object():
    config_path = Path(__file__).parent / "configs" / "objects.yaml"
    with open(config_path, "r") as f:
        config = load_config(f)
    assert isinstance(config["path"], pathlib.Path)
    assert str(config["path"]) == "/tmp/test"
    assert config["counter"] == Counter([1, 1, 1, 4, 5])
    assert config["complex"] == complex(2, 3)


def test_deep_merge_call_spec_patch():
    base = {"key": CallSpec("test", [], {"a": 1})}
    patch = {"key": PatchSpec({"b": 2})}
    result = deep_merge(base, patch)
    assert result["key"].kwargs == {"b": 2}


def test_deep_merge_call_spec_dict():
    base = {"key": CallSpec("test", [], {"a": 1})}
    patch = {"key": {"b": 2}}
    result = deep_merge(base, patch)
    assert result["key"].kwargs == {"a": 1, "b": 2}


def test_callspec_empty_scalar():
    loader = ConfigLoader("")
    node = ScalarNode("!@test", "")
    spec = construct_callspec(loader, "test", node)
    assert spec.args == []


def test_callspec_none_scalar():
    loader = ConfigLoader("")
    node = ScalarNode("!@test", None)
    spec = construct_callspec(loader, "test", node)
    assert spec.args == []


def test_import_tag():
    yaml_content = """
path_class: !import pathlib.Path
counter_class: !import collections.Counter
"""
    from io import StringIO
    config = load_config(StringIO(yaml_content))

    assert config["path_class"] is pathlib.Path
    assert config["counter_class"] is Counter
    assert callable(config["path_class"])
    assert callable(config["counter_class"])
