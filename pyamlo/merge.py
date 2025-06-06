import importlib
import os
import re
from typing import Any

import yaml

from pyamlo.tags import CallSpec, ConfigLoader, ExtendSpec, PatchSpec, IncludeAtSpec


class MergeError(Exception):
    """Problems during merging or patching."""


class IncludeError(Exception):
    """Problems during include! processing."""


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


def _load_file(path: str) -> dict[str, Any]:
    """Unified file loading with error handling."""
    try:
        with open(path) as f:
            return yaml.load(f, Loader=ConfigLoader)
    except FileNotFoundError as e:
        raise IncludeError(f"Include file not found: '{path}'") from e
    except Exception as e:
        raise IncludeError(f"Error loading include file '{path}': {e}") from e


def _resolve_path(path: str, base_path: str | None = None, context: dict[str, Any] | None = None) -> str:
    """Unified path resolution with variable interpolation."""
    # Interpolate variables if context provided
    if context:
        for var, value in context.items():
            if not isinstance(value, IncludeAtSpec):  # Skip include specs
                path = path.replace(f"${{{var}}}", str(value))
        
        # Check for unresolved variables
        if '${' in path:
            unresolved = re.findall(r'\$\{([^}]+)\}', path)
            available = [k for k in context.keys() if not isinstance(context[k], IncludeAtSpec)]
            raise IncludeError(
                f"Unresolved variables in path: {', '.join(unresolved)}. "
                f"Available: {', '.join(available)}"
            )
    
    # Resolve relative paths
    if base_path and not os.path.isabs(path):
        path = os.path.join(os.path.dirname(base_path), path)
    
    return path


def process_includes(raw: dict[str, Any], base_path: str | None = None) -> dict[str, Any]:
    """Simplified include processing - handles both traditional and positional includes."""
    # Process traditional include! entries first
    incs = raw.pop("include!", [])
    merged: dict[str, Any] = {}
    for entry in incs:
        part = _load_traditional_include(entry, base_path)
        deep_merge(merged, part)
    
    # Process positional !include_at entries while preserving order
    result = {}
    for key, value in raw.items():
        if isinstance(value, IncludeAtSpec):
            # Load and process the included file
            path = _resolve_path(value.path, base_path, raw)
            included = _load_file(path)
            included = process_includes(included, path)  # Recursive processing
            
            # Always validate keys for !include_at
            if ',' in key:
                # Comma syntax: validate multiple expected keys
                expected_keys = {k.strip() for k in key.split(',')}
            else:
                # Single key syntax: validate only that key
                expected_keys = {key}
            _validate_include_at_keys(included, expected_keys, path)
            
            # Add included content directly to result (replaces the key)
            deep_merge(result, included)
        else:
            # Regular key-value pair
            result[key] = value
    
    # Merge traditional includes first, then positional content
    return deep_merge(merged, result)


def _validate_include_at_keys(included: dict[str, Any], expected_keys: set[str], file_path: str) -> None:
    """Validate that included file only contains expected keys or keys starting with underscore."""
    included_keys = set(included.keys())
    
    # Keys starting with underscore are always allowed (helper/private keys)
    allowed_keys = expected_keys | {k for k in included_keys if k.startswith('_')}
    
    # Find unexpected keys (keys that are not expected and don't start with underscore)
    unexpected_keys = included_keys - allowed_keys
    
    if unexpected_keys:
        expected_list = ', '.join(sorted(expected_keys))
        unexpected_list = ', '.join(sorted(unexpected_keys))
        raise IncludeError(
            f"File '{file_path}' contains unexpected keys: {unexpected_list}. "
            f"Expected keys: {expected_list} (plus any keys starting with underscore)"
        )


def _load_traditional_include(entry: Any, base_path: str | None = None) -> dict[str, Any]:
    """Load traditional include! entries."""
    if isinstance(entry, str):
        path = _resolve_path(entry, base_path)
        content = _load_file(path)
        # Process includes within the loaded file if it contains include! or !include_at tags
        needs_processing = 'include!' in content or any(
            isinstance(v, IncludeAtSpec) for v in content.values()
        )
        return process_includes(content, path) if needs_processing else content
    
    if _is_pkg_include(entry):
        fn, prefix = entry  # type: ignore
        return _load_pkg_include(fn, prefix)
    
    raise IncludeError(f"Invalid include entry: {entry!r}")


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
        return _load_file(fn)
    base = str(os.path.dirname(pkg.__file__))  # type: ignore
    cfg_path = os.path.join(base, "configuration", fn)
    return {prefix: _load_file(cfg_path)}
