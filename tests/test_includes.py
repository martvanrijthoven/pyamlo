import os
from pathlib import Path

import pytest
from yaml import MappingNode, ScalarNode
from yaml.constructor import ConstructorError

from yamlo import load_config
from yamlo.merge import IncludeError, _load_include, _load_pkg_include, load_raw
from yamlo.tags import ConfigLoader, construct_include


def test_includes_and_merging(tmp_path):
    config_path = tmp_path / "main.yaml"
    config_path.write_text(
        """
            _includes:
            - base.yaml
            - override.yaml
        """
    )
    for name in ("base.yaml", "override.yaml"):
        src = Path(__file__).parent / "configs" / name
        (tmp_path / name).write_text(src.read_text())
    os.chdir(tmp_path)
    with open(config_path, "r") as f:
        config = load_config(f)
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


def test_load_raw_yaml_error(tmp_path):
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


def test_pkg_include_import_error(tmp_path):
    test_file = tmp_path / "config.yml"
    test_file.write_text("key: value")
    result = _load_pkg_include(str(test_file), "nonexistent_package")
    assert isinstance(result, dict)


def test_pkg_include_config_notfound(monkeypatch, tmp_path):
    class MockPackage:
        __file__ = str(tmp_path / "pkg" / "__init__.py")

    def mock_import(name):
        return MockPackage()

    monkeypatch.setattr("importlib.import_module", mock_import)
    monkeypatch.setattr("os.path.dirname", lambda x: str(tmp_path / "pkg"))

    with pytest.raises(IncludeError):
        _load_pkg_include("nonexistent.yml", "test_package")


def test_pkg_include_complex(monkeypatch, tmp_path):
    pkg_dir = tmp_path / "pkg"
    config_dir = pkg_dir / "configuration"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "config.yml"
    config_file.write_text("key: value")

    init_file = pkg_dir / "__init__.py"
    init_file.touch()

    class MockPackage:
        __file__ = str(init_file)

    monkeypatch.setattr("importlib.import_module", lambda x: MockPackage())

    result = _load_pkg_include("config.yml", "test_package")
    assert result == {"test_package": {"key": "value"}}
