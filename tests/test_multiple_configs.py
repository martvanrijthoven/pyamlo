from pathlib import Path
from pyamlo.config import load_config

CONFIGS_DIR = Path(__file__).parent / "configs"

def test_multiple_config_loading():
    config = load_config([
        CONFIGS_DIR / "base_config.yml",
        CONFIGS_DIR / "override_config.yml"
    ])

    assert config["common"]["name"] == "test-app"
    assert config["common"]["include_test"]["database"]["host"] == "localhost"
    assert config["common"]["include_test"]["database"]["port"] == 5432
    assert config["common"]["log_dir"] == "custom_logs"
    assert config["model"]["params"]["pretrained"] is False
    assert config["model"]["params"]["layers"] == 50
    assert config["training"]["epochs"] == 100

def test_multiple_config_cli_overrides():
    config = load_config(
        [CONFIGS_DIR / "base_config.yml", CONFIGS_DIR / "override_config.yml"],
        overrides=["pyamlo.common.log_dir=cli_logs", "pyamlo.model.params.layers=101"]
    )
    
    assert config["common"]["log_dir"] == "cli_logs"
    assert config["model"]["params"]["layers"] == 101
    assert config["training"]["epochs"] == 100  
    assert config["model"]["type"] == "resnet"
