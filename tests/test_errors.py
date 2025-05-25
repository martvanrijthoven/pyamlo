from pathlib import Path
import os
import pytest
from yaml import ScalarNode

from pyamlo import load_config
from pyamlo.merge import MergeError, deep_merge
from pyamlo.resolve import ResolutionError, Resolver, _apply_call
from pyamlo.tags import (
    ConfigLoader,
    ExtendSpec,
    PatchSpec,
    TagError,
    construct_callspec,
    construct_extend,
    construct_patch,
)


def test_invalid_env_tag(tmp_path):
    src = Path(__file__).parent / "configs" / "invalid.yaml"
    config_path = tmp_path / "invalid.yaml"
    config_path.write_text(src.read_text())
    with open(config_path, "r") as f:
        with pytest.raises(Exception):
            load_config(f)


def test_merge_patch_errors():
    with pytest.raises(MergeError, match="Cannot patch non-dict at"):
        deep_merge({"a": [1, 2]}, {"a": PatchSpec({"x": 1})})

    with pytest.raises(MergeError, match="Cannot extend non-list at"):
        deep_merge({"a": {"b": 1}}, {"a": ExtendSpec([1, 2])})


def test_construct_extend_wrong_type():
    node = ScalarNode(tag="!extend", value="not-a-sequence")
    with pytest.raises(TagError):
        construct_extend(ConfigLoader(""), node)


def test_construct_patch_wrong_type():
    node = ScalarNode(tag="!patch", value="not-a-mapping")
    with pytest.raises(TagError):
        construct_patch(ConfigLoader(""), node)


def test_construct_callspec_unsupported():
    class DummyNode:
        start_mark = "dummy"

    with pytest.raises(TagError):
        construct_callspec(ConfigLoader(""), "foo", DummyNode())


def test_resolver_get_unknown():
    r = Resolver()
    with pytest.raises(ResolutionError):
        r._get("notfound")


def test_resolver_get_attr_error():
    r = Resolver()
    r.ctx["foo"] = object()
    with pytest.raises(ResolutionError):
        r._get("foo.bar")


def test_resolve_missing_attribute():
    resolver = Resolver()
    resolver.ctx["obj"] = object()
    with pytest.raises(ResolutionError):
        resolver._get("obj.missing")


def test_apply_call_signature_error():
    class NoSignature:
        def __call__(self, *args, **kwargs):
            return args

    f = NoSignature()
    assert _apply_call(f, [1, 2], {}) == (1, 2)


def test_apply_call_valueerror():
    class F:
        def __call__(self, *args, **kwargs):
            raise ValueError

    f = F()
    with pytest.raises(ValueError):
        _apply_call(f, [1, 2], {})


def test_apply_call_positional_list():
    def f(x):
        return x

    assert _apply_call(f, [1, 2], {}) == [[1, 2]]
