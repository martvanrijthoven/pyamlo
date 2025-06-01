import re
from typing import Any

from pyamlo.tags import ResolutionError
import keyword


class ExpressionError(Exception):
    """Errors specific to expression evaluation."""


# fmt: off
MATH_OPERATORS = {"+", "-", "*", "/", "//", "%", "**", "(", ")", "&", "|", "^", "~", "<<", ">>"}
# fmt: on
COMPARISON_OPERATORS = {"==", "!=", "<=", ">=", "<", ">"}
LOGICAL_OPERATORS = {"and", "or", "not", "if", "else"}
LOGICAL_PATTERNS = [rf"\b{op}\b" for op in LOGICAL_OPERATORS]


def is_expression(expression: str) -> bool:
    return _has_operators(
        expression, MATH_OPERATORS | COMPARISON_OPERATORS
    ) or _has_logical_operators(expression)


def _has_operators(expression: str, operators: set[str]) -> bool:
    return any(op in expression for op in operators)


def _has_logical_operators(expression: str) -> bool:
    return any(re.search(pattern, expression) for pattern in LOGICAL_PATTERNS)


def _is_math_operation(expression: str) -> bool:
    has_math = _has_operators(expression, MATH_OPERATORS)
    has_comparison = _has_operators(expression, COMPARISON_OPERATORS)
    has_logical = _has_logical_operators(expression)
    return has_math and not has_comparison and not has_logical


def _extract_variables(expression: str) -> list[str]:
    no_strings = re.sub(r'"[^"]*"|\'[^\']*\'', "", expression)
    var_pattern = re.compile(r"\b[a-zA-Z_][a-zA-Z0-9_.]*\b")
    all_words = var_pattern.findall(no_strings)
    return [word for word in all_words if word not in keyword.kwlist]


def _should_validate_as_numeric(var_name: str, variables_found: list[str]) -> bool:
    dotted_vars_with_this_prefix = [
        v for v in variables_found if v.startswith(var_name + ".")
    ]
    return not dotted_vars_with_this_prefix


def _get_safe(expression: str, var_name: str) -> tuple[str, str]:
    safe_name = var_name.replace(".", "_") if "." in var_name else var_name
    if safe_name != var_name:
        expression = expression.replace(var_name, safe_name)
    return safe_name, expression


def _validate_variable(
    var_name: str,
    value: Any,
    variables_found: list[str],
) -> None:
    validate_numeric = _should_validate_as_numeric(var_name, variables_found)
    numeric = isinstance(value, (int, float, bool))

    if ("." in var_name or validate_numeric) and not numeric:
        raise ExpressionError(
            f"Cannot use non-numeric value '{var_name}' in math expression "
            f"(got {type(value).__name__})"
        )


class ExpressionEvaluator:
    def __init__(self, variable_resolver):
        self._get = variable_resolver

    def evaluate(self, expression: str) -> Any:
        safe_expression, namespace = self._get_safe_expr_with_ns(expression)
        try:
            return eval(safe_expression, {"__builtins__": {}}, namespace)
        except ZeroDivisionError:
            raise ExpressionError(f"Division by zero in expression '{expression}'")
        except Exception as e:
            raise ExpressionError(f"Invalid expression '{expression}': {e}")

    def _get_safe_expr_with_ns(self, expression):
        variables_found = _extract_variables(expression)
        is_math = _is_math_operation(expression)

        namespace = {}
        safe_expression = expression
        for var_name in variables_found:
            try:
                value = self._get(var_name)
                if is_math:
                    _validate_variable(var_name, value, variables_found)
                safe_name, safe_expression = _get_safe(safe_expression, var_name)
                namespace[safe_name] = value
            except (ResolutionError, ExpressionError):
                raise
            except Exception as e:
                raise ExpressionError(f"Failed to resolve variable '{var_name}': {e}")
        return safe_expression, namespace
