"""Tests for Symbol base class."""

import pytest
from or_algo.lp.symbol import Symbol


def test_symbol_creation():
    """Symbol should store name, name_cn, and sign."""
    symbol = Symbol(name="test", name_cn="测试", sign="t")
    assert symbol.name == "test"
    assert symbol.name_cn == "测试"
    assert symbol.sign == "t"


def test_symbol_str_returns_sign():
    """Symbol.__str__ should return sign."""
    symbol = Symbol(name="test", name_cn="测试", sign="X")
    assert str(symbol) == "X"


def test_symbol_repr_returns_name():
    """Symbol.__repr__ should return name."""
    symbol = Symbol(name="test_var", name_cn="测试变量", sign="x")
    assert repr(symbol) == "test_var"


def test_symbol_has_vtype_attribute():
    """Symbol should have a vtype attribute (initially None)."""
    symbol = Symbol(name="test", name_cn="测试", sign="t")
    # vtype will be set by subclasses
    assert hasattr(symbol, 'vtype')
