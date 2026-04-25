"""Tests for or_algo.solver module."""

import pytest
from register import Register, Parameter, Id, Index
from or_algo.solver import Solver


def test_solver_cannot_be_instantiated_directly():
    """Test that Solver cannot be instantiated directly because it's abstract."""
    with pytest.raises(TypeError):
        Solver()


def test_solver_default_name():
    """Test that Solver uses class name as default name."""
    class MockSolver(Solver):
        def solve(self, data: Register[Parameter]) -> None:
            pass

    solver = MockSolver()
    assert solver.name == "MockSolver"


def test_solver_custom_name():
    """Test that Solver accepts custom name."""
    class MockSolver(Solver):
        def solve(self, data: Register[Parameter]) -> None:
            pass

    solver = MockSolver(name="CustomName")
    assert solver.name == "CustomName"


def test_solver_solve_requires_implementation():
    """Test that subclasses must implement solve()."""
    class IncompleteSolver(Solver):
        pass

    # Cannot instantiate without implementing solve()
    with pytest.raises(TypeError):
        IncompleteSolver()


def test_solver_solve_can_be_called():
    """Test that a properly implemented Solver can call solve()."""
    class WorkingSolver(Solver):
        def solve(self, data: Register[Parameter]) -> None:
            # Store a marker to verify solve was called
            data[Id][(Index,)][(0,)] = "solved"

    solver = WorkingSolver()
    register = Register[Parameter]()
    solver.solve(register)

    # Verify solve was executed
    assert (Index,) in register[Id]
    assert (0,) in register[Id][(Index,)]
    assert register[Id][(Index,)][(0,)] == "solved"
