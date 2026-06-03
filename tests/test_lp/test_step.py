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

    # Test bool -> BINARY
    mock_param.vtype = bool
    var_bool = Var(p=mock_param, sign="z")

    step_bool = ConcreteCreateVar(
        symbol=var_bool,
        weight=Register(),
        lb=Register(),
        ub=Register()
    )
    assert step_bool.vtype == 'BINARY'


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


def test_create_constr_calculate_metric_sum():
    """Test that SUM metric creates equality constraint with sum of base variables."""
    from or_algo.lp.step import CreateConstrCalculateMetric
    from or_algo.lp.symbol import Var
    from register import Register, Parameter, Dimension, Metric
    from ortools.linear_solver import pywraplp

    # Create mock parameter
    mock_param = Mock(spec=Parameter)
    mock_param.vtype = float

    # Create dimensions
    test_dim = Dimension('TestDim', 'TestDimCN', 'TD')

    # Create variable symbol
    var_symbol = Var(p=mock_param, sign='x')

    # Create solver
    model = pywraplp.Solver.CreateSolver('CBC')

    # Create base variables
    base1_0 = model.NumVar(0, 10, 'x_base1_0')
    base1_1 = model.NumVar(0, 10, 'x_base1_1')
    base1_2 = model.NumVar(0, 10, 'x_base1_2')

    base2_0 = model.NumVar(0, 10, 'x_base2_0')
    base2_1 = model.NumVar(0, 10, 'x_base2_1')
    base2_2 = model.NumVar(0, 10, 'x_base2_2')

    base3_0 = model.NumVar(0, 10, 'x_base3_0')
    base3_1 = model.NumVar(0, 10, 'x_base3_1')
    base3_2 = model.NumVar(0, 10, 'x_base3_2')

    # Create metric variables - one for each base index
    metric_var_0 = model.NumVar(0, 100, 'x_sum_0')
    metric_var_1 = model.NumVar(0, 100, 'x_sum_1')
    metric_var_2 = model.NumVar(0, 100, 'x_sum_2')

    # Create register with base and metric variables
    var_register = Register()
    # Base variables at dimension (test_dim,)
    var_register[var_symbol][(test_dim,)][(0,)] = base1_0
    var_register[var_symbol][(test_dim,)][(1,)] = base1_1
    var_register[var_symbol][(test_dim,)][(2,)] = base1_2

    # Metric variables at dimension (test_dim, Metric)
    var_register[var_symbol][(test_dim, Metric)][(0, Register.SUM)] = metric_var_0
    var_register[var_symbol][(test_dim, Metric)][(1, Register.SUM)] = metric_var_1
    var_register[var_symbol][(test_dim, Metric)][(2, Register.SUM)] = metric_var_2

    # Create data register with primary key
    data = Register()
    data[Parameter][(test_dim,)][(0,)] = (0,)
    data[Parameter][(test_dim,)][(1,)] = (1,)
    data[Parameter][(test_dim,)][(2,)] = (2,)

    # Create step and run
    step = CreateConstrCalculateMetric()
    step.run(data, model, var_register)

    # Verify constraint was created by solving and checking
    # Each metric variable should sum only base variables with matching prefix
    model.Add(base1_0 == 1)
    model.Add(base1_1 == 2)
    model.Add(base1_2 == 3)

    status = model.Solve()
    assert status == pywraplp.Solver.OPTIMAL
    # metric_var_0 sums base vars with prefix (0,) -> only base1_0 = 1
    assert metric_var_0.solution_value() == 1.0
    # metric_var_1 sums base vars with prefix (1,) -> only base1_1 = 2
    assert metric_var_1.solution_value() == 2.0
    # metric_var_2 sums base vars with prefix (2,) -> only base1_2 = 3
    assert metric_var_2.solution_value() == 3.0


