from typing import Any

from pyamlo.tags import CallSpec, ExtendSpec, PatchSpec


class MergeError(Exception):
    """Problems during merging or patching."""


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
