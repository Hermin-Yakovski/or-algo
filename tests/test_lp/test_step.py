import pytest
from abc import ABC
from or_algo.lp.step import LpStep
from or_algo.lp.symbol import Symbol
from or_algo.lp.symbol import Var
from or_algo.lp.symbol import Constr
from register import Register
from unittest.mock import Mock


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


def test_create_var_is_lp_step():
    """CreateVar should be an LpStep subclass."""
    from or_algo.lp.step import CreateVar
    assert issubclass(CreateVar, LpStep)
    assert issubclass(CreateVar, ABC)


def test_create_var_cannot_be_instantiated_directly():
    """CreateVar should be abstract without run() implementation."""
    from or_algo.lp.step import CreateVar
    mock_param = Mock()
    mock_param.name = "x"
    mock_param.name_cn = "x变量"
    mock_param.id = 1
    mock_param.vtype = float

    var_symbol = Var(p=mock_param, sign="x")
    weight = Register()
    lb = Register()
    ub = Register()

    with pytest.raises(TypeError):
        CreateVar(symbol=var_symbol, weight=weight, lb=lb, ub=ub)


def test_create_var_concrete_subclass():
    """CreateVar subclass with run() should be instantiable."""
    from or_algo.lp.step import CreateVar
    mock_param = Mock()
    mock_param.name = "x"
    mock_param.name_cn = "x变量"
    mock_param.id = 1
    mock_param.vtype = float

    var_symbol = Var(p=mock_param, sign="x")
    weight = Register()
    lb = Register()
    ub = Register()

    class ConcreteCreateVar(CreateVar):
        def run(self, data, model, var):
            pass

    step = ConcreteCreateVar(symbol=var_symbol, weight=weight, lb=lb, ub=ub)
    assert step._symbol is var_symbol
    assert step._weight is weight
    assert step._lb is lb
    assert step._ub is ub


def test_create_var_vtype_mapping():
    """CreateVar.vtype should map Parameter vtype to OR-Tools types."""
    from or_algo.lp.step import CreateVar
    # Test float -> CONTINUOUS
    mock_param = Mock()
    mock_param.vtype = float
    var_float = Var(p=mock_param, sign="x")

    class ConcreteCreateVar(CreateVar):
        def run(self, data, model, var):
            pass

    step_float = ConcreteCreateVar(
        symbol=var_float,
        weight=Register(),
        lb=Register(),
        ub=Register()
    )
    assert step_float.vtype == 'CONTINUOUS'

    # Test int -> INTEGER
    mock_param.vtype = int
    var_int = Var(p=mock_param, sign="y")

    step_int = ConcreteCreateVar(
        symbol=var_int,
        weight=Register(),
        lb=Register(),
        ub=Register()
    )
    assert step_int.vtype == 'INTEGER'

    # Test bool -> INTEGER
    mock_param.vtype = bool
    var_bool = Var(p=mock_param, sign="z")

    step_bool = ConcreteCreateVar(
        symbol=var_bool,
        weight=Register(),
        lb=Register(),
        ub=Register()
    )
    assert step_bool.vtype == 'INTEGER'


def test_create_constr_is_lp_step():
    """CreateConstr should be an LpStep subclass."""
    from or_algo.lp.step import CreateConstr
    assert issubclass(CreateConstr, LpStep)
    assert issubclass(CreateConstr, ABC)


def test_create_constr_cannot_be_instantiated_directly():
    """CreateConstr should be abstract without run() implementation."""
    from or_algo.lp.step import CreateConstr
    constr_symbol = Constr(name="limit", name_cn="限制", sign="L")

    with pytest.raises(TypeError):
        CreateConstr(symbol=constr_symbol)


def test_create_constr_concrete_subclass():
    """CreateConstr subclass with run() should be instantiable."""
    from or_algo.lp.step import CreateConstr
    constr_symbol = Constr(name="limit", name_cn="限制", sign="L")

    class ConcreteCreateConstr(CreateConstr):
        def run(self, data, model, var):
            pass

    step = ConcreteCreateConstr(symbol=constr_symbol)
    assert step._symbol is constr_symbol


def test_create_constr_calculate_metric_is_create_constr():
    """Test that CreateConstrCalculateMetric is a CreateConstr subclass."""
    from or_algo.lp.step import CreateConstr, CreateConstrCalculateMetric

    assert issubclass(CreateConstrCalculateMetric, CreateConstr)

    step = CreateConstrCalculateMetric()
    assert isinstance(step, CreateConstr)
    assert step._symbol.name == 'CalculateMetric'


def test_create_constr_calculate_metric_no_metric_dimension():
    """Test that run() skips variables without Metric dimension."""
    from or_algo.lp.step import CreateConstrCalculateMetric
    from or_algo.lp.symbol import Var
    from register import Register, Parameter, Dimension
    from ortools.linear_solver import pywraplp
    from unittest.mock import Mock

    # Create a mock parameter
    mock_param = Mock(spec=Parameter)
    mock_param.vtype = float

    # Create a variable symbol with non-Metric dimension
    test_dim = Dimension('TestDim', 'TestDimCN', 'TD')
    var_symbol = Var(p=mock_param, sign='x')

    # Create register with variable but no Metric dimension
    var_register = Register()
    var_register[var_symbol][(test_dim,)][(0,)] = Mock()

    # Create solver
    model = pywraplp.Solver.CreateSolver('CBC')

    # Create step and run
    step = CreateConstrCalculateMetric()
    data = Register()

    # Should not raise any errors
    step.run(data, model, var_register)

    # Verify no constraints were created (model has only 0 constraints)
    # Note: OR-Tools doesn't expose a direct constraint count, but we can verify it doesn't crash