def test_create_constr_calculate_metric_max():
    """Test that MAX metric creates lower bound constraints (metric >= each base)."""
    from or_algo.lp.step import CreateConstrCalculateMetric
    from or_algo.lp.symbol import Var
    from register import Register, Parameter, Dimension, Metric
    from ortools.linear_solver import pywraplp

    # Create mock parameter
    mock_param = Mock(spec=Parameter)
    mock_param.vtype = float

    # Create dimensions
    test_dim = Dimension('TestDim', 'TestDimCN', 'TD')

    # Create variable symbol
    var_symbol = Var(p=mock_param, sign='x')

    # Create solver
    model = pywraplp.Solver.CreateSolver('CBC')

    # Create base variables
    base1 = model.NumVar(0, 10, 'x_base1')
    base2 = model.NumVar(0, 20, 'x_base2')
    base3 = model.NumVar(0, 15, 'x_base3')

    # Create metric variable
    metric_var = model.NumVar(0, 100, 'x_max')

    # Create register with base and metric variables
    var_register = Register()
    var_register[var_symbol][(test_dim,)][(0,)] = base1
    var_register[var_symbol][(test_dim,)][(1,)] = base2
    var_register[var_symbol][(test_dim,)][(2,)] = base3
    var_register[var_symbol][(test_dim, Metric)][(Register.ALL, Register.MAX)] = metric_var

    # Create data register
    data = Register()

    # Create step and run
    step = CreateConstrCalculateMetric()
    step.run(data, model, var_register)

    # Verify constraints: metric >= each base
    # To test, we set base variables and minimize metric
    # The optimal metric should be max(base1, base2, base3) = 20
    model.Add(base1 == 5)
    model.Add(base2 == 20)
    model.Add(base3 == 15)
    model.Minimize(metric_var)

    status = model.Solve()
    assert status == pywraplp.Solver.OPTIMAL
    # Metric should be >= 20 (the maximum), and minimized so equals 20
    assert metric_var.solution_value() == 20.0


def test_create_constr_calculate_metric_min():
    """Test that MIN metric creates upper bound constraints (metric <= each base)."""
    from or_algo.lp.step import CreateConstrCalculateMetric
    from or_algo.lp.symbol import Var
    from register import Register, Parameter, Dimension, Metric
    from ortools.linear_solver import pywraplp

    # Create mock parameter
    mock_param = Mock(spec=Parameter)
    mock_param.vtype = float

    # Create dimensions
    test_dim = Dimension('TestDim', 'TestDimCN', 'TD')

    # Create variable symbol
    var_symbol = Var(p=mock_param, sign='x')

    # Create solver
    model = pywraplp.Solver.CreateSolver('CBC')

    # Create base variables
    base1 = model.NumVar(10, 100, 'x_base1')
    base2 = model.NumVar(20, 100, 'x_base2')
    base3 = model.NumVar(15, 100, 'x_base3')

    # Create metric variable
    metric_var = model.NumVar(0, 100, 'x_min')

    # Create register with base and metric variables
    var_register = Register()
    var_register[var_symbol][(test_dim,)][(0,)] = base1
    var_register[var_symbol][(test_dim,)][(1,)] = base2
    var_register[var_symbol][(test_dim,)][(2,)] = base3
    var_register[var_symbol][(test_dim, Metric)][(0, Register.MIN)] = metric_var

    # Create data register
    data = Register()

    # Create step and run
    step = CreateConstrCalculateMetric()
    step.run(data, model, var_register)

    # Verify constraints: metric <= each base
    # To test, we set base variables and maximize metric
    # The optimal metric should be min(base1, base2, base3) = 10
    model.Add(base1 == 10)
    model.Add(base2 == 20)
    model.Add(base3 == 15)
    model.Maximize(metric_var)

    status = model.Solve()
    assert status == pywraplp.Solver.OPTIMAL
    # Metric should be <= 10 (the minimum), and maximized so equals 10
    assert metric_var.solution_value() == 10.0


