import pytest
from or_algo.lp.solver import LpSolver
from or_algo import Solver
from or_algo.lp.step import CreateVar, CreateConstr
from or_algo.lp.symbol import Var, Constr
from register import Register
from unittest.mock import Mock
from ortools.linear_solver import pywraplp


def test_lp_solver_is_solver():
    """LpSolver should inherit from or-algo's Solver."""
    assert issubclass(LpSolver, Solver)


def test_lp_solver_initialization():
    """LpSolver should initialize with required parameters."""
    solver = LpSolver(name="test_solver")
    assert solver._name == "test_solver"
    assert solver.solver_type == 'CBC'
    assert solver._model is not None


def test_lp_solver_custom_solver_type():
    """LpSolver should accept custom solver_type."""
    solver = LpSolver(name="test_solver", solver_type='GLOP')
    assert solver.solver_type == 'GLOP'


def test_lp_solver_invalid_solver_type():
    """LpSolver should handle invalid solver_type gracefully."""
    # OR-Tools returns None for invalid solver types
    with pytest.raises(Exception):  # LpSolverException
        LpSolver(name="test_solver", solver_type='INVALID_SOLVER')


def test_lp_solver_has_weight_lb_ub_defaults():
    """LpSolver should create default Register for weight, lb, ub."""
    from register import Register
    solver = LpSolver(name="test_solver")
    assert isinstance(solver._weight, Register)
    assert isinstance(solver._lb, Register)
    assert isinstance(solver._ub, Register)
    assert isinstance(solver._var, Register)


def test_lp_solver_custom_weight_lb_ub():
    """LpSolver should accept custom weight, lb, ub Registers."""
    from register import Register

    weight = Register()
    lb = Register()
    ub = Register()

    solver = LpSolver(name="test_solver", weight=weight, lb=lb, ub=ub)
    assert solver._weight is weight
    assert solver._lb is lb
    assert solver._ub is ub


def test_lp_solver_append_create_var():
    """LpSolver.append() should accept CreateVar steps."""
    solver = LpSolver(name="test_solver")

    mock_param = Mock()
    mock_param.name = "x"
    mock_param.name_cn = "x变量"
    mock_param.id = 1
    mock_param.vtype = float
    var_symbol = Var(p=mock_param, sign="x")

    class TestCreateVar(CreateVar):
        def run(self, data, model, var):
            pass

    initial_count = len(solver._build_steps)
    solver.append(TestCreateVar, var_symbol)
    assert len(solver._build_steps) == initial_count + 1


def test_lp_solver_append_create_var_auto_fills_args():
    """LpSolver.append() should auto-fill weight, lb, ub for CreateVar."""
    solver = LpSolver(name="test_solver")

    mock_param = Mock()
    mock_param.name = "x"
    mock_param.name_cn = "x变量"
    mock_param.id = 1
    mock_param.vtype = float
    var_symbol = Var(p=mock_param, sign="x")

    class TestCreateVar(CreateVar):
        def __init__(self, symbol, weight, lb, ub, custom_arg=None):
            super().__init__(symbol, weight, lb, ub)
            self.custom_arg = custom_arg

        def run(self, data, model, var):
            pass

    # Pass only symbol and custom_arg - weight, lb, ub should be auto-filled
    solver.append(TestCreateVar, var_symbol, custom_arg="test")
    step_type, args, kwargs = solver._build_steps[-1]

    assert args[0] is var_symbol  # symbol
    assert args[1] is solver._weight  # weight
    assert args[2] is solver._lb  # lb
    assert args[3] is solver._ub  # ub
    assert kwargs['custom_arg'] == "test"


def test_lp_solver_append_create_constr():
    """LpSolver.append() should accept CreateConstr steps."""
    solver = LpSolver(name="test_solver")

    constr_symbol = Constr(name="limit", name_cn="限制", sign="L")

    class TestCreateConstr(CreateConstr):
        def run(self, data, model, var):
            pass

    initial_count = len(solver._build_steps)
    solver.append(TestCreateConstr, constr_symbol)
    assert len(solver._build_steps) == initial_count + 1


