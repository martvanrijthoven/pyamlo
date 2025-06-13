from pathlib import Path
from typing import IO, Any, Sequence, Union

from pyamlo.merge import deep_merge
from pyamlo.include import process_includes, set_base_paths
from pyamlo.tags import ConfigLoader
from pyamlo.security import SecurityPolicy


def _load_source(
    source: Union[str, Path, IO[str]], security_policy: SecurityPolicy
) -> dict[str, Any]:
    def _load_with_loader(stream):
        loader = ConfigLoader(stream, security_policy=security_policy)
        try:
            return loader.get_single_data()
        finally:
            loader.dispose()
    if isinstance(source, (str, Path)):
        with open(source, "r") as f:
            return _load_with_loader(f)
    return _load_with_loader(source)


def _process_single_source(
    src: Union[str, Path, IO[str]], security_policy: SecurityPolicy
) -> dict[str, Any]:
    raw = _load_source(src, security_policy=security_policy)
    if not raw:
        return {}
    src_path = src.name if isinstance(src, IO) else str(src)
    if src_path:
        set_base_paths(raw, src_path)
    return process_includes(raw, src_path, security_policy=security_policy)


def get_sources(
    source: Union[str, Path, IO[str], Sequence[Union[str, Path, IO[str]]]],
) -> list[Union[str, Path, IO[str]]]:
    if not isinstance(source, Sequence) or isinstance(source, (str, Path)):
        return [source]
    return list(source)


def merge_all_sources(
    sources: list[Union[str, Path, IO[str]]], security_policy: SecurityPolicy
) -> dict[str, Any]:
    config: dict[str, Any] = {}
    for src in sources:
        processed = _process_single_source(src, security_policy)
        if processed:
            config = deep_merge(config, processed)
    return config