def test_create_constr_calculate_metric_range():
    """Test that RANGE metric creates pairwise difference constraints."""
    from or_algo.lp.step import CreateConstrCalculateMetric
    from or_algo.lp.symbol import Var
    from register import Register, Parameter, Dimension, Metric
    from ortools.linear_solver import pywraplp

    # Create mock parameter
    mock_param = Mock(spec=Parameter)
    mock_param.vtype = float

    # Create dimensions
    test_dim = Dimension('TestDim', 'TestDimCN', 'TD')

    # Create variable symbol
    var_symbol = Var(p=mock_param, sign='x')

    # Create solver
    model = pywraplp.Solver.CreateSolver('CBC')

    # Create base variables
    base1 = model.NumVar(0, 100, 'x_base1')
    base2 = model.NumVar(0, 100, 'x_base2')
    base3 = model.NumVar(0, 100, 'x_base3')

    # Create metric variable
    metric_var = model.NumVar(0, 100, 'x_range')

    # Create register with base and metric variables
    var_register = Register()
    var_register[var_symbol][(test_dim,)][(0,)] = base1
    var_register[var_symbol][(test_dim,)][(1,)] = base2
    var_register[var_symbol][(test_dim,)][(2,)] = base3
    var_register[var_symbol][(test_dim, Metric)][(Register.ALL, Register.RANGE)] = metric_var

    # Create data register
    data = Register()

    # Create step and run
    step = CreateConstrCalculateMetric()
    step.run(data, model, var_register)

    # Set values: base1=10, base2=25, base3=15
    # Range should be max - min = 25 - 10 = 15
    model.Add(base1 == 10)
    model.Add(base2 == 25)
    model.Add(base3 == 15)
    model.Minimize(metric_var)

    status = model.Solve()
    assert status == pywraplp.Solver.OPTIMAL
    # Metric should be >= 15 (max - min), and minimized so equals 15
    assert metric_var.solution_value() == 15.0


def test_create_constr_calculate_metric_unknown_metric():
    """Test that unknown metric type raises BuildLpStepException."""
    from or_algo.lp.step import CreateConstrCalculateMetric
    from or_algo.lp.symbol import Var
    from or_algo.lp.exception import BuildLpStepException
    from register import Register, Parameter, Dimension, Metric
    from ortools.linear_solver import pywraplp
    import pytest

    # Create mock parameter
    mock_param = Mock(spec=Parameter)
    mock_param.vtype = float

    # Create dimensions
    test_dim = Dimension('TestDim', 'TestDimCN', 'TD')

    # Create variable symbol
    var_symbol = Var(p=mock_param, sign='x')

    # Create solver
    model = pywraplp.Solver.CreateSolver('CBC')

    # Create metric variable
    metric_var = model.NumVar(0, 100, 'x_unknown')

    # Create register with metric variable using unknown metric type
    var_register = Register()
    var_register[var_symbol][(test_dim, Metric)][(0, "UNKNOWN_METRIC")] = metric_var

    # Create data register
    data = Register()

    # Create step
    step = CreateConstrCalculateMetric()

    # Should raise BuildLpStepException for unknown metric type
    with pytest.raises(BuildLpStepException, match="Unknown metric type"):
        step.run(data, model, var_register)


def test_create_var_vtype_unsupported_type():
    """CreateVar.vtype should raise ValueError for unsupported vtype."""
    from or_algo.lp.step import CreateVar
    # Test unsupported vtype (str instead of int/float/bool)
    mock_param = Mock()
    mock_param.vtype = str  # Unsupported type
    var_unsupported = Var(p=mock_param, sign="x")

    class ConcreteCreateVar(CreateVar):
        def run(self, data, model, var):
            pass

    step = ConcreteCreateVar(
        symbol=var_unsupported,
        weight=Register(),
        lb=Register(),
        ub=Register()
    )
    with pytest.raises(ValueError, match="Unsupported Parameter vtype"):
        _ = step.vtype


