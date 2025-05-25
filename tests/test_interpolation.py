from pathlib import Path

import pytest

from pyamlo import load_config
from pyamlo.resolve import Resolver
from pyamlo.tags import IncludeSpec, ResolutionError


def test_interpolation(tmp_path):
    src = Path(__file__).parent / "configs" / "interpolation.yaml"
    config_path = tmp_path / "interpolation.yaml"
    config_path.write_text(src.read_text())
    with open(config_path, "r") as f:
        config = load_config(f)
    assert config["result"] == "102"
    assert config["nested"]["value"] == "102"


def test_resolve_string_interpolation():
    resolver = Resolver()
    resolver.instances["var1"] = "hello"
    resolver.instances["var2"] = "world"

    assert resolver.resolve("${var1}") == "hello"
    assert resolver.resolve("say ${var1} ${var2}!") == "say hello world!"


def test_resolve_mapping_interpolation():
    resolver = Resolver()
    resolver.instances["var1"] = "world"
    resolver.instances["map1"] = {"nested": "hello"}

    # Test dictionary access in interpolation
    assert resolver.resolve("${map1.nested} ${var1}") == "hello world"


def test_resolve_dict_nested():
    resolver = Resolver()
    resolver.instances["var"] = "test"

    data = {"a": {"b": "${var}", "c": {"d": "before ${var} after"}}}

    result = resolver.resolve(data)
    assert result["a"]["b"] == "test"
    assert result["a"]["c"]["d"] == "before test after"
    assert resolver.ctx["a.b"] == "test"
    assert resolver.ctx["a.c.d"] == "before test after"


def test_resolve_include_with_interpolation(tmp_path):
    resolver = Resolver()
    resolver.instances["base_dir"] = str(tmp_path)

    test_file = tmp_path / "test.yml"
    test_file.write_text("key: value")

    spec = IncludeSpec("${base_dir}/test.yml")
    result = resolver.resolve(spec)
    assert result == {"key": "value"}


def test_resolve_include_interpolation_error():
    resolver = Resolver()
    spec = IncludeSpec("${nonexistent}/test.yml")
    with pytest.raises(ResolutionError):
        resolver.resolve(spec)


def test_resolve_empty_var():
    resolver = Resolver()
    resolver.instances["var"] = ""
    assert resolver.resolve("prefix${var}suffix") == "prefixsuffix"
