from pprint import pprint
import pytest
from pathlib import Path
import uuid
import sys

# Conditional imports - skip tests if not found
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import torchvision
    HAS_TORCHVISION = True
except ImportError:
    HAS_TORCHVISION = False

try:
    import instatorch # Assuming this is the name of the library
    # You might need a more specific import if the call is deeper
    # e.g., from instatorch.data import get_dataloaders
    HAS_INSTATORCH = True
except ImportError:
    HAS_INSTATORCH = False

# --- Import the function to test ---
# Assumes tests are run such that src/ is in PYTHONPATH (e.g., via hatch/tox/pytest config)
try:
    from yamlo import load_config, ConfigError
except ImportError as e:
    pytest.fail(f"Failed to import yamlo.load_config - ensure src/ is in PYTHONPATH: {e}")

# Import the expected Repository class type from the fixture
from yamlo import Repository


# Mark functions requiring optional dependencies
requires_numpy = pytest.mark.skipif(not HAS_NUMPY, reason="Requires numpy to be installed")
requires_torchvision = pytest.mark.skipif(not HAS_TORCHVISION, reason="Requires torchvision to be installed")
requires_instatorch = pytest.mark.skipif(not HAS_INSTATORCH, reason="Requires instatorch to be installed")


def test_load_test_config_output(temp_config_dir: Path):
    """
    Loads the main test_config.yaml (with includes resolved) and verifies
    the structure and values of the resulting config dictionary (cfg)
    and the instances dictionary.
    """
    config_file_path = temp_config_dir # Fixture yields the path to temp test_config.yaml

    with open(config_file_path, 'r') as f:
        cfg, instances = load_config(f)

    pprint(cfg)
    # --- Expected Values ---
    # These should reflect the final state after all includes, merges, patches,
    # object instantiations, and interpolations.

    # --- Assertions for `cfg` dictionary ---

    # 1. Top-level keys from test_config.yaml itself
    assert "testenv" in cfg
    assert cfg["testenv"] == "value_for_pytest" # Value set by fixture

    # assert "instatorch" in cfg
    # assert cfg["instatorch"] == {"extra": 2} # Result of !patch

    assert "inclusion_test" in cfg
    assert cfg["inclusion_test"] == {"test2": 2}

    assert "app" in cfg
    assert cfg["app"] == {"name": "TestApp", "version": "2.0"}

    # 2. Settings merged from base.yml and override.yml
    assert "ssettings" in cfg
    ssettings = cfg["ssettings"]
    assert "thresholds" in ssettings
    assert ssettings["thresholds"] == [1, 2, 3, 4, 5] # base + !extend from override

    assert "options" in ssettings
    # base: {a: alpha, b: beta}, override !patch: {b: bravo, c: charlie} -> final
    assert ssettings["options"] == {"b": "bravo", "c": "charlie"}

    if HAS_NUMPY:
        assert "extra" in ssettings
        assert isinstance(ssettings["extra"], np.ndarray)
        np.testing.assert_array_equal(ssettings["extra"], np.array([4, 2, 4]))
    else:
        # If numpy isn't present, the !@numpy.array likely raised an error during load_config
        # or was skipped. If load_config didn't raise, check if 'extra' is missing or None.
        # This depends on yamlo's error handling for failed !@ calls.
        # Assuming load_config would fail if numpy isn't installed and !@numpy is used:
        # We might not reach here if numpy isn't installed, unless load_config has fallback.
        # If execution reaches here without numpy, assert 'extra' is not present or handle as appropriate.
         assert "extra" not in ssettings # Or assert specific error state if applicable

    # 3. Paths with object instantiation and interpolation
    assert "paths" in cfg
    paths = cfg["paths"]
    assert "base" in paths
    assert isinstance(paths["base"], Path)
    assert str(paths["base"]) == "/opt/TestApp" # Interpolated ${app.name}

    assert "data" in paths
    assert isinstance(paths["data"], Path)
    assert str(paths["data"]) == "/opt/TestApp/data" # Interpolated ${paths.base}

    # 4. Services with object instantiation, interpolation, and instance ID tracking
    assert "services" in cfg
    services = cfg["services"]
    assert "main" in services
    assert isinstance(services["main"], Repository) # Check type
    assert services["main"].host == "main.TestApp.svc" # Interpolated ${app.name}
    assert services["main"].port == 9000

    assert "secondary" in services
    assert isinstance(services["secondary"], Repository) # Check type
    assert services["secondary"].host == "secondary.TestApp.svc" # Interpolated ${app.name}
    assert services["secondary"].port == 9000 # Interpolated ${services.main.port}

    # 5. Pipeline with interpolation using instance attributes and direct instance reference
    assert "pipeline" in cfg
    pipeline = cfg["pipeline"]["composite"]
    assert pipeline["first"] == "main.TestApp.svc" # Interpolated ${services.main.host}
    assert pipeline["second"] is services["secondary"] # Direct object reference

    # 6. Logs with object instantiation and interpolation
    assert "logs" in cfg
    logs = cfg["logs"]
    assert len(logs) == 2
    # assert isinstance(logs[0], Path)
    assert str(logs[0]) == "/logs/TestApp/main.log" # Interpolated ${app.name}
    # assert isinstance(logs[1], Path)
    assert str(logs[1]) == "/logs/TestApp/main.TestApp.svc.log" # Interpolated ${app.name}, ${services.main.host}

    # 7. Training section from training.yml
    pprint(cfg)
    assert "training" in cfg
    training = cfg["training"]
    assert training["epochs"] == 10.0 # !@float
    assert isinstance(training["epochs"], float)
    assert training["check"] is True
    assert training["learning_rate"] == 0.001
    assert isinstance(training["id"], uuid.UUID) # !@uuid.uuid4
    assert training["a"] is True

    # 8. Training data section (potentially requires mocking/skipping)
    if HAS_TORCHVISION and HAS_INSTATORCH:
        assert "data" in training
        tdata = training["data"]
        # Assertions depend heavily on whether libs were mocked or actually called
        # If mocked (as in conftest example):
        # assert isinstance(tdata["train_data"], MagicMock) # Or whatever mock object is used
        # assert isinstance(tdata["test_data"], MagicMock)
        # If *not* mocked, these would be actual MNIST objects, potentially triggering downloads etc.
        # Add appropriate assertions based on your mocking strategy or skip if real objects expected.
        # For now, just check presence if libs are available
        assert "train_data" in tdata
        assert "test_data" in tdata

        assert "data_loaders" in training
        # If mocked:
        # assert isinstance(training["data_loaders"], MagicMock)
        # If not mocked, check type returned by instatorch.data.get_dataloaders
        assert "data_loaders" in training # Check presence

        assert "train_data_loader_dataset" in training
        # If mocked (matching conftest example):
        # assert training["train_data_loader_dataset"] == "MockTrainDataset"
        # If not mocked, assert actual interpolated value based on real dataloader object
        assert "train_data_loader_dataset" in training # Check presence

    # --- Assertions for `instances` dictionary ---
    assert isinstance(instances, dict)
    assert "main" in instances # id from services.main
    assert instances["main"] is cfg["services"]["main"] # Verify same object

    assert "secondary" in instances # id from services.secondary
    assert instances["secondary"] is cfg["services"]["secondary"] # Verify same object

    # Check if any other !@ calls had an 'id'
    # training.id used !@uuid.uuid4 which doesn't take an 'id' field in the mapping itself
    # Add assertions for other IDs if present in your config
    assert len(instances) == 2 # Only 'main' and 'secondary' had explicit IDs