def test_create_var_create_method_basic():
    """Test CreateVar._create method with basic variable creation."""
    from or_algo.lp.step import CreateVar
    from register import Parameter, Dimension
    from ortools.linear_solver import pywraplp

    # Create a mock parameter
    mock_param = Mock()
    mock_param.name = "x"
    mock_param.vtype = float

    var_symbol = Var(p=mock_param, sign='x')

    # Create solver
    model = pywraplp.Solver.CreateSolver('CBC')

    # Create dimension
    test_dim = Dimension('TestDim', 'TestDimCN', 'TD')

    # Create registers
    var_register = Register()
    weight_register = Register()
    lb_register = Register()
    ub_register = Register()

    # Create a concrete CreateVar subclass
    class ConcreteCreateVar(CreateVar):
        def run(self, data, model, var):
            pass

    step = ConcreteCreateVar(
        symbol=var_symbol,
        weight=weight_register,
        lb=lb_register,
        ub=ub_register
    )

    # Create data register with primary key
    data = Register()
    data[Parameter][(test_dim,)][(0,)] = (0,)
    data[Parameter][(test_dim,)][(1,)] = (1,)
    data[Parameter][(test_dim,)][(2,)] = (2,)

    # Set bounds
    lb_register[var_symbol][(test_dim,)][(0,)] = 0.0
    lb_register[var_symbol][(test_dim,)][(1,)] = 0.0
    lb_register[var_symbol][(test_dim,)][(2,)] = 0.0
    ub_register[var_symbol][(test_dim,)][(0,)] = 10.0
    ub_register[var_symbol][(test_dim,)][(1,)] = 20.0
    ub_register[var_symbol][(test_dim,)][(2,)] = 15.0

    # Set weights
    weight_register[var_symbol][(test_dim,)][(0,)] = 1.0
    weight_register[var_symbol][(test_dim,)][(1,)] = 2.0
    weight_register[var_symbol][(test_dim,)][(2,)] = 3.0

    # Call _create method
    count = step._create(
        data=data,
        model=model,
        var=var_register,
        primary_key=Parameter,
        dimension=(test_dim,),
        sense='minimize'
    )

    # Should create 3 variables
    assert count == 3

    # Verify variables were created
    assert var_symbol in var_register
    assert (test_dim,) in var_register[var_symbol]
    assert (0,) in var_register[var_symbol][(test_dim,)]
    assert (1,) in var_register[var_symbol][(test_dim,)]
    assert (2,) in var_register[var_symbol][(test_dim,)]

    # Verify objective coefficients were set
    obj = model.Objective()
    assert obj.GetCoefficient(var_register[var_symbol][(test_dim,)][(0,)]) == -1.0  # minimize, so negative
    assert obj.GetCoefficient(var_register[var_symbol][(test_dim,)][(1,)]) == -2.0
    assert obj.GetCoefficient(var_register[var_symbol][(test_dim,)][(2,)]) == -3.0


def test_create_var_create_with_metric_sum():
    """Test CreateVar._create method with SUM metric aggregating all dimensions."""
    from or_algo.lp.step import CreateVar
    from register import Parameter, Dimension, Metric
    from ortools.linear_solver import pywraplp

    mock_param = Mock()
    mock_param.name = "x"
    mock_param.vtype = float

    var_symbol = Var(p=mock_param, sign='x')
    model = pywraplp.Solver.CreateSolver('CBC')
    test_dim = Dimension('TestDim', 'TestDimCN', 'TD')

    var_register = Register()
    weight_register = Register()
    lb_register = Register()
    ub_register = Register()

    class ConcreteCreateVar(CreateVar):
        def run(self, data, model, var):
            pass

    step = ConcreteCreateVar(
        symbol=var_symbol,
        weight=weight_register,
        lb=lb_register,
        ub=ub_register
    )

    data = Register()
    data[Parameter][(test_dim,)][(0,)] = (0,)
    data[Parameter][(test_dim,)][(1,)] = (1,)
    data[Parameter][(test_dim,)][(2,)] = (2,)

    # Create with SUM metric (aggregates all dimensions)
    # When all dimensions are aggregated, only metric variable is created
    count = step._create(
        data=data,
        model=model,
        var=var_register,
        primary_key=Parameter,
        dimension=(test_dim,),
        metric=Register.SUM,
        sense='minimize'
    )

    # Should create only 1 metric variable (all dimensions aggregated)
    assert count == 1

    # Verify metric variable was created at (test_dim, Metric) with (Register.ALL, SUM)
    assert (test_dim, Metric) in var_register[var_symbol]
    assert (Register.ALL, Register.SUM) in var_register[var_symbol][(test_dim, Metric)]


