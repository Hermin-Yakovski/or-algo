"""Tests for SolverTask class."""

import pytest
from or_algo.task import SolverTask
from or_algo.solver import Solver
from register import Register, Parameter


class DummySolver(Solver):
    """Test solver that returns data unchanged."""

    def solve(self, data: Register[Parameter]) -> Register[Parameter]:
        return data


def test_solver_task_initialization():
    """Test SolverTask initialization with all parameters."""
    task = SolverTask(
        solver_type=DummySolver,
        args=(),
        kwargs={},
        dependencies=[1, 2],
        task_id=3
    )
    assert task.solver_type == DummySolver
    assert task.dependencies == [1, 2]
    assert task.task_id == 3
    assert task.state == "pending"
    assert task.exception is None


def test_solver_task_state_transitions():
    """Test state transitions from pending to running to completed."""
    task = SolverTask(DummySolver, (), {}, [], 1)
    assert task.state == "pending"

    task.mark_running()
    assert task.state == "running"

    task.mark_completed()
    assert task.state == "completed"


def test_solver_task_failure_state():
    """Test state transition to failed with exception."""
    task = SolverTask(DummySolver, (), {}, [], 1)
    exc = ValueError("test error")
    task.mark_failed(exc)
    assert task.state == "failed"
    assert task.exception == exc


def test_solver_task_execute_success():
    """Test execute() method with successful solver."""
    task = SolverTask(DummySolver, (), {}, [], 1)
    data = Register[Parameter]()
    task.execute(data)
    assert task.state == "completed"


def test_solver_task_execute_failure():
    """Test execute() method with failing solver."""

    class FailingSolver(Solver):
        def solve(self, data: Register[Parameter]) -> Register[Parameter]:
            raise ValueError("solver failed")

    task = SolverTask(FailingSolver, (), {}, [], 1)
    data = Register[Parameter]()
    with pytest.raises(ValueError, match="solver failed"):
        task.execute(data)
    assert task.state == "failed"
    assert isinstance(task.exception, ValueError)
