"""Tests for LpSolver."""

import pytest
from or_algo.lp.solver import LpSolver
from or_algo import Solver
from or_algo.lp.step import CreateVar, CreateConstr
from or_algo.lp.symbol import VarKey, ConstrKey
from or_register import Register, Dimension


def test_lp_solver_is_solver():
    assert issubclass(LpSolver, Solver)


def test_lp_solver_initialization():
    solver = LpSolver(name="test_solver")
    assert solver._name == "test_solver"
    assert solver.solver_type == 'SCIP'
    assert solver._model is not None
    assert isinstance(solver._var, Register)


def test_lp_solver_custom_solver_type():
    solver = LpSolver(name="test_solver", solver_type='GLOP')
    assert solver.solver_type == 'GLOP'


def test_lp_solver_invalid_solver_type():
    with pytest.raises(Exception):
        LpSolver(name="test_solver", solver_type='INVALID_SOLVER')


def test_lp_solver_no_weight_lb_ub():
    solver = LpSolver(name="test_solver")
    assert not hasattr(solver, '_weight')
    assert not hasattr(solver, '_lb')
    assert not hasattr(solver, '_ub')


def test_lp_solver_append_create_var():
    solver = LpSolver(name="test_solver")
    vk = VarKey(id=1, name='X', name_cn='x', sign='x')

    class TestCreateVar(CreateVar):
        def run(self, data, model, var):
            pass

    initial_count = len(solver._build_steps)
    solver.append(TestCreateVar, vk)
    assert len(solver._build_steps) == initial_count + 1


def test_lp_solver_append_create_constr():
    solver = LpSolver(name="test_solver")
    ck = ConstrKey(id=1, name='C', name_cn='c', sign='c')

    class TestCreateConstr(CreateConstr):
        def run(self, data, model, var):
            pass

    initial_count = len(solver._build_steps)
    solver.append(TestCreateConstr, ck)
    assert len(solver._build_steps) == initial_count + 1


def test_lp_solver_append_rejects_unknown_step():
    from or_algo.lp.step import LpStep
    solver = LpSolver(name="test_solver")

    class UnknownStep(LpStep):
        def run(self, data, model, var):
            pass

    with pytest.raises(Exception):
        solver.append(UnknownStep)


def test_lp_solver_solve_executes_steps():
    solver = LpSolver(name="test_solver_exec")
    executed = []

    class TrackingCreateVar(CreateVar):
        def run(self, data, model, var):
            executed.append('create_var')

    vk = VarKey(id=1, name='X', name_cn='x', sign='x')
    solver.append(TrackingCreateVar, vk)

    data = Register()
    solver.solve(data)
    assert executed == ['create_var']


def test_lp_solver_solve_returns_data():
    solver = LpSolver(name="test_solver_ret")
    vk = VarKey(id=1, name='X', name_cn='x', sign='x')

    class SimpleCreateVar(CreateVar):
        def run(self, data, model, var):
            d = Dimension('I', 'i', 'I')
            v = model.NumVar(0, 1, 'x')
            var[self._symbol][d,][0,] = v
            model.Objective().SetCoefficient(v, 1)

    solver.append(SimpleCreateVar, vk)
    data = Register()
    result = solver.solve(data)
    assert result is data


def test_lp_solver_append_no_default_args():
    solver = LpSolver(name="test_solver_args")
    vk = VarKey(id=1, name='X', name_cn='x', sign='x')

    class TestCreateVar(CreateVar):
        def run(self, data, model, var):
            pass

    solver.append(TestCreateVar, vk)
    step_type, args, kwargs = solver._build_steps[-1]
    assert args == (vk,)