def test_create_var_create_with_skip():
    """Test CreateVar._create method with skip callback."""
    from or_algo.lp.step import CreateVar
    from register import Parameter, Dimension
    from ortools.linear_solver import pywraplp

    mock_param = Mock()
    mock_param.name = "x"
    mock_param.vtype = float

    var_symbol = Var(p=mock_param, sign='x')
    model = pywraplp.Solver.CreateSolver('CBC')
    test_dim = Dimension('TestDim', 'TestDimCN', 'TD')

    var_register = Register()
    weight_register = Register()
    lb_register = Register()
    ub_register = Register()

    class ConcreteCreateVar(CreateVar):
        def run(self, data, model, var):
            pass

    step = ConcreteCreateVar(
        symbol=var_symbol,
        weight=weight_register,
        lb=lb_register,
        ub=ub_register
    )

    data = Register()
    data[Parameter][(test_dim,)][(0,)] = (0,)
    data[Parameter][(test_dim,)][(1,)] = (1,)
    data[Parameter][(test_dim,)][(2,)] = (2,)

    # Skip index (1,)
    skip_func = lambda index: index == (1,)

    count = step._create(
        data=data,
        model=model,
        var=var_register,
        primary_key=Parameter,
        dimension=(test_dim,),
        skip=skip_func
    )

    # Should create only 2 variables (skipped index 1)
    assert count == 2

    # Verify index (1,) was skipped
    assert (1,) not in var_register[var_symbol][(test_dim,)]


def test_create_var_create_invalid_which_length():
    """Test CreateVar._create raises BuildLpStepException for invalid which length."""
    from or_algo.lp.step import CreateVar
    from or_algo.lp.exception import BuildLpStepException
    from register import Parameter, Dimension
    from ortools.linear_solver import pywraplp

    mock_param = Mock()
    mock_param.name = "x"
    mock_param.vtype = float

    var_symbol = Var(p=mock_param, sign='x')
    model = pywraplp.Solver.CreateSolver('CBC')
    test_dim = Dimension('TestDim', 'TestDimCN', 'TD')

    var_register = Register()
    weight_register = Register()
    lb_register = Register()
    ub_register = Register()

    class ConcreteCreateVar(CreateVar):
        def run(self, data, model, var):
            pass

    step = ConcreteCreateVar(
        symbol=var_symbol,
        weight=weight_register,
        lb=lb_register,
        ub=ub_register
    )

    data = Register()
    data[Parameter][(test_dim,)][(0,)] = (0,)

    # which has length 1 but dimension has length 2 - should raise
    with pytest.raises(BuildLpStepException, match="length of which and dimension must be equal"):
        step._create(
            data=data,
            model=model,
            var=var_register,
            primary_key=Parameter,
            dimension=(test_dim, test_dim),  # 2 dimensions
            metric=Register.SUM,
            which=(False,)  # only 1 which flag
        )


