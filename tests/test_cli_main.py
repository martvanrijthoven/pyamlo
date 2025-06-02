"""Tests for the main CLI module."""
import json
import sys
import subprocess
import tempfile
from pathlib import Path


def test_cli_with_overrides():
    """Test that CLI overrides work correctly when mixed with config files."""
    test_dir = Path(__file__).parent
    config_file = test_dir / "configs" / "base_config.yml"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
        tmp_path = tmp_file.name
    
    try:
        # Test CLI override
        result = subprocess.run([
            sys.executable, "-m", "pyamlo", 
            str(config_file), 
            "pyamlo.test=123",
            f"--cfg-output={tmp_path}"
        ], capture_output=True, text=True, cwd=test_dir.parent)
        
        assert result.returncode == 0
        assert result.stderr == ""
        
        # Verify the override worked
        with open(tmp_path, 'r') as f:
            config = json.load(f)
        
        assert config["test"] == 123
        assert config["common"]["name"] == "test-app"  # Original value preserved
        
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    

def test_cli_multiple_configs_with_overrides():
    """Test multiple config files with CLI overrides."""
    test_dir = Path(__file__).parent
    base_config = test_dir / "configs" / "base_config.yml"
    override_config = test_dir / "configs" / "override_config.yml"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
        tmp_path = tmp_file.name
    
    try:
        # Test multiple configs with CLI override
        result = subprocess.run([
            sys.executable, "-m", "pyamlo",
            str(base_config),
            str(override_config), 
            "pyamlo.model.params.layers=100",
            f"--cfg-output={tmp_path}"
        ], capture_output=True, text=True, cwd=test_dir.parent)
        
        assert result.returncode == 0
        assert result.stderr == ""
        
        # Verify the configurations merged and override worked
        with open(tmp_path, 'r') as f:
            config = json.load(f)
        
        assert config["model"]["params"]["layers"] == 100  # CLI override
        assert config["model"]["params"]["pretrained"] == False  # From override_config.yml
        assert config["model"]["params"]["batch_size"] == 32  # From override_config.yml
        assert config["training"]["epochs"] == 100  # From override_config.yml
        assert config["common"]["name"] == "test-app"  # From base_config.yml
        
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_cli_nested_overrides():
    """Test nested CLI overrides."""
    test_dir = Path(__file__).parent
    config_file = test_dir / "configs" / "base_config.yml"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
        tmp_path = tmp_file.name
    
    try:
        # Test nested override
        result = subprocess.run([
            sys.executable, "-m", "pyamlo",
            str(config_file),
            "pyamlo.new.section.value=42",
            f"--cfg-output={tmp_path}"
        ], capture_output=True, text=True, cwd=test_dir.parent)
        
        assert result.returncode == 0
        assert result.stderr == ""
        
        # Verify the nested override worked
        with open(tmp_path, 'r') as f:
            config = json.load(f)
        
        assert config["new"]["section"]["value"] == 42
        assert config["common"]["name"] == "test-app"  # Original value preserved
        
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_cli_string_overrides():
    """Test string CLI overrides with quotes."""
    test_dir = Path(__file__).parent
    config_file = test_dir / "configs" / "base_config.yml"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
        tmp_path = tmp_file.name
    
    try:
        # Test string override
        result = subprocess.run([
            sys.executable, "-m", "pyamlo",
            str(config_file),
            'pyamlo.common.name="cli-override"',
            f"--cfg-output={tmp_path}"
        ], capture_output=True, text=True, cwd=test_dir.parent)
        
        assert result.returncode == 0
        assert result.stderr == ""
        
        # Verify the string override worked
        with open(tmp_path, 'r') as f:
            config = json.load(f)
        
        assert config["common"]["name"] == "cli-override"
        assert config["model"]["type"] == "resnet"  # Original value preserved
        
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_cli_no_config_files():
    """Test that CLI fails gracefully when no config files are provided."""
    test_dir = Path(__file__).parent
    
    # Test with only overrides, no config files
    result = subprocess.run([
        sys.executable, "-m", "pyamlo",
        "pyamlo.test=123"
    ], capture_output=True, text=True, cwd=test_dir.parent)
    
    assert result.returncode == 1
    assert "At least one config file must be provided" in result.stderr
