"""Tests for or_algo.solver module."""

import pytest
from register import Register, RegisterKey, Id, Index
from or_algo.solver import Solver


@pytest.fixture
def empty_register() -> Register[RegisterKey]:
    """Provide an empty Register for testing."""
    return Register()


def test_solver_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        Solver()


def test_solver_default_name():
    class MockSolver(Solver):
        def solve(self, data: Register[RegisterKey]) -> Register[RegisterKey]:
            return data
    solver = MockSolver()
    assert solver.name == "MockSolver"


def test_solver_custom_name():
    class MockSolver(Solver):
        def solve(self, data: Register[RegisterKey]) -> Register[RegisterKey]:
            return data
    solver = MockSolver(name="CustomName")
    assert solver.name == "CustomName"


def test_solver_solve_requires_implementation():
    class IncompleteSolver(Solver):
        pass
    with pytest.raises(TypeError):
        IncompleteSolver()


def test_solver_solve_can_be_called(empty_register):
    class WorkingSolver(Solver):
        def solve(self, data: Register[RegisterKey]) -> Register[RegisterKey]:
            data[Id][(Index,)][(0,)] = "solved"
            return data

    solver = WorkingSolver()
    result = solver.solve(empty_register)

    assert (Index,) in empty_register[Id]
    assert (0,) in empty_register[Id][(Index,)]
    assert empty_register[Id][(Index,)][(0,)] == "solved"
    assert result is empty_register
