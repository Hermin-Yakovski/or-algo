"""Tests for or_algo.solver module."""

import pytest
from register import Register, Parameter, Id, Index
from or_algo.solver import Solver


@pytest.fixture
def empty_register() -> Register[Parameter]:
    """Provide an empty Register for testing."""
    return Register[Parameter]()


def test_solver_cannot_be_instantiated_directly():
    """Test that Solver cannot be instantiated directly because it's abstract."""
    with pytest.raises(TypeError):
        Solver()


def test_solver_default_name():
    """Test that Solver uses class name as default name."""
    class MockSolver(Solver):
        def solve(self, data: Register[Parameter]) -> Register[Parameter]:
            return data

    solver = MockSolver()
    assert solver.name == "MockSolver"


def test_solver_custom_name():
    """Test that Solver accepts custom name."""
    class MockSolver(Solver):
        def solve(self, data: Register[Parameter]) -> Register[Parameter]:
            return data

    solver = MockSolver(name="CustomName")
    assert solver.name == "CustomName"


def test_solver_solve_requires_implementation():
    """Test that subclasses must implement solve()."""
    class IncompleteSolver(Solver):
        pass

    # Cannot instantiate without implementing solve()
    with pytest.raises(TypeError):
        IncompleteSolver()


def test_solver_solve_can_be_called(empty_register):
    """Test that a properly implemented Solver can call solve()."""
    class WorkingSolver(Solver):
        def solve(self, data: Register[Parameter]) -> Register[Parameter]:
            # Store a marker to verify solve was called
            data[Id][(Index,)][(0,)] = "solved"
            return data

    solver = WorkingSolver()
    result = solver.solve(empty_register)

    # Verify solve was executed
    assert (Index,) in empty_register[Id]
    assert (0,) in empty_register[Id][(Index,)]
    assert empty_register[Id][(Index,)][(0,)] == "solved"
    # Verify the returned var is the same as input
    assert result is empty_register
