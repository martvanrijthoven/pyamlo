import os
import pytest
from pyamlo.config import load_config
from pyamlo.security import SecurityPolicy
from pathlib import Path
from io import StringIO

def test_env_var_denied(tmp_path):
    policy = SecurityPolicy()
    # No env vars allowed by default
    os.environ["TEST_DENIED"] = "should_not_be_accessible"
    config_path = tmp_path / "env.yaml"
    config_path.write_text("db_user: !env TEST_DENIED\n")
    with pytest.raises(PermissionError):
        load_config(config_path, security_policy=policy)

def test_env_var_allowed(tmp_path):
    policy = SecurityPolicy()
    policy.allowed_env_vars.add("TEST_ALLOWED")
    os.environ["TEST_ALLOWED"] = "yes"
    config_path = tmp_path / "env.yaml"
    config_path.write_text("db_user: !env TEST_ALLOWED\n")
    config = load_config(config_path, security_policy=policy)
    assert config["db_user"] == "yes"

def test_import_denied():
    policy = SecurityPolicy()
    # No imports allowed by default
    yaml_content = "path: !import pathlib.Path"
    with pytest.raises(PermissionError):
        load_config(StringIO(yaml_content), security_policy=policy)

def test_import_allowed():
    policy = SecurityPolicy()
    policy.allowed_imports.add("pathlib.Path")
    yaml_content = "path: !import pathlib.Path"
    config = load_config(StringIO(yaml_content), security_policy=policy)
    from pathlib import Path
    assert isinstance(config["path"], type(Path))

def test_include_denied(tmp_path):
    policy = SecurityPolicy()
    # No includes allowed by default
    inc = tmp_path / "inc.yaml"
    inc.write_text("foo: 1\n")
    main = tmp_path / "main.yaml"
    main.write_text(f"include!: ['{inc}']\n")
    with pytest.raises(PermissionError):
        load_config(main, security_policy=policy)

def test_include_allowed(tmp_path):
    policy = SecurityPolicy()
    inc = tmp_path / "inc.yaml"
    inc.write_text("foo: 1\n")
    policy.allowed_include_paths.add(str(inc))
    main = tmp_path / "main.yaml"
    main.write_text(f"include!: ['{inc}']\n")
    config = load_config(main, security_policy=policy)
    assert config["foo"] == 1

def test_expression_denied():
    policy = SecurityPolicy()
    yaml_content = "foo: ${1+2}"
    from io import StringIO
    with pytest.raises(PermissionError):
        load_config(StringIO(yaml_content), security_policy=policy)

def test_expression_allowed():
    policy = SecurityPolicy()
    policy.allow_expressions = True
    expression_content = "foo: ${1+2}"
    config = load_config(StringIO(expression_content), security_policy=policy)
    assert config["foo"] == 3
