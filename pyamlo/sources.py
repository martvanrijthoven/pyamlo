from pathlib import Path
from typing import IO, Any, Sequence, Union
import os

from pyamlo.merge import deep_merge
from pyamlo.include import process_includes, set_base_paths
from pyamlo.tags import ConfigLoader
from pyamlo.security import SecurityPolicy


def _process_dict_tags(data: Any, security_policy: SecurityPolicy) -> Any:
    """Process dictionary data - handle both raw dicts and dicts with YAML tag strings."""
    
    def has_yaml_tags(obj):
        """Check if the data structure contains YAML tag-like strings."""
        if isinstance(obj, dict):
            return any(has_yaml_tags(v) for v in obj.values())
        elif isinstance(obj, list):
            return any(has_yaml_tags(item) for item in obj)
        elif isinstance(obj, str):
            return obj.startswith('!')
        return False
    
    # If the dict contains no YAML tag strings, it's already fully resolved
    if not has_yaml_tags(data):
        return data
    
    # Otherwise, process YAML tags using the YAML stream approach (simpler than direct parsing)
    from io import StringIO
    import yaml
    
    def dict_to_yaml_text(obj, indent=0):
        """Convert dict to YAML text without escaping tags."""
        def format_value(val):
            if isinstance(val, str):
                # Don't quote strings that are YAML tags
                if val.startswith('!'):
                    return val
                # Quote strings to preserve them as strings
                dumped = yaml.safe_dump(val, default_flow_style=True).strip()
                # Remove document separators
                if dumped.endswith('\n...'):
                    dumped = dumped[:-4]
                elif dumped.endswith('...'):
                    dumped = dumped[:-3]
                return dumped
            return str(val)
        
        if isinstance(obj, dict):
            lines = []
            for key, value in obj.items():
                if isinstance(value, dict):
                    lines.append("  " * indent + f"{key}:")
                    lines.append(dict_to_yaml_text(value, indent + 1))
                elif isinstance(value, list):
                    lines.append("  " * indent + f"{key}:")
                    for item in value:
                        if isinstance(item, dict):
                            lines.append("  " * (indent + 1) + "-")
                            lines.append(dict_to_yaml_text(item, indent + 2))
                        else:
                            lines.append("  " * (indent + 1) + f"- {format_value(item)}")
                else:
                    lines.append("  " * indent + f"{key}: {format_value(value)}")
            return '\n'.join(lines)
        return str(obj)
    
    # Convert to YAML text and parse with ConfigLoader
    yaml_text = dict_to_yaml_text(data)
    loader = ConfigLoader(StringIO(yaml_text), security_policy=security_policy)
    try:
        return loader.get_single_data()
    finally:
        loader.dispose()


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
