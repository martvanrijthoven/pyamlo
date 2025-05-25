import importlib
import re
from functools import singledispatchmethod
from inspect import Parameter, signature
from typing import Any

from pyamlo.merge import load_raw, process_includes
from pyamlo.tags import CallSpec, IncludeSpec, ResolutionError


class Resolver:
    VAR_RE = re.compile(r"\$\{([^}]+)\}")

    def __init__(self) -> None:
        self.ctx: dict[str, Any] = {}
        self.instances: dict[str, Any] = {}

    @singledispatchmethod
    def resolve(self, node: Any, path: str = "") -> Any:
        return node

    @resolve.register
    def _(self, node: IncludeSpec, path: str = "") -> Any:
        fn = self.VAR_RE.sub(lambda m: str(self._get(m.group(1))), node.path)
        raw = load_raw(fn)
        merged = process_includes(raw)
        return self.resolve(merged)

    @resolve.register
    def _(self, node: CallSpec, path: str = "") -> Any:
        fn = _import_attr(node.path)
        args = [self.resolve(a, path) for a in node.args]
        kwargs = {k: self.resolve(v, path) for k, v in node.kwargs.items()}
        inst = _apply_call(fn, args, kwargs)
        name = node.id or path
        if name:
            self.instances[name] = inst
        self.ctx[path] = inst
        return inst

    @resolve.register
    def _(self, node: dict, path: str = "") -> dict[str, Any]:
        out: dict[str, Any] = {}
        self.ctx[path] = out
        for key, val in node.items():
            child = f"{path}.{key}" if path else key
            out[key] = self.ctx[child] = self.resolve(val, child)
        return out

    @resolve.register
    def _(self, node: list, path: str = "") -> list[Any]:
        return [self.resolve(x, path) for x in node]

    @resolve.register
    def _(self, node: str, path: str = "") -> Any:
        if m := self.VAR_RE.fullmatch(node):
            return self._get(m.group(1))
        return self.VAR_RE.sub(lambda m: str(self._get(m.group(1))), node)

    def _get(self, path: str) -> Any:
        root, *rest = path.split(".")
        obj = self.instances.get(root, self.ctx.get(root))
        if obj is None:
            raise ResolutionError(f"Unknown variable '{root}'")
        for tok in rest:
            try:
                obj = obj[tok] if isinstance(obj, dict) else getattr(obj, tok)
            except Exception as e:
                raise ResolutionError(
                    f"Failed to resolve '{tok}' in '{path}': {e}"
                ) from e
        return obj


def call(calling, **kwargs):
    if not kwargs:
        return calling()
    return calling(**kwargs)


def _import_attr(path: str):
    module, _, name = path.rpartition(".")
    mod = importlib.import_module(module or "builtins")
    return getattr(mod, name or module)


def _apply_call(fn, args, kwargs):
    try:
        sig = signature(fn)
        params = sig.parameters.values()

        has_starargs = any(p.kind is Parameter.VAR_POSITIONAL for p in params)
        num_positional = sum(
            p.kind in (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD)
            for p in params
        )

        if not has_starargs and num_positional == 1 and len(args) > 1:
            return fn([args], **kwargs)

    except (ValueError, TypeError):
        if len(args) > 1:
            return fn([args], **kwargs)
    return fn(*args, **kwargs)
