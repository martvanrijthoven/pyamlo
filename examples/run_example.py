import pprint
import os
from pathlib import Path
import io # Import io for StringIO

# Assuming this script is run from the package root directory
# If yamlo is installed, you can just 'import yamlo'
# If running directly from source, adjust Python path or use editable install
try:
    from yamlo import load_config, ConfigError
except ImportError:
    # Simple fallback for running directly from root (requires src/ in PYTHONPATH)
    import sys
    # Calculate path to src directory relative to this script
    root_dir = Path(__file__).parent.parent
    src_dir = root_dir / "src"
    sys.path.insert(0, str(src_dir))
    from yamlo import load_config, ConfigError


# --- Configuration for the example ---
CONFIG_FILE = Path(__file__).parent / "test_config.yaml"
# Set the environment variable needed by the config
ENV_VAR_NAME = "MY_TEST_VAR"
ENV_VAR_VALUE = "value_from_env"
os.environ[ENV_VAR_NAME] = ENV_VAR_VALUE

print(f"Attempting to load config: {CONFIG_FILE}")
print(f"Environment variable set: {ENV_VAR_NAME}={os.environ.get(ENV_VAR_NAME)}")
print("-" * 20)


try:
    # load_config expects a file-like object (stream)
    with open(CONFIG_FILE, 'r') as f:
        cfg, instances = load_config(f)

    print("--- Raw Config Loaded ---")
    pprint.pprint(cfg)
    print("-" * 20)

    print("--- Resolved Instances ---")
    pprint.pprint(instances)
    print("-" * 20)

    # --- Example Accessing Config Values ---
    print("--- Accessing Values ---")
    print(f"App Name: {cfg.get('app', {}).get('name')}")
    print(f"Test Env Var: {cfg.get('testenv')}")

    # Accessing nested values requires checking existence
    ssettings = cfg.get('ssettings', {})
    print(f"Settings Thresholds: {ssettings.get('thresholds')}")
    print(f"Settings Options: {ssettings.get('options')}")
    print(f"Settings Extra (Numpy): {ssettings.get('extra')}") # Should be a numpy array

    paths = cfg.get('paths', {})
    print(f"Base Path: {paths.get('base')}") # Should be a Path object
    print(f"Data Path: {paths.get('data')}") # Should be a Path object

    services = cfg.get('services', {})
    main_service = services.get('main') # Should be a Repository object (or None)
    secondary_service = services.get('secondary') # Should be a Repository object (or None)
    print(f"Main Service: {main_service}")
    print(f"Secondary Service: {secondary_service}")

    if main_service:
      print(f"Main Service Host: {main_service.host}") # Access attribute

    pipeline = cfg.get('pipeline', {}).get('composite', {})
    print(f"Pipeline First (interpolated): {pipeline.get('first')}")
    print(f"Pipeline Second (instance): {pipeline.get('second')}") # Should be the secondary Repository instance

    logs = cfg.get('logs', [])
    print(f"Log Paths: {logs}") # Should be a list of Path objects

    # Accessing instance by ID
    main_instance = instances.get('main')
    print(f"Instance 'main': {main_instance}")
    print(f"Is cfg['services']['main'] the same object as instances['main']? {cfg.get('services', {}).get('main') is main_instance}")
    print(f"Is cfg['pipeline']['composite']['second'] the same object as instances['secondary']? {cfg.get('pipeline', {}).get('composite', {}).get('second') is instances.get('secondary')}")


except ConfigError as e:
    print(f"\nERROR loading configuration: {e}")
except FileNotFoundError:
    print(f"\nERROR: Config file not found at {CONFIG_FILE}")
    print("Ensure you are running this script from the 'yamlo-package' root directory.")
except Exception as e:
     print(f"\nAn unexpected error occurred: {e}")

finally:
    # Clean up environment variable if needed
    # del os.environ[ENV_VAR_NAME]
    pass