from pathlib import Path
from typing import IO, Any, Sequence, Union
import os

from pyamlo.merge import deep_merge
from pyamlo.include import process_includes, set_base_paths
from pyamlo.tags import ConfigLoader, CallSpec, ExtendSpec, PatchSpec
from pyamlo.security import SecurityPolicy


def _process_dict_tags(data: Any, security_policy: SecurityPolicy) -> Any:
    """Process YAML-style tags in dictionary data."""
    if isinstance(data, dict):
        return {k: _process_dict_tags(v, security_policy) for k, v in data.items()}
    elif isinstance(data, list):
        return [_process_dict_tags(item, security_policy) for item in data]
    elif isinstance(data, str):
        # Check for YAML tags in string values
        if data.startswith("!@"):
            # Object instantiation tag
            parts = data[2:].strip().split(None, 1)
            path = parts[0]
            args = [parts[1]] if len(parts) > 1 else []
            return CallSpec(path, args, {}, is_interpolated=False)
        elif data.startswith("!env "):
            # Environment variable tag
            var = data[5:].strip()
            security_policy.check_env_var(var)
            val = os.environ.get(var)
            if val is None:
                raise ValueError(f"Environment variable '{var}' not set")
            return val
        elif data == "!extend":
            return ExtendSpec([])
        elif data == "!patch":
            return PatchSpec({})
    return data


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
    src: Union[str, Path, IO[str], dict], security_policy: SecurityPolicy
) -> dict[str, Any]:
    if isinstance(src, dict):
        raw = _process_dict_tags(src.copy(), security_policy)
        src_path = "<dict>"
    else:
        raw = _load_source(src, security_policy=security_policy)
        src_path = src.name if isinstance(src, IO) else str(src)
    if not raw:
        return {}
    if src_path and src_path != "<dict>":
        set_base_paths(raw, src_path)
    return process_includes(raw, src_path, security_policy=security_policy)


def get_sources(
    source: Union[str, Path, IO[str], dict, Sequence[Union[str, Path, IO[str], dict]]],
) -> list[Union[str, Path, IO[str], dict]]:
    if not isinstance(source, Sequence) or isinstance(source, (str, Path)):
        return [source]
    return list(source)


def merge_all_sources(
    sources: list[Union[str, Path, IO[str], dict]], security_policy: SecurityPolicy
) -> dict[str, Any]:
    config: dict[str, Any] = {}
    for src in sources:
        processed = _process_single_source(src, security_policy)
        if processed:
            config = deep_merge(config, processed)
    return config