# --- Optional: Add tests for specific sections if needed ---

@requires_numpy
def test_ssettings_numpy_output(temp_config_dir: Path):
    """Verify numpy array creation specifically."""
    with open(temp_config_dir, 'r') as f:
        cfg, _ = load_config(f)
    assert "ssettings" in cfg and "extra" in cfg["ssettings"]
    assert isinstance(cfg["ssettings"]["extra"], np.ndarray)
    np.testing.assert_array_equal(cfg["ssettings"]["extra"], np.array([4, 2, 4]))

@requires_torchvision
@requires_instatorch
def test_training_data_output(temp_config_dir: Path):
    """Verify training data section specifically (requires external libs)."""
    # This test will be skipped if torchvision or instatorch are not installed.
    # Implement assertions based on whether you expect real objects or mocks.
    with open(temp_config_dir, 'r') as f:
        cfg, _ = load_config(f)

    assert "training" in cfg
    training = cfg["training"]
    assert "data" in training
    assert "train_data" in training["data"]
    assert "test_data" in training["data"]
    assert "data_loaders" in training
    assert "train_data_loader_dataset" in training
    # Add more specific assertions here depending on mocking strategy or expected real objects
    # e.g., assert isinstance(training["data"]["train_data"], torchvision.datasets.MNIST)
    # e.g., assert training["train_data_loader_dataset"] == expected_interpolated_value