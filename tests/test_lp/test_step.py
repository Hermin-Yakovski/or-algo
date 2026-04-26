import pytest
from abc import ABC
from or_algo.lp.step import LpStep
from or_algo.lp.symbol import Symbol


def test_lp_step_is_abstract():
    """LpStep should be an abstract base class."""
    assert issubclass(LpStep, ABC)

    # Cannot instantiate LpStep directly
    with pytest.raises(TypeError):
        LpStep(symbol=Symbol(name="test", name_cn="测试", sign="t"))


def test_lp_step_requires_run_method():
    """LpStep subclasses must implement the run method."""

    class InvalidStep(LpStep):
        pass  # Missing run() method

    with pytest.raises(TypeError):
        InvalidStep(symbol=Symbol(name="test", name_cn="测试", sign="t"))


def test_lp_step_concrete_subclass():
    """LpStep subclass with run() method should be instantiable."""

    class ConcreteStep(LpStep):
        def run(self, data, model, var):
            pass

    symbol = Symbol(name="test", name_cn="测试", sign="t")
    step = ConcreteStep(symbol=symbol)
    assert step._symbol is symbol
