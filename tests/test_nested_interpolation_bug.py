"""Test for nested interpolation resolution bug."""

import pytest
from pyamlo import load_config


def test_nested_interpolation_bug():
    """Test that nested interpolation works - this currently fails."""
    component1 = {
        "stage": {
            "step": {
                "component1": {
                    "example": "test_value",
                    "version": 1.0,
                }
            }
        }
    }

    component2 = {
        "stage": {
            "step": {
                "component2": {
                    "example": "${stage.step.component1.example}",
                    "version": 2.0,
                }
            }
        }
    }

    # This should work but currently fails
    result = load_config([component1, component2])
    
    assert result["stage"]["step"]["component1"]["example"] == "test_value"
    assert result["stage"]["step"]["component2"]["example"] == "test_value"


def test_shallow_interpolation_works():
    """Test that shallow interpolation works - this should pass."""
    component1 = {
        "stage": {
            "component1": {
                "example": "test_value",
                "version": 1.0,
            }
        }
    }

    component2 = {
        "stage": {
            "component2": {
                "example": "${stage.component1.example}",
                "version": 2.0,
            }
        }
    }

    result = load_config([component1, component2])
    
    assert result["stage"]["component1"]["example"] == "test_value"
    assert result["stage"]["component2"]["example"] == "test_value"


def test_deep_nested_interpolation():
    """Test even deeper nesting."""
    config1 = {
        "level1": {
            "level2": {
                "level3": {
                    "component1": {
                        "value": "deep_value"
                    }
                }
            }
        }
    }

    config2 = {
        "level1": {
            "level2": {
                "level3": {
                    "component2": {
                        "value": "${level1.level2.level3.component1.value}"
                    }
                }
            }
        }
    }

    result = load_config([config1, config2])
    
    assert result["level1"]["level2"]["level3"]["component1"]["value"] == "deep_value"
    assert result["level1"]["level2"]["level3"]["component2"]["value"] == "deep_value"


def test_object_property_access():
    """Test accessing properties of instantiated objects."""
    config1 = {
        "stage": {
            "step": {
                "component1": {
                    "path": "!@pathlib.Path /tmp/test/example.txt",
                    "version": 1.0,
                }
            }
        }
    }

    config2 = {
        "stage": {
            "step": {
                "component2": {
                    "filename": "${stage.step.component1.path.name}",
                    "parent": "${stage.step.component1.path.parent}",
                    "suffix": "${stage.step.component1.path.suffix}",
                }
            }
        }
    }

    result = load_config([config1, config2])
    
    # Check that the object was created correctly
    path_obj = result["stage"]["step"]["component1"]["path"]
    assert str(path_obj) == "/tmp/test/example.txt"
    
    # Check that property access works
    assert result["stage"]["step"]["component2"]["filename"] == "example.txt"
    assert str(result["stage"]["step"]["component2"]["parent"]) == "/tmp/test"
    assert result["stage"]["step"]["component2"]["suffix"] == ".txt"