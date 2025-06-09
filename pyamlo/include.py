

import os
from typing import Any
import yaml

from pyamlo.merge import deep_merge
from pyamlo.tags import ConfigLoader


class IncludeError(Exception):
    """Problems during include! processing."""
    
def load_raw(path: str) -> dict[str, Any]:
    try:
        with open(path) as f:
            return yaml.load(f, Loader=ConfigLoader)
    except FileNotFoundError as e:
        raise IncludeError(f"Include file not found: '{path}'") from e
    except Exception as e:
        raise IncludeError(f"Error loading include file '{path}': {e}") from e


def process_includes(
    raw: dict[str, Any], base_path: str | None = None
) -> dict[str, Any]:
    incs = raw.pop("include!", [])
    merged: dict[str, Any] = {}
    for entry in incs:
        part = _load_include(entry, base_path)
        deep_merge(merged, part)
    return deep_merge(merged, raw)


def _load_include(entry: Any, base_path: str | None = None) -> dict[str, Any]:
    if isinstance(entry, str):
        if base_path is not None and not os.path.isabs(entry):
            entry = os.path.join(os.path.dirname(base_path), entry)
        raw = load_raw(entry)
        # Set base paths for any include specs in the loaded content
        from pyamlo.config import _set_base_paths
        _set_base_paths(raw, entry)
        return raw
    raise IncludeError(f"Invalid include entry: {entry!r}")