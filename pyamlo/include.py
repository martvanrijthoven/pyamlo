import os
from typing import Any
import yaml

from pyamlo.merge import deep_merge
from pyamlo.security import SecurityPolicy
from pyamlo.tags import ConfigLoader, IncludeFromSpec, IncludeSpec


class IncludeError(Exception):
    """Problems during include! processing."""


def set_base_paths(data: Any, base_path: str) -> None:
    """Recursively set base paths on IncludeSpec and IncludeAsSpec objects."""
    if isinstance(data, (IncludeSpec, IncludeFromSpec)):
        data.set_base_path(base_path)
    elif isinstance(data, dict):
        for value in data.values():
            set_base_paths(value, base_path)
    elif isinstance(data, list):
        for item in data:
            set_base_paths(item, base_path)


def load_raw(path: str) -> dict[str, Any]:
    try:
        with open(path) as f:
            return yaml.load(f, Loader=ConfigLoader)
    except FileNotFoundError as e:
        raise IncludeError(f"Include file not found: '{path}'") from e
    except Exception as e:
        raise IncludeError(f"Error loading include file '{path}': {e}") from e


def process_includes(
    raw: dict[str, Any], base_path: str | None = None, security_policy: SecurityPolicy = None
) -> dict[str, Any]:
    incs = raw.pop("include!", [])
    merged: dict[str, Any] = {}
    for entry in incs:
        part = _load_include(entry, base_path, security_policy=security_policy)
        deep_merge(merged, part)
    return deep_merge(merged, raw)


def _load_include(
    entry: Any, base_path: str | None = None, security_policy: SecurityPolicy = None
) -> dict[str, Any]:
    if isinstance(entry, str):
        if base_path is not None and not os.path.isabs(entry):
            entry = os.path.join(os.path.dirname(base_path), entry)
        if security_policy:
            security_policy.check_include(entry)
        raw = load_raw(entry)
        set_base_paths(raw, entry)
        return raw
    raise IncludeError(f"Invalid include entry: {entry!r}")