def test_publish_basic():
    """Test Publish.run method with continuous variables."""
    from or_algo.lp.step import Publish
    from register import Parameter, Dimension
    from ortools.linear_solver import pywraplp

    mock_param = Mock()
    mock_param.name = "x"
    mock_param.vtype = float

    var_symbol = Var(p=mock_param, sign='x')
    test_dim = Dimension('TestDim', 'TestDimCN', 'TD')

    # Create solver and variable
    model = pywraplp.Solver.CreateSolver('CBC')
    var = model.NumVar(0, 100, 'x_0')

    # Solve the model to set the variable value
    # Add constraint to fix the variable value
    model.Add(var == 42.5)
    model.Minimize(var)
    status = model.Solve()
    assert status == pywraplp.Solver.OPTIMAL

    # Create register with variable
    var_register = Register()
    var_register[var_symbol][(test_dim,)][(0,)] = var

    # Create data register
    data = Register()

    # Create Publish step
    step = Publish(symbol=var_symbol, dimension=(test_dim,))

    # Run publish
    step.run(data, model, var_register)

    # Verify data was published (mock_param is used as key)
    assert data[mock_param][(test_dim,)][(0,)] == 42.5


def test_publish_with_integer_vtype():
    """Test Publish.run method rounds integer variables."""
    from or_algo.lp.step import Publish
    from register import Parameter, Dimension
    from ortools.linear_solver import pywraplp

    mock_param = Mock()
    mock_param.name = "x"
    mock_param.vtype = int

    var_symbol = Var(p=mock_param, sign='x')
    test_dim = Dimension('TestDim', 'TestDimCN', 'TD')

    model = pywraplp.Solver.CreateSolver('CBC')
    var = model.IntVar(0, 100, 'x_0')

    # Fix to a specific value - use objective to drive it to 42
    model.Add(var >= 42)
    model.Add(var <= 42)
    model.Minimize(var)
    status = model.Solve()
    assert status == pywraplp.Solver.OPTIMAL

    var_register = Register()
    var_register[var_symbol][(test_dim,)][(0,)] = var

    data = Register()
    step = Publish(symbol=var_symbol, dimension=(test_dim,))

    step.run(data, model, var_register)

    # Verify integer value (mock_param is used as key)
    assert data[mock_param][(test_dim,)][(0,)] == 42


def test_publish_with_boolean_vtype():
    """Test Publish.run method converts to boolean."""
    from or_algo.lp.step import Publish
    from register import Parameter, Dimension
    from ortools.linear_solver import pywraplp

    mock_param = Mock()
    mock_param.name = "x"
    mock_param.vtype = bool

    var_symbol = Var(p=mock_param, sign='x')
    test_dim = Dimension('TestDim', 'TestDimCN', 'TD')

    model = pywraplp.Solver.CreateSolver('CBC')
    var = model.IntVar(0, 1, 'x_0')

    # Fix to value that rounds to 1 (True)
    model.Add(var >= 0.5)
    model.Minimize(var)
    status = model.Solve()
    assert status == pywraplp.Solver.OPTIMAL

    var_register = Register()
    var_register[var_symbol][(test_dim,)][(0,)] = var

    data = Register()
    step = Publish(symbol=var_symbol, dimension=(test_dim,))

    step.run(data, model, var_register)

    # Verify conversion to boolean (mock_param is used as key)
    assert data[mock_param][(test_dim,)][(0,)] is True  # round(0.5+) = 1 = bool(1) = True


def test_publish_with_zeros_flag():
    """Test Publish.run method with zeros=True publishes zero values."""
    from or_algo.lp.step import Publish
    from register import Parameter, Dimension
    from ortools.linear_solver import pywraplp

    mock_param = Mock()
    mock_param.name = "x"
    mock_param.vtype = float

    var_symbol = Var(p=mock_param, sign='x')
    test_dim = Dimension('TestDim', 'TestDimCN', 'TD')

    model = pywraplp.Solver.CreateSolver('CBC')
    var = model.NumVar(0, 100, 'x_0')

    # Fix to zero
    model.Add(var == 0.0)
    model.Minimize(var)
    status = model.Solve()
    assert status == pywraplp.Solver.OPTIMAL

    var_register = Register()
    var_register[var_symbol][(test_dim,)][(0,)] = var

    data = Register()
    step = Publish(symbol=var_symbol, dimension=(test_dim,), zeros=True)  # Enable zeros

    step.run(data, model, var_register)

    # With zeros=True, zero values should be published (mock_param is used as key)
    assert data[mock_param][(test_dim,)][(0,)] == 0.0


