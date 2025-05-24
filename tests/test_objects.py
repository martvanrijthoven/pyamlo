import pathlib
from collections import Counter
from pathlib import Path

from yaml import ScalarNode

from yamlo import load_config
from yamlo.config import SystemInfo
from yamlo.merge import deep_merge
from yamlo.resolve import call
from yamlo.tags import CallSpec, ConfigLoader, PatchSpec, construct_callspec


def test_object_instantiation():
    config_path = Path(__file__).parent / "configs" / "objects.yaml"
    with open(config_path, "r") as f:
        config = load_config(f)
    assert isinstance(config["path"], pathlib.Path)
    assert str(config["path"]) == "/tmp/test"
    assert hasattr(config["sysinfo"], "as_dict")
    assert isinstance(config["call"], dict)
    assert config["counter"] == Counter([1, 1, 1, 4, 5])
    assert config["complex"] == complex(2, 3)


def test_systeminfo_as_dict():
    info = SystemInfo()
    data = info.as_dict()
    assert isinstance(data, dict)
    assert "host" in data
    assert "user" in data
    assert "started" in data


def test_deep_merge_call_spec_patch():
    base = {"key": CallSpec("test", [], {"a": 1}, None)}
    patch = {"key": PatchSpec({"b": 2})}
    result = deep_merge(base, patch)
    assert result["key"].kwargs == {"b": 2}


def test_deep_merge_call_spec_dict():
    base = {"key": CallSpec("test", [], {"a": 1}, None)}
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


def test_config_call():
    def example_fn(a=None):
        return a

    assert call(lambda: 42) == 42
    assert call(example_fn, a=10) == 10
