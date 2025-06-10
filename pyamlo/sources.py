from pathlib import Path
from typing import IO, Any, Sequence, Union

from pyamlo.merge import deep_merge
from pyamlo.include import process_includes, set_base_paths
from pyamlo.tags import ConfigLoader
from pyamlo.security import SecurityPolicy


def _get_source_path(src: Union[str, Path, IO[str]]) -> str:
    """Get the path string from a source, handling both file paths and IO objects."""
    return src.name if isinstance(src, IO) else str(src)


def _process_single_source(
    src: Union[str, Path, IO[str]], security_policy: SecurityPolicy
) -> dict[str, Any]:
    """Process a single configuration source and return the processed config."""
    raw = _load_yaml(src, security_policy=security_policy)
    if not raw:
        return {}

    src_path = _get_source_path(src)
    if src_path:
        set_base_paths(raw, src_path)

    return process_includes(raw, src_path, security_policy=security_policy)


def _load_yaml(
    source: Union[str, Path, IO[str]], security_policy: SecurityPolicy
) -> dict[str, Any]:
    """Load raw YAML from a file or file-like object."""
    if isinstance(source, (str, Path)):
        with open(source, "r") as f:
            loader = ConfigLoader(f, security_policy=security_policy)
            try:
                return loader.get_single_data()
            finally:
                loader.dispose()
    else:
        loader = ConfigLoader(source, security_policy=security_policy)
        try:
            return loader.get_single_data()
        finally:
            loader.dispose()


def get_sources(
    source: Union[str, Path, IO[str], Sequence[Union[str, Path, IO[str]]]],
) -> list[Union[str, Path, IO[str]]]:
    """Convert source parameter to a list of sources."""
    if not isinstance(source, Sequence) or isinstance(source, (str, Path)):
        return [source]
    return list(source)


def merge_all_sources(
    sources: list[Union[str, Path, IO[str]]], security_policy: SecurityPolicy
) -> dict[str, Any]:
    """Process and merge all configuration sources."""
    config: dict[str, Any] = {}
    for src in sources:
        processed = _process_single_source(src, security_policy)
        if processed:
            config = deep_merge(config, processed)
    return config