def test_lp_solver_append_invalid_step_type():
    """LpSolver.append() should raise exception for unsupported step types."""
    solver = LpSolver(name="test_solver")

    class InvalidStep:
        pass

    with pytest.raises(Exception):  # LpSolverException
        solver.append(InvalidStep)


def test_lp_solver_solve_executes_build_steps():
    """LpSolver.solve() should execute build steps in order."""
    from unittest.mock import Mock

    solver = LpSolver(name="test_solver")

    # Mock the steps
    executed_steps = []

    class Step1(CreateVar):
        def run(self, data, model, var):
            executed_steps.append('step1')

    class Step2(CreateConstr):
        def run(self, data, model, var):
            executed_steps.append('step2')

    mock_param = Mock()
    mock_param.name = "x"
    mock_param.name_cn = "x变量"
    mock_param.id = 1
    mock_param.vtype = float
    var_symbol = Var(p=mock_param, sign="x")
    constr_symbol = Constr(name="limit", name_cn="限制", sign="L")

    solver.append(Step1, var_symbol)
    solver.append(Step2, constr_symbol)

    # Create mock data var
    data = Register()

    # Mock the model.optimize() to return OPTIMAL
    solver._model.Solve = Mock(return_value=pywraplp.Solver.OPTIMAL)

    # Solve
    result = solver.solve(data)

    assert executed_steps == ['step1', 'step2']
    assert result is data  # Should return the same var


def test_lp_solver_solve_build_step_exception():
    """LpSolver.solve() should wrap build step exceptions."""
    class FailingStep(CreateVar):
        def run(self, data, model, var):
            raise ValueError("Step failed!")

    solver = LpSolver(name="test_solver")

    mock_param = Mock()
    mock_param.name = "x"
    mock_param.name_cn = "x变量"
    mock_param.id = 1
    mock_param.vtype = float
    var_symbol = Var(p=mock_param, sign="x")

    solver.append(FailingStep, var_symbol)

    data = Register()

    # Mock the model.optimize() to return OPTIMAL (won't be reached)
    solver._model.Solve = Mock(return_value=pywraplp.Solver.OPTIMAL)

    # Should raise BuildLpStepException
    with pytest.raises(Exception):  # BuildLpStepException
        solver.solve(data)


def test_lp_solver_solve_optimal_status():
    """LpSolver.solve() should handle OPTIMAL status."""
    solver = LpSolver(name="test_solver")
    data = Register()

    solver._model.Solve = Mock(return_value=pywraplp.Solver.OPTIMAL)

    # Should not raise, should return data
    result = solver.solve(data)
    assert result is data


def test_lp_solver_solve_infeasible_status():
    """LpSolver.solve() should raise exception for INFEASIBLE status."""
    solver = LpSolver(name="test_solver")
    data = Register()

    solver._model.Solve = Mock(return_value=pywraplp.Solver.INFEASIBLE)

    with pytest.raises(Exception):  # LpModelOptimizeException
        solver.solve(data)


def test_lp_solver_solve_unbounded_status():
    """LpSolver.solve() should raise exception for UNBOUNDED status."""
    solver = LpSolver(name="test_solver")
    data = Register()

    solver._model.Solve = Mock(return_value=pywraplp.Solver.UNBOUNDED)

    with pytest.raises(Exception):  # LpModelOptimizeException
        solver.solve(data)


def test_lp_solver_solve_not_solved_status():
    """LpSolver.solve() should raise exception for NOT_SOLVED status."""
    solver = LpSolver(name="test_solver")
    data = Register()

    solver._model.Solve = Mock(return_value=pywraplp.Solver.NOT_SOLVED)

    with pytest.raises(Exception):  # LpModelOptimizeException
        solver.solve(data)


def test_lp_solver_solve_abnormal_status():
    """LpSolver.solve() should raise exception for ABNORMAL status."""
    solver = LpSolver(name="test_solver")
    data = Register()

    solver._model.Solve = Mock(return_value=pywraplp.Solver.ABNORMAL)

    with pytest.raises(Exception):  # LpModelOptimizeException
        solver.solve(data)
