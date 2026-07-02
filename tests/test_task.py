"""Tests for SolverTask class."""

import pytest
from or_algo.task import SolverTask
from or_algo.solver import Solver
from register import Register, RegisterKey


class DummySolver(Solver):
    def solve(self, data: Register[RegisterKey]) -> Register[RegisterKey]:
        return data


def test_solver_task_initialization():
    task = SolverTask(
        solver_type=DummySolver, args=(), kwargs={},
        dependencies=[1, 2], task_id=3
    )
    assert task.solver_type == DummySolver
    assert task.dependencies == [1, 2]
    assert task.task_id == 3
    assert task.state == "pending"
    assert task.exception is None


def test_solver_task_state_transitions():
    task = SolverTask(DummySolver, (), {}, [], 1)
    assert task.state == "pending"
    task.mark_running()
    assert task.state == "running"
    task.mark_completed()
    assert task.state == "completed"


def test_solver_task_failure_state():
    task = SolverTask(DummySolver, (), {}, [], 1)
    exc = ValueError("test error")
    task.mark_failed(exc)
    assert task.state == "failed"
    assert task.exception == exc


def test_solver_task_execute_success():
    task = SolverTask(DummySolver, (), {}, [], 1)
    data = Register()
    task.execute(data)
    assert task.state == "completed"


def test_solver_task_execute_failure():
    class FailingSolver(Solver):
        def solve(self, data: Register[RegisterKey]) -> Register[RegisterKey]:
            raise ValueError("solver failed")

    task = SolverTask(FailingSolver, (), {}, [], 1)
    data = Register()
    with pytest.raises(ValueError, match="solver failed"):
        task.execute(data)
    assert task.state == "failed"
    assert isinstance(task.exception, ValueError)


def test_solver_task_execute_returns_register():
    task = SolverTask(DummySolver, (), {}, [], 1)
    reg = Register()
    reg._data["test"] = "input"
    result_reg = task.execute(reg)
    assert result_reg is reg
    assert isinstance(result_reg, Register)
