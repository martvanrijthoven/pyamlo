import importlib
import os
import re
from functools import singledispatchmethod
from inspect import Parameter, signature
from typing import Any

from pyamlo.expressions import ExpressionEvaluator, is_expression
from pyamlo.merge import _load_file, process_includes
from pyamlo.tags import CallSpec, ImportSpec, IncludeSpec, InterpolatedCallSpec, ResolutionError


class Resolver:
    VAR_RE = re.compile(r"\$\{([^}]+)\}")

    def __init__(self) -> None:
        self.ctx: dict[str, Any] = {}
        self._expression_evaluator = ExpressionEvaluator(self._get)

    @singledispatchmethod
    def resolve(self, node: Any, path: str = "") -> Any:
        return node

    @resolve.register
    def _(self, node: ImportSpec, path: str = "") -> Any:
        return _import_attr(node.path)

    @resolve.register
    def _(self, node: IncludeSpec, path: str = "") -> Any:
        fn = self.VAR_RE.sub(lambda m: str(self._get(m.group(1))), node.path)
        if hasattr(node, "_base_path") and node._base_path and not os.path.isabs(fn):
            fn = os.path.join(os.path.dirname(node._base_path), fn)
        raw = _load_file(fn)
        merged = process_includes(raw, fn)
        return self.resolve(merged)

    @resolve.register
    def _(self, node: CallSpec, path: str = "") -> Any:
        fn = _import_attr(node.path)
        args = [self.resolve(a, path) for a in node.args]
        kwargs = {k: self.resolve(v, path) for k, v in node.kwargs.items()}
        inst = _apply_call(fn, args, kwargs)
        self.ctx[path] = inst
        return inst

    @resolve.register
    def _(self, node: InterpolatedCallSpec, path: str = "") -> Any:
        # Handle variable interpolation in the path template
        path_template = node.path_template
        
        # If the path starts with @variable, it means we want to access an object or its method
        if path_template.startswith('@'):
            var_name = path_template[1:]  # Remove the @ prefix
            if '.' in var_name:
                # Split on the first dot to separate object from method/attribute
                obj_name, method_name = var_name.split('.', 1)
                obj = self._get(obj_name)
                fn = getattr(obj, method_name)
            else:
                # Entire path is a variable reference - could be a string (module path) or object
                var_value = self._get(var_name)
                if isinstance(var_value, str):
                    # If it's a string, treat it as a module path to import
                    fn = _import_attr(var_value)
                else:
                    # If it's already an object, use it directly
                    fn = var_value
        else:
            # Handle regular module path with @variable substitutions
            interpolated_path = re.sub(
                r'@([a-zA-Z_][a-zA-Z0-9_]*)',
                lambda m: str(self._get(m.group(1))), 
                path_template
            )
            fn = _import_attr(interpolated_path)
        
        args = [self.resolve(a, path) for a in node.args]
        kwargs = {k: self.resolve(v, path) for k, v in node.kwargs.items()}
        inst = _apply_call(fn, args, kwargs)
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
            expression = m.group(1)
            if is_expression(expression):
                return self._expression_evaluator.evaluate(expression)
            else:
                return self._get(expression)
        return self.VAR_RE.sub(lambda m: self._resolve_interpolation(m.group(1)), node)

    def _resolve_interpolation(self, expression: str) -> str:
        """Resolve a single interpolation expression to string."""
        if is_expression(expression):
            return str(self._expression_evaluator.evaluate(expression))
        else:
            return str(self._get(expression))

    def _get(self, path: str) -> Any:
        root, *rest = path.split(".")
        obj = self.ctx.get(root)
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