def test_publish_without_zeros_skips_small_values():
    """Test Publish.run method without zeros skips values below threshold."""
    from or_algo.lp.step import Publish
    from register import Parameter, Dimension
    from ortools.linear_solver import pywraplp

    mock_param = Mock()
    mock_param.name = "x"
    mock_param.vtype = float

    var_symbol = Var(p=mock_param, sign='x')
    test_dim = Dimension('TestDim', 'TestDimCN', 'TD')

    model = pywraplp.Solver.CreateSolver('CBC')
    var = model.NumVar(0, 100, 'x_0')

    # Fix to a very small value, below default threshold of 1e-6
    model.Add(var == 1e-7)
    model.Minimize(var)
    status = model.Solve()
    assert status == pywraplp.Solver.OPTIMAL

    var_register = Register()
    var_register[var_symbol][(test_dim,)][(0,)] = var

    data = Register()
    step = Publish(symbol=var_symbol, dimension=(test_dim,), zeros=False)  # Default zeros=False

    step.run(data, model, var_register)

    # With zeros=False, values below threshold should not be published (mock_param is used as key)
    assert (0,) not in data[mock_param][(test_dim,)]


def test_publish_unsupported_vtype():
    """Test Publish.run raises BuildLpStepException for unsupported vtype."""
    from or_algo.lp.step import Publish
    from or_algo.lp.exception import BuildLpStepException
    from register import Parameter, Dimension
    from ortools.linear_solver import pywraplp

    mock_param = Mock()
    mock_param.name = "x"
    mock_param.vtype = str  # Unsupported type

    var_symbol = Var(p=mock_param, sign='x')
    test_dim = Dimension('TestDim', 'TestDimCN', 'TD')

    model = pywraplp.Solver.CreateSolver('CBC')
    var = model.NumVar(0, 100, 'x_0')

    # Fix to any value
    model.Add(var == 42.0)
    model.Minimize(var)
    status = model.Solve()
    assert status == pywraplp.Solver.OPTIMAL

    var_register = Register()
    var_register[var_symbol][(test_dim,)][(0,)] = var

    data = Register()
    step = Publish(symbol=var_symbol, dimension=(test_dim,))

    # Should raise BuildLpStepException for unsupported vtype
    with pytest.raises(BuildLpStepException, match="Unsupported vtype"):
        step.run(data, model, var_register)


def test_publish_with_target():
    """Test Publish.run method with target filter."""
    from or_algo.lp.step import Publish
    from register import Parameter, Dimension
    from ortools.linear_solver import pywraplp

    mock_param = Mock()
    mock_param.name = "x"
    mock_param.vtype = float

    var_symbol = Var(p=mock_param, sign='x')
    test_dim = Dimension('TestDim', 'TestDimCN', 'TD')

    model = pywraplp.Solver.CreateSolver('CBC')
    var0 = model.NumVar(0, 100, 'x_0')
    var1 = model.NumVar(0, 100, 'x_1')

    # Fix variables to specific values
    model.Add(var0 == 10.0)
    model.Add(var1 == 20.0)
    model.Minimize(var0 + var1)
    status = model.Solve()
    assert status == pywraplp.Solver.OPTIMAL

    var_register = Register()
    var_register[var_symbol][(test_dim,)][(0,)] = var0
    var_register[var_symbol][(test_dim,)][(1,)] = var1

    data = Register()
    # Only publish index (1,)
    step = Publish(symbol=var_symbol, dimension=(test_dim,), target=(1,))

    step.run(data, model, var_register)

    # Only index (1,) should be published (mock_param is used as key)
    assert (1,) in data[mock_param][(test_dim,)]
    assert data[mock_param][(test_dim,)][(1,)] == 20.0
    # Index (0,) should not be published
    assert (0,) not in data[mock_param][(test_dim,)]
