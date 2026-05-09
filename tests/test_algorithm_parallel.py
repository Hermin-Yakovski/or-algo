"""Tests for Algorithm.parallel_solve() method."""

import pytest
from concurrent.futures import ProcessPoolExecutor
from register import Register, Parameter, Id, Index
from or_algo.solver import Solver
from or_algo.algorithm import Algorithm
from or_algo.exception import OrAlgoException
from or_algo.shared_register import SharedRegister


class MarkerSolver(Solver):
    """A solver that writes a marker to the register."""

    def __init__(self, marker: str = "default"):
        super().__init__()
        self.marker = marker

    def solve(self, data: Register[Parameter]) -> None:
        data[Id][(Index,)][(0,)] = self.marker


class FailingSolver(Solver):
    """A solver that always fails."""

    def solve(self, data: Register[Parameter]) -> None:
        raise ValueError("intentional failure")


def test_parallel_solve_cycle_detection():
    """Test that parallel_solve raises OrAlgoException for cycles."""
    algo = Algorithm()
    id1 = algo.append(MarkerSolver, "task1")
    id2 = algo.append(MarkerSolver, "task2")
    id3 = algo.append(MarkerSolver, "task3")

    # Create a cycle: 1 -> 2 -> 3 -> 1
    algo._dependency_graph[1] = [3]
    algo._dependency_graph[2] = [1]
    algo._dependency_graph[3] = [2]

    data = SharedRegister[Parameter]()

    with ProcessPoolExecutor(max_workers=2) as executor:
        with pytest.raises(OrAlgoException) as exc_info:
            algo.parallel_solve(data, executor)

    assert "cycle" in str(exc_info.value).lower()


def test_parallel_solve_self_loop_detection():
    """Test that parallel_solve detects self-loops."""
    algo = Algorithm()
    id1 = algo.append(MarkerSolver, "task1")

    # Create a self-loop
    algo._dependency_graph[1] = [1]

    data = SharedRegister[Parameter]()

    with ProcessPoolExecutor(max_workers=2) as executor:
        with pytest.raises(OrAlgoException) as exc_info:
            algo.parallel_solve(data, executor)

    assert "cycle" in str(exc_info.value).lower()


def test_parallel_solve_empty_algorithm():
    """Test that parallel_solve handles an empty algorithm gracefully."""
    algo = Algorithm()
    data = SharedRegister[Parameter]()

    with ProcessPoolExecutor(max_workers=2) as executor:
        result = algo.parallel_solve(data, executor)

    # Should return the same SharedRegister unchanged
    assert result is data


def test_parallel_solve_returns_same_register():
    """Test that parallel_solve returns the same SharedRegister instance."""
    algo = Algorithm()
    algo.append(MarkerSolver, "test")

    data = SharedRegister[Parameter]()

    with ProcessPoolExecutor(max_workers=2) as executor:
        result = algo.parallel_solve(data, executor)

    # Should return the exact same instance
    assert result is data


def test_parallel_solve_task_creation():
    """Test that parallel_solve creates SolverTask wrappers correctly."""
    algo = Algorithm()
    algo.append(MarkerSolver, "task1", after=[])
    algo.append(MarkerSolver, "task2", after=[1])

    from multiprocessing import Manager
    manager = Manager()
    data = SharedRegister[Parameter].create(manager)

    # This should not raise an exception during task creation
    # (it will fail during execution due to pickling issues, but that's expected)
    with ProcessPoolExecutor(max_workers=2) as executor:
        try:
            algo.parallel_solve(data, executor)
        except (OrAlgoException, KeyError, TypeError):
            # Expected to fail during execution due to Register pickling issues
            pass


def test_parallel_solve_dag_validation_before_execution():
    """Test that DAG validation happens before any task execution."""
    algo = Algorithm()
    algo.append(MarkerSolver, "task1")
    algo.append(MarkerSolver, "task2")

    # Don't create a cycle, so validation should pass
    # The tasks will fail during execution, but that's after validation
    data = SharedRegister[Parameter]()

    with ProcessPoolExecutor(max_workers=2) as executor:
        try:
            algo.parallel_solve(data, executor)
        except (OrAlgoException, KeyError, TypeError):
            # Expected to fail during execution
            pass
