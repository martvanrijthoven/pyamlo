"""Test bitwise operations in PYAMLO expressions."""
import pytest
from pyamlo.resolve import Resolver


def test_bitwise_and_operations():
    """Test bitwise AND operations."""
    resolver = Resolver()
    resolver.ctx["a"] = 12  # Binary: 1100
    resolver.ctx["b"] = 5   # Binary: 0101
    resolver.ctx["c"] = 15  # Binary: 1111
    
    # Basic AND
    assert resolver.resolve("${a & b}") == 4    # 1100 & 0101 = 0100
    assert resolver.resolve("${a & c}") == 12   # 1100 & 1111 = 1100
    assert resolver.resolve("${b & c}") == 5    # 0101 & 1111 = 0101
    
    # AND with literals
    assert resolver.resolve("${12 & 5}") == 4
    assert resolver.resolve("${a & 7}") == 4    # 1100 & 0111 = 0100


def test_bitwise_or_operations():
    """Test bitwise OR operations."""
    resolver = Resolver()
    resolver.ctx["a"] = 12  # Binary: 1100
    resolver.ctx["b"] = 5   # Binary: 0101
    resolver.ctx["c"] = 0   # Binary: 0000
    
    # Basic OR
    assert resolver.resolve("${a | b}") == 13   # 1100 | 0101 = 1101
    assert resolver.resolve("${a | c}") == 12   # 1100 | 0000 = 1100
    assert resolver.resolve("${b | c}") == 5    # 0101 | 0000 = 0101
    
    # OR with literals
    assert resolver.resolve("${12 | 5}") == 13
    assert resolver.resolve("${a | 3}") == 15   # 1100 | 0011 = 1111


def test_bitwise_xor_operations():
    """Test bitwise XOR operations."""
    resolver = Resolver()
    resolver.ctx["a"] = 12  # Binary: 1100
    resolver.ctx["b"] = 5   # Binary: 0101
    resolver.ctx["c"] = 12  # Binary: 1100 (same as a)
    
    # Basic XOR
    assert resolver.resolve("${a ^ b}") == 9    # 1100 ^ 0101 = 1001
    assert resolver.resolve("${a ^ c}") == 0    # 1100 ^ 1100 = 0000 (same bits cancel)
    assert resolver.resolve("${b ^ b}") == 0    # Any number XOR itself = 0
    
    # XOR with literals
    assert resolver.resolve("${12 ^ 5}") == 9
    assert resolver.resolve("${a ^ 15}") == 3   # 1100 ^ 1111 = 0011


def test_bitwise_not_operations():
    """Test bitwise NOT operations."""
    resolver = Resolver()
    resolver.ctx["a"] = 12    # Binary: 1100
    resolver.ctx["b"] = 0     # Binary: 0000
    resolver.ctx["neg"] = -1  # Binary: all 1s in two's complement
    
    # Basic NOT (two's complement)
    assert resolver.resolve("${~a}") == -13     # ~12 = -13
    assert resolver.resolve("${~b}") == -1      # ~0 = -1
    assert resolver.resolve("${~neg}") == 0     # ~(-1) = 0
    
    # NOT with literals
    assert resolver.resolve("${~5}") == -6      # ~5 = -6
    assert resolver.resolve("${~255}") == -256  # ~255 = -256


def test_bitwise_shift_operations():
    """Test bitwise shift operations."""
    resolver = Resolver()
    resolver.ctx["num"] = 12  # Binary: 1100
    resolver.ctx["small"] = 3 # Binary: 11
    
    # Left shift (multiply by powers of 2)
    assert resolver.resolve("${num << 1}") == 24   # 12 << 1 = 24 (12 * 2)
    assert resolver.resolve("${num << 2}") == 48   # 12 << 2 = 48 (12 * 4)
    assert resolver.resolve("${small << 3}") == 24 # 3 << 3 = 24 (3 * 8)
    
    # Right shift (divide by powers of 2, floor division)
    assert resolver.resolve("${num >> 1}") == 6    # 12 >> 1 = 6 (12 / 2)
    assert resolver.resolve("${num >> 2}") == 3    # 12 >> 2 = 3 (12 / 4)
    assert resolver.resolve("${48 >> 4}") == 3     # 48 >> 4 = 3 (48 / 16)
    
    # Shift with literals
    assert resolver.resolve("${8 << 2}") == 32
    assert resolver.resolve("${32 >> 3}") == 4


def test_bitwise_operator_precedence():
    """Test bitwise operator precedence."""
    resolver = Resolver()
    resolver.ctx["a"] = 8   # Binary: 1000
    resolver.ctx["b"] = 4   # Binary: 0100  
    resolver.ctx["c"] = 2   # Binary: 0010
    
    # Shift has higher precedence than bitwise AND/OR/XOR
    assert resolver.resolve("${a | b << 1}") == 8   # a | (b << 1) = 8 | 8 = 8
    assert resolver.resolve("${a & c << 2}") == 8   # a & (c << 2) = 8 & 8 = 8
    
    # AND has higher precedence than OR  
    assert resolver.resolve("${a | b & c}") == 8    # a | (b & c) = 8 | 0 = 8
    
    # Parentheses override precedence
    assert resolver.resolve("${(a | b) & c}") == 0  # (8 | 4) & 2 = 12 & 2 = 0


def test_bitwise_in_config():
    """Test bitwise operations in a realistic config scenario."""
    config_data = {
        "permissions": {
            "read": 1,     # Binary: 001
            "write": 2,    # Binary: 010
            "execute": 4,  # Binary: 100
            "user_perms": "${permissions.read | permissions.write}",    # 3 (read + write)
            "admin_perms": "${permissions.read | permissions.write | permissions.execute}",  # 7 (all)
            "readonly_mask": "${~permissions.write}",   # Mask to remove write permission
        },
        "flags": {
            "debug": 1,
            "verbose": 2,
            "trace": 4,
            "current_flags": "${flags.debug | flags.verbose}",  # 3
            "has_debug": "${flags.current_flags & flags.debug}",  # 1 (truthy)
            "toggle_trace": "${flags.current_flags ^ flags.trace}",  # 7 (add trace)
        }
    }
    
    resolver = Resolver()
    result = resolver.resolve(config_data)
    
    # Check permissions
    assert result["permissions"]["user_perms"] == 3
    assert result["permissions"]["admin_perms"] == 7
    assert result["permissions"]["readonly_mask"] == -3
    
    # Check flags
    assert result["flags"]["current_flags"] == 3
    assert result["flags"]["has_debug"] == 1
    assert result["flags"]["toggle_trace"] == 7


def test_bitwise_with_math_operations():
    """Test combining bitwise with arithmetic operations."""
    resolver = Resolver()
    resolver.ctx["base"] = 8
    resolver.ctx["mask"] = 3
    
    # Bitwise operations with arithmetic
    assert resolver.resolve("${(base << 1) + mask}") == 19  # (8 << 1) + 3 = 16 + 3 = 19
    assert resolver.resolve("${base & (mask + 1)}") == 0    # 8 & (3 + 1) = 8 & 4 = 0
    assert resolver.resolve("${base | mask * 2}") == 14     # 8 | (3 * 2) = 8 | 6 = 14


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
