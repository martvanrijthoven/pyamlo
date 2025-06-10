import os
from collections import UserDict, UserList
from typing import Any, Hashable, Optional, Union

from yaml import MappingNode, SafeLoader, ScalarNode, SequenceNode

from pyamlo.security import SecurityPolicy


class ResolutionError(Exception):
    """Problems during interpolation or object resolution."""


class TagError(Exception):
    """Problems during interpolation or object resolution."""


class ExtendSpec(UserList):
    def __init__(self, items: list[Any]) -> None:
        super().__init__(items)
        self.items = items


class PatchSpec(UserDict):
    def __init__(self, mapping: dict[Hashable, Any]) -> None:
        super().__init__(mapping)
        self.mapping = mapping


class CallSpec:
    def __init__(
        self,
        path: str,
        args: list[Any],
        kwargs: dict[str, Any],
    ) -> None:
        self.path: str = path
        self.args: list[Any] = args
        self.kwargs: dict[str, Any] = kwargs


class InterpolatedCallSpec:
    """A CallSpec that defers path interpolation until resolution time."""

    def __init__(
        self,
        path_template: str,
        args: list[Any],
        kwargs: dict[str, Any],
    ):
        self.path_template = path_template  # Contains {variable} placeholders
        self.args = args
        self.kwargs = kwargs


class IncludeSpec:
    def __init__(self, path: str):
        self.path = path
        self._base_path: Optional[str] = None

    def set_base_path(self, base_path: str) -> None:
        self._base_path = base_path


class ImportSpec:
    def __init__(self, path: str):
        self.path = path


class IncludeFromSpec:
    def __init__(self, path: str):
        self.path = path
        self._base_path: Optional[str] = None

    def set_base_path(self, base_path: str) -> None:
        self._base_path = base_path


class ConfigLoader(SafeLoader):
    def __init__(self, stream, security_policy=SecurityPolicy(restrictive=False)):
        super().__init__(stream)
        self.security_policy = security_policy


def construct_env(loader: ConfigLoader, node: Union[ScalarNode, MappingNode]) -> Any:
    
    if isinstance(node, ScalarNode):
        var = loader.construct_scalar(node)
        loader.security_policy.check_env_var(var)
        val = os.environ.get(var)
        if val is None:
            raise ResolutionError(
                f"Environment variable '{var}' not set {node.start_mark}"
            )
        return val
    elif isinstance(node, MappingNode):
        mapping = loader.construct_mapping(node, deep=True)
        var = mapping.get("var") or mapping.get("name")
        default = mapping.get("default")
        loader.security_policy.check_env_var(var)
        val = os.environ.get(var, default)
        if val is None:
            raise ResolutionError(
                f"Environment variable '{var}' not set and no default provided {node.start_mark}"
            )
        return val
    raise TagError(
        f"!env must be used with a scalar or mapping node at {node.start_mark}"
    )


def construct_extend(loader: ConfigLoader, node: SequenceNode) -> ExtendSpec:
    if not isinstance(node, SequenceNode):
        raise TagError(f"!extend must be used on a YAML sequence at {node.start_mark}")
    return ExtendSpec(loader.construct_sequence(node, deep=True))


def construct_patch(loader: ConfigLoader, node: MappingNode) -> PatchSpec:
    if not isinstance(node, MappingNode):
        raise TagError(f"!patch must be used on a YAML mapping at {node.start_mark}")
    return PatchSpec(loader.construct_mapping(node, deep=True))


def _construct_callspec_args(
    loader: ConfigLoader, node: Union[MappingNode, SequenceNode, ScalarNode]
) -> tuple[list[Any], dict[str, Any]]:
    """Extract args and kwargs from a node."""
    if isinstance(node, MappingNode):
        return [], loader.construct_mapping(node, deep=True)
    elif isinstance(node, SequenceNode):
        return loader.construct_sequence(node, deep=True), {}
    elif isinstance(node, ScalarNode):
        scalar = loader.construct_scalar(node)
        args = [] if scalar in (None, "") else [scalar]
        return args, {}
    raise TagError(f"Unsupported node type at {node.start_mark}")


def construct_callspec(
    loader: ConfigLoader,
    suffix: str,
    node: Union[MappingNode, SequenceNode, ScalarNode],
) -> CallSpec:
    args, kwargs = _construct_callspec_args(loader, node)
    return CallSpec(suffix, args, kwargs)


def construct_interpolated_callspec(
    loader: ConfigLoader,
    suffix: str,
    node: Union[MappingNode, SequenceNode, ScalarNode],
) -> InterpolatedCallSpec:
    args, kwargs = _construct_callspec_args(loader, node)
    return InterpolatedCallSpec(suffix, args, kwargs)


def construct_include(loader: ConfigLoader, node: ScalarNode) -> IncludeSpec:
    path = loader.construct_scalar(node)
    loader.security_policy.check_include(path)
    return IncludeSpec(path)


def construct_import(loader: ConfigLoader, node: ScalarNode) -> ImportSpec:
    if not isinstance(node, ScalarNode):
        raise TagError(f"!import must be used with a string path at {node.start_mark}")
    path = loader.construct_scalar(node)
    loader.security_policy.check_import(path)
    return ImportSpec(path)


def construct_include_from(loader: ConfigLoader, node: ScalarNode) -> IncludeFromSpec:
    if not isinstance(node, ScalarNode):
        raise TagError(
            f"!include_from must be used with a file path at {node.start_mark}"
        )

    path = loader.construct_scalar(node)
    if not path:
        raise TagError(
            f"!include_from requires a non-empty file path at {node.start_mark}"
        )

    return IncludeFromSpec(path)


ConfigLoader.add_multi_constructor("!@", construct_callspec)
ConfigLoader.add_multi_constructor("!$", construct_interpolated_callspec)
ConfigLoader.add_constructor("!env", construct_env)
ConfigLoader.add_constructor("!extend", construct_extend)
ConfigLoader.add_constructor("!patch", construct_patch)
ConfigLoader.add_constructor("!include", construct_include)
ConfigLoader.add_constructor("!import", construct_import)
ConfigLoader.add_constructor("!include_from", construct_include_from)
