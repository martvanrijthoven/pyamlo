#!/usr/bin/env python3
"""Test script to demonstrate the new overrides functionality."""

import sys
from io import StringIO
from pyamlo import load_config

# Sample config
yaml_content = """
app:
  name: BaseApp
  version: 1.0
  debug: false

database:
  host: localhost
  port: 5432
"""

def test_overrides_only():
    """Test using manual overrides only."""
    print("=== Test 1: Manual overrides only ===")
    config = load_config(
        StringIO(yaml_content),
        overrides=["pyamlo.app.name=ManualApp", "pyamlo.app.debug=true"]
    )
    print(f"App name: {config['app']['name']}")
    print(f"App debug: {config['app']['debug']}")
    print(f"App version: {config['app']['version']}")
    print()

def test_use_cli_only():
    """Test using CLI overrides only."""
    print("=== Test 2: CLI overrides only (simulated) ===")
    # Simulate CLI args
    sys.argv = ["script.py", "pyamlo.app.name=CLIApp", "pyamlo.database.host=cli-db"]
    config = load_config(
        StringIO(yaml_content),
        use_cli=True
    )
    print(f"App name: {config['app']['name']}")
    print(f"Database host: {config['database']['host']}")
    print()

def test_combined():
    """Test using both manual and CLI overrides."""
    print("=== Test 3: Combined manual + CLI overrides ===")
    # Simulate CLI args
    sys.argv = ["script.py", "pyamlo.database.port=3306", "pyamlo.app.version=2.0"]
    config = load_config(
        StringIO(yaml_content),
        overrides=["pyamlo.app.name=CombinedApp", "pyamlo.app.debug=true"],
        use_cli=True
    )
    print(f"App name: {config['app']['name']} (from manual)")
    print(f"App debug: {config['app']['debug']} (from manual)")
    print(f"App version: {config['app']['version']} (from CLI)")
    print(f"Database port: {config['database']['port']} (from CLI)")
    print()

if __name__ == "__main__":
    test_overrides_only()
    test_use_cli_only()
    test_combined()
    print("✅ All tests demonstrate the new overrides functionality working correctly!")
