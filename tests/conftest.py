# tests/conftest.py

import pytest
import os
import shutil
from pathlib import Path
from typing import Generator, Dict, Any
import uuid

@pytest.fixture(scope="session")
def examples_dir() -> Path:
    """Path to the examples directory relative to tests/."""
    return Path(__file__).parent.parent / "examples"

@pytest.fixture(scope="function")
def temp_config_dir(tmp_path: Path, examples_dir: Path) -> Generator[Path, None, None]:
    """
    Copies example YAML files to a temporary directory, adjusts include paths,
    sets the environment variable, CHANGES CWD temporarily, and yields the path
    to the temporary main config file.
    """
    files_to_copy = ["base.yml", "override.yml", "training.yml", "test_config.yaml"]
    temp_files: Dict[str, Path] = {}

    for filename in files_to_copy:
        source_path = examples_dir / filename
        if not source_path.exists():
            pytest.fail(f"Example file not found: {source_path}")
        temp_path = tmp_path / filename
        shutil.copy(source_path, temp_path)
        temp_files[filename] = temp_path

    main_config_path = temp_files["test_config.yaml"]
    content = main_config_path.read_text()
    content = content.replace("examples/base.yml", "base.yml")
    content = content.replace("examples/override.yml", "override.yml")
    content = content.replace("examples/training.yml", "training.yml")
    main_config_path.write_text(content)

    env_var_name = "TESTENV"
    original_value = os.environ.get(env_var_name)
    test_value = "value_for_pytest"
    os.environ[env_var_name] = test_value

    # --- CHANGE CWD ---
    original_cwd = Path.cwd()
    os.chdir(tmp_path) # Change CWD to the temp directory

    try:
        # --- Yield path to the main config file in the temp dir ---
        yield main_config_path
    finally:
        # --- Teardown: Restore CWD and environment variable ---
        os.chdir(original_cwd) # Change back to original CWD

        if original_value is None:
            if env_var_name in os.environ:
                 del os.environ[env_var_name]
        else:
            os.environ[env_var_name] = original_value
