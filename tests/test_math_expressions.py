"""Tests for math expressions in variable interpolation."""

import pytest

from pyamlo import load_config
from pyamlo.resolve import Resolver
from pyamlo.tags import ResolutionError
from pyamlo.expressions import ExpressionError


def test_basic_math_operations():
    """Test basic arithmetic operations."""
    resolver = Resolver()
    resolver.ctx["a"] = 10
    resolver.ctx["b"] = 3
    
    # Addition
    assert resolver.resolve("${a + b}") == 13
    
    # Subtraction  
    assert resolver.resolve("${a - b}") == 7
    
    # Multiplication
    assert resolver.resolve("${a * b}") == 30
    
    # Division
    assert resolver.resolve("${a / b}") == 10 / 3
    
    # Floor division
    assert resolver.resolve("${a // b}") == 3
    
    # Modulo
    assert resolver.resolve("${a % b}") == 1
    
    # Power
    assert resolver.resolve("${b ** 2}") == 9


def test_math_with_literals():
    """Test math operations with literal numbers."""
    resolver = Resolver()
    resolver.ctx["count"] = 5
    
    # Variable with literal
    assert resolver.resolve("${count * 2}") == 10
    assert resolver.resolve("${count + 10}") == 15
    assert resolver.resolve("${100 / count}") == 20.0
    
    # Pure literals
    assert resolver.resolve("${2 + 3}") == 5
    assert resolver.resolve("${10.5 * 2}") == 21.0


def test_math_in_string_interpolation():
    """Test math expressions within string interpolation."""
    resolver = Resolver()
    resolver.ctx["workers"] = 4
    resolver.ctx["factor"] = 2
    
    result = resolver.resolve("Total workers: ${workers * factor}")
    assert result == "Total workers: 8"
    
    result = resolver.resolve("Port: ${8000 + workers}")
    assert result == "Port: 8004"


def test_math_with_nested_variables():
    """Test math expressions with nested object references."""
    resolver = Resolver()
    resolver.ctx["app"] = {"workers": 4, "scaling": 2.5}
    resolver.ctx["config"] = {"base_port": 8000}
    
    assert resolver.resolve("${app.workers * app.scaling}") == 10.0
    assert resolver.resolve("${config.base_port + app.workers}") == 8004


def test_complex_config_with_math():
    """Test a complete config using math expressions."""
    data = {
        "app": {
            "workers": 4,
            "scaling_factor": 2
        },
        "database": {
            "pool_size": "${app.workers * app.scaling_factor}",
            "timeout": "${app.workers + 5}"
        },
        "services": {
            "web": {
                "port": "${8000 + 1}",
                "workers": "${app.workers / 2}"
            },
            "api": {
                "port": "${8000 + 2}",
                "memory_per_worker": 512,
                "total_memory": "${512 * app.workers}"  # Use literal instead of circular reference
            }
        }
    }

    resolver = Resolver()
    result = resolver.resolve(data)

    assert result["database"]["pool_size"] == 8
    assert result["database"]["timeout"] == 9
    assert result["services"]["web"]["port"] == 8001
    assert result["services"]["web"]["workers"] == 2.0
    assert result["services"]["api"]["port"] == 8002
    assert result["services"]["api"]["total_memory"] == 2048


def test_math_expression_errors():
    """Test error handling for invalid math expressions."""
    resolver = Resolver()
    resolver.ctx["zero"] = 0
    resolver.ctx["text"] = "hello"

    # Division by zero - expect the actual Python error message
    with pytest.raises(ExpressionError, match="division by zero"):
        resolver.resolve("${10 / zero}")

    # Type error for invalid operations
    with pytest.raises(ExpressionError, match="Invalid expression"):
        resolver.resolve("${text + 5}")  # Can't add string and int


def test_operator_precedence():
    """Test that operator precedence works correctly."""
    resolver = Resolver()
    
    # Power has highest precedence
    assert resolver.resolve("${2 ** 3 * 2}") == 16  # (2^3) * 2 = 8 * 2 = 16
    
    # Multiplication before addition  
    assert resolver.resolve("${2 + 3 * 4}") == 14  # 2 + (3*4) = 2 + 12 = 14
    
    # Floor division before addition
    assert resolver.resolve("${10 + 15 // 3}") == 15  # 10 + (15//3) = 10 + 5 = 15


def test_floating_point_results():
    """Test that floating point operations work correctly."""
    resolver = Resolver()
    resolver.ctx["pi"] = 3.14159
    
    assert resolver.resolve("${pi * 2}") == pytest.approx(6.28318)
    assert resolver.resolve("${22 / 7}") == pytest.approx(3.142857)
    assert resolver.resolve("${pi + 1.5}") == pytest.approx(4.64159)


def test_yaml_file_with_math(tmp_path):
    """Test loading a complete YAML file with math expressions."""
    config_content = """
app:
  name: TestApp
  workers: 4
  scaling_factor: 2.5
  base_port: 8000

database:
  pool_size: ${app.workers * app.scaling_factor}
  timeout: ${app.workers + 5}
  connections_per_worker: ${database.pool_size / app.workers}

services:
  web:
    port: ${app.base_port + 1}
    memory_mb: ${256 * app.workers}
  api:
    port: ${app.base_port + 2}
    threads: ${app.workers / 2}

monitoring:
  port: ${app.base_port + 100}
  check_interval: ${30 * 60}  # 30 minutes in seconds
"""
    
    config_file = tmp_path / "test_math.yaml"
    config_file.write_text(config_content)
    
    config = load_config(str(config_file))
    
    # Verify all math expressions were resolved correctly
    assert config["database"]["pool_size"] == 10.0
    assert config["database"]["timeout"] == 9
    assert config["database"]["connections_per_worker"] == 2.5
    assert config["services"]["web"]["port"] == 8001
    assert config["services"]["web"]["memory_mb"] == 1024
    assert config["services"]["api"]["port"] == 8002
    assert config["services"]["api"]["threads"] == 2.0
    assert config["monitoring"]["port"] == 8100
    assert config["monitoring"]["check_interval"] == 1800
