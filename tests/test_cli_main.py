"""Tests for the main CLI module."""
import sys
import subprocess
from pathlib import Path


def test_cli_with_overrides():
    """Test that CLI overrides work correctly when mixed with config files."""
    test_dir = Path(__file__).parent
    config_file = test_dir / "configs" / "base_config.yml"
    
    # Test CLI override
    result = subprocess.run([
        sys.executable, "-m", "pyamlo", 
        str(config_file), 
        "pyamlo.test=123"
    ], capture_output=True, text=True, cwd=test_dir.parent)
    
    assert result.returncode == 0
    assert "test': 123" in result.stdout
    

def test_cli_multiple_configs_with_overrides():
    """Test multiple config files with CLI overrides."""
    test_dir = Path(__file__).parent
    base_config = test_dir / "configs" / "base_config.yml"
    override_config = test_dir / "configs" / "override_config.yml"
    
    # Test multiple configs with CLI override
    result = subprocess.run([
        sys.executable, "-m", "pyamlo",
        str(base_config),
        str(override_config), 
        "pyamlo.model.params.layers=100"
    ], capture_output=True, text=True, cwd=test_dir.parent)
    
    assert result.returncode == 0
    assert "'layers': 100" in result.stdout
    # Should have values from override config
    assert "'batch_size': 32" in result.stdout


def test_cli_nested_overrides():
    """Test nested CLI overrides."""
    test_dir = Path(__file__).parent
    config_file = test_dir / "configs" / "base_config.yml"
    
    # Test nested override
    result = subprocess.run([
        sys.executable, "-m", "pyamlo",
        str(config_file),
        "pyamlo.new.section.value=42"
    ], capture_output=True, text=True, cwd=test_dir.parent)
    
    assert result.returncode == 0
    assert "'new': {'section': {'value': 42}}" in result.stdout


def test_cli_string_overrides():
    """Test string CLI overrides with quotes."""
    test_dir = Path(__file__).parent
    config_file = test_dir / "configs" / "base_config.yml"
    
    # Test string override
    result = subprocess.run([
        sys.executable, "-m", "pyamlo",
        str(config_file),
        'pyamlo.common.name="cli-override"'
    ], capture_output=True, text=True, cwd=test_dir.parent)
    
    assert result.returncode == 0
    assert "'name': 'cli-override'" in result.stdout


def test_cli_no_config_files():
    """Test that CLI fails gracefully when no config files are provided."""
    test_dir = Path(__file__).parent
    
    # Test with only overrides, no config files
    result = subprocess.run([
        sys.executable, "-m", "pyamlo",
        "pyamlo.test=123"
    ], capture_output=True, text=True, cwd=test_dir.parent)
    
    assert result.returncode == 1
    assert "At least one config file must be specified" in result.stderr
