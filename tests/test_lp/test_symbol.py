"""Tests for Symbol base class."""

from or_algo.lp.symbol import Symbol
from or_algo.lp.symbol import Var
from unittest.mock import Mock


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


def test_var_creation():
    """Var should wrap a Parameter."""
    mock_param = Mock()
    mock_param.name = "x_var"
    mock_param.name_cn = "x变量"
    mock_param.id = 42

    var = Var(p=mock_param, sign="x")
    assert var.name == "x_var"
    assert var.name_cn == "x变量"
    assert var.sign == "x"
    assert var.id == 42
    assert var.parameter is mock_param


def test_var_inherits_from_symbol():
    """Var should be a Symbol subclass."""
    mock_param = Mock()
    mock_param.name = "test"
    mock_param.name_cn = "测试"
    mock_param.id = 1

    var = Var(p=mock_param, sign="t")
    assert isinstance(var, Symbol)
    assert str(var) == "t"
    assert repr(var) == "test"
