import pytest
from or_algo.lp.solver import LpSolver
from or_algo import Solver


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
    from or_algo.lp import Symbol

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
