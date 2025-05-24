import importlib
import os
from typing import Any

import yaml

from yamlo.tags import CallSpec, ConfigLoader, ExtendSpec, PatchSpec


class MergeError(Exception):
    """Problems during merging or patching."""


class IncludeError(Exception):
    """Problems during _includes processing."""


def deep_merge(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    for key, val in b.items():
        existing = a.get(key)
        match existing, val:
            case CallSpec() as callspec, PatchSpec(mapping=m):
                callspec.kwargs = m  # type: ignore
            case CallSpec() as callspec, dict() as mapping:
                deep_merge(callspec.kwargs, mapping)
            case list() as base_list, ExtendSpec(items=more):
                a[key] = base_list + more
            case dict() as base_map, PatchSpec(mapping=m):
                a[key] = m
            case _, PatchSpec():
                raise MergeError(f"Cannot patch non-dict at '{key}'")
            case _, ExtendSpec():
                raise MergeError(f"Cannot extend non-list at '{key}'")
            case dict() as base_map, dict() as other_map:
                deep_merge(base_map, other_map)
            case _:
                a[key] = val

    return a


def load_raw(path: str) -> dict[str, Any]:
    try:
        with open(path) as f:
            return yaml.load(f, Loader=ConfigLoader)
    except FileNotFoundError as e:
        raise IncludeError(f"Include file not found: '{path}'") from e
    except Exception as e:
        raise IncludeError(f"Error loading include file '{path}': {e}") from e


def process_includes(raw: dict[str, Any]) -> dict[str, Any]:
    incs = raw.pop("_includes", [])
    merged: dict[str, Any] = {}
    for entry in incs:
        part = _load_include(entry)
        deep_merge(merged, part)
    return deep_merge(merged, raw)


def _is_pkg_include(entry: Any) -> bool:
    return (
        isinstance(entry, (list, tuple))
        and len(entry) == 2
        and isinstance(entry[0], str)
        and isinstance(entry[1], str)
    )


def _load_pkg_include(fn: str, prefix: str) -> dict[str, Any]:
    try:
        pkg = importlib.import_module(prefix)
    except ImportError:
        return load_raw(fn)
    base = str(os.path.dirname(pkg.__file__))  # type: ignore
    cfg_path = os.path.join(base, "configuration", fn)
    return {prefix: load_raw(cfg_path)}


def _load_include(entry: Any) -> dict[str, Any]:
    if isinstance(entry, str):
        return load_raw(entry)
    if _is_pkg_include(entry):
        fn, prefix = entry  # type: ignore
        return _load_pkg_include(fn, prefix)
    raise IncludeError(f"Invalid include entry: {entry!r}")
