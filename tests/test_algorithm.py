"""Tests for or_algo.algorithm module."""

import pytest
from register import Register, RegisterKey, Id, Index
from or_algo.solver import Solver
from or_algo.algorithm import Algorithm
from or_algo.exception import OrAlgoException
from or_algo.task import SolverTask


class SuccessSolver(Solver):
    """A solver that always succeeds."""

    def __init__(self, marker: str = "default"):
        super().__init__()
        self.marker = marker
        self.called = False

    def solve(self, data: Register[RegisterKey]) -> None:
        self.called = True
        data[Id][(Index,)][(0,)] = self.marker


class FailingSolver(Solver):
    """A solver that always fails."""

    def solve(self, data: Register[RegisterKey]) -> None:
        raise ValueError("intentional failure")


def test_algorithm_initialization():
    """Test that Algorithm can be initialized."""
    algo = Algorithm()
    assert algo is not None


def test_algorithm_append_returns_one_based_index():
    """Test that append() returns 1-based index."""
    algo = Algorithm()
    idx1 = algo.append(SuccessSolver)
    idx2 = algo.append(SuccessSolver)
    assert idx1 == 1
    assert idx2 == 2


def test_algorithm_solve_executes_solvers_in_order():
    """Test that solve() executes solvers in the order they were appended."""
    execution_order = []

    class OrderSolver(Solver):
        def __init__(self, marker: str):
            super().__init__()
            self.marker = marker

        def solve(self, data: Register[RegisterKey]) -> None:
            execution_order.append(self.marker)

    algo = Algorithm()
    algo.append(OrderSolver, "first")
    algo.append(OrderSolver, "second")
    algo.append(OrderSolver, "third")

    algo.solve(Register())
    assert execution_order == ["first", "second", "third"]


def test_algorithm_solve_stops_on_first_failure():
    """Test that solve() stops and raises on first solver failure."""
    execution_order = []

    class TrackingSolver(Solver):
        def __init__(self, marker: str):
            super().__init__()
            self.marker = marker

        def solve(self, data: Register[RegisterKey]) -> None:
            execution_order.append(self.marker)
            if self.marker == "fail":
                raise ValueError("intentional failure")

    algo = Algorithm()
    algo.append(TrackingSolver, "first")
    algo.append(TrackingSolver, "fail")
    algo.append(TrackingSolver, "never_reached")

    with pytest.raises(OrAlgoException) as exc_info:
        algo.solve(Register())

    # Verify execution stopped at failure
    assert execution_order == ["first", "fail"]

    # Verify original exception is chained
    assert isinstance(exc_info.value.__cause__, ValueError)
    assert "intentional failure" in str(exc_info.value.__cause__)


def test_algorithm_solve_with_solver_args():
    """Test that solver positional args are passed correctly."""
    class ConfiguredSolver(Solver):
        def __init__(self, value: int):
            super().__init__()
            self.value = value

        def solve(self, data: Register[RegisterKey]) -> None:
            data[Id][(Index,)][(0,)] = f"value={self.value}"

    algo = Algorithm()
    algo.append(ConfiguredSolver, 42)

    register = Register()
    algo.solve(register)

    assert register[Id][(Index,)][(0,)] == "value=42"


def test_algorithm_solve_with_solver_kwargs():
    """Test that solver keyword args are passed correctly."""
    class ConfiguredSolver(Solver):
        def __init__(self, value: int, flag: bool = False):
            super().__init__()
            self.value = value
            self.flag = flag

        def solve(self, data: Register[RegisterKey]) -> None:
            data[Id][(Index,)][(0,)] = f"value={self.value},flag={self.flag}"

    algo = Algorithm()
    algo.append(ConfiguredSolver, 42, flag=True)

    register = Register()
    algo.solve(register)

    assert register[Id][(Index,)][(0,)] == "value=42,flag=True"


def test_algorithm_solve_with_both_args_and_kwargs():
    """Test that both args and kwargs are passed correctly."""
    class ConfiguredSolver(Solver):
        def __init__(self, a: int, b: str, c: bool = False):
            super().__init__()
            self.a = a
            self.b = b
            self.c = c

        def solve(self, data: Register[RegisterKey]) -> None:
            data[Id][(Index,)][(0,)] = f"a={self.a},b={self.b},c={self.c}"

    algo = Algorithm()
    algo.append(ConfiguredSolver, 1, "two", c=True)

    register = Register()
    algo.solve(register)

    assert register[Id][(Index,)][(0,)] == "a=1,b=two,c=True"


def test_algorithm_exception_message():
    """Test that OrAlgoException includes useful information."""
    algo = Algorithm()
    algo.append(FailingSolver)

    with pytest.raises(OrAlgoException) as exc_info:
        algo.solve(Register())

    assert "FailingSolver" in str(exc_info.value)
    assert "solve()" in str(exc_info.value)


def test_algorithm_dependency_graph_no_dependencies():
    """Test that dependency graph tracks solvers with no dependencies."""
    algo = Algorithm()
    solver_id = algo.append(SuccessSolver)

    assert solver_id == 1
    assert algo._dependency_graph[1] == []


def test_algorithm_dependency_graph_with_dependencies():
    """Test that dependency graph tracks solvers with dependencies."""
    algo = Algorithm()
    solver_id_1 = algo.append(SuccessSolver)
    solver_id_2 = algo.append(SuccessSolver, after=[solver_id_1])
    solver_id_3 = algo.append(SuccessSolver, after=[solver_id_1, solver_id_2])

    # Verify solver IDs
    assert solver_id_1 == 1
    assert solver_id_2 == 2
    assert solver_id_3 == 3

    # Verify dependency graph
    assert algo._dependency_graph[1] == []
    assert algo._dependency_graph[2] == [1]
    assert algo._dependency_graph[3] == [1, 2]


def test_algorithm_detect_cycle_no_cycle():
    """Test that _detect_cycle() returns False for a DAG."""
    algo = Algorithm()
    id1 = algo.append(SuccessSolver)
    id2 = algo.append(SuccessSolver, after=[id1])
    id3 = algo.append(SuccessSolver, after=[id1])

    assert algo._detect_cycle() is False


def test_algorithm_detect_cycle_self_loop():
    """Test that _detect_cycle() returns True for a self-loop."""
    algo = Algorithm()
    id1 = algo.append(SuccessSolver)
    # Create a self-loop: task 1 depends on itself
    algo._dependency_graph[1] = [1]

    assert algo._detect_cycle() is True


def test_algorithm_detect_cycle_complex_cycle():
    """Test that _detect_cycle() returns True for a complex cycle."""
    algo = Algorithm()
    id1 = algo.append(SuccessSolver)
    id2 = algo.append(SuccessSolver)
    id3 = algo.append(SuccessSolver)

    # Create a cycle: 1 -> 2 -> 3 -> 1
    algo._dependency_graph[1] = [3]
    algo._dependency_graph[2] = [1]
    algo._dependency_graph[3] = [2]

    assert algo._detect_cycle() is True


def test_algorithm_detect_cycle_partial_cycle():
    """Test that _detect_cycle() returns True when cycle exists in part of graph."""
    algo = Algorithm()
    id1 = algo.append(SuccessSolver)
    id2 = algo.append(SuccessSolver)
    id3 = algo.append(SuccessSolver)
    id4 = algo.append(SuccessSolver)

    # Create a cycle between 2 and 3, but 1 and 4 are independent
    algo._dependency_graph[1] = []
    algo._dependency_graph[2] = [3]
    algo._dependency_graph[3] = [2]
    algo._dependency_graph[4] = []

    assert algo._detect_cycle() is True


def test_algorithm_get_ready_tasks_initially():
    """Test that tasks with no dependencies are ready initially."""
    algo = Algorithm()

    # Create tasks: 1 and 2 have no dependencies, 3 depends on 1 and 2
    task1 = SolverTask(SuccessSolver, (), {}, [], 1)
    task2 = SolverTask(SuccessSolver, (), {}, [], 2)
    task3 = SolverTask(SuccessSolver, (), {}, [1, 2], 3)

    tasks = {1: task1, 2: task2, 3: task3}
    completed = set()

    ready = algo._get_ready_tasks(tasks, completed)

    # Only tasks 1 and 2 should be ready (no dependencies)
    assert sorted(ready) == [1, 2]


def test_algorithm_get_ready_tasks_after_completion():
    """Test that dependent tasks become ready after dependencies complete."""
    algo = Algorithm()

    # Create tasks: 1 and 2 have no dependencies, 3 depends on 1 and 2
    task1 = SolverTask(SuccessSolver, (), {}, [], 1)
    task2 = SolverTask(SuccessSolver, (), {}, [], 2)
    task3 = SolverTask(SuccessSolver, (), {}, [1, 2], 3)

    tasks = {1: task1, 2: task2, 3: task3}

    # After task 1 completes (mark it as completed)
    task1.state = "completed"
    completed = {1}
    ready = algo._get_ready_tasks(tasks, completed)

    # Only task 2 should be ready (task 3 still needs task 2)
    assert sorted(ready) == [2]


def test_algorithm_get_ready_tasks_after_both_dependencies_complete():
    """Test that task dependent on both becomes ready after both complete."""
    algo = Algorithm()

    # Create tasks: 1 and 2 have no dependencies, 3 depends on 1 and 2
    task1 = SolverTask(SuccessSolver, (), {}, [], 1)
    task2 = SolverTask(SuccessSolver, (), {}, [], 2)
    task3 = SolverTask(SuccessSolver, (), {}, [1, 2], 3)

    tasks = {1: task1, 2: task2, 3: task3}

    # After tasks 1 and 2 complete (mark them as completed)
    task1.state = "completed"
    task2.state = "completed"
    completed = {1, 2}
    ready = algo._get_ready_tasks(tasks, completed)

    # Task 3 should now be ready
    assert sorted(ready) == [3]


def test_algorithm_get_ready_tasks_ignores_non_pending_tasks():
    """Test that _get_ready_tasks ignores tasks that are not pending."""
    algo = Algorithm()

    # Create tasks with different states
    task1 = SolverTask(SuccessSolver, (), {}, [], 1)
    task2 = SolverTask(SuccessSolver, (), {}, [], 2)
    task3 = SolverTask(SuccessSolver, (), {}, [], 3)

    # Change states
    task1.state = "running"
    task2.state = "completed"
    task3.state = "pending"

    tasks = {1: task1, 2: task2, 3: task3}
    completed = set()

    ready = algo._get_ready_tasks(tasks, completed)

    # Only task 3 should be ready (only pending task)
    assert sorted(ready) == [3]


def test_algorithm_get_ready_tasks_empty_when_all_completed():
    """Test that _get_ready_tasks returns empty list when all tasks completed."""
    algo = Algorithm()

    # Create tasks
    task1 = SolverTask(SuccessSolver, (), {}, [], 1)
    task2 = SolverTask(SuccessSolver, (), {}, [], 2)

    tasks = {1: task1, 2: task2}

    # Mark all as completed
    task1.state = "completed"
    task2.state = "completed"

    completed = {1, 2}
    ready = algo._get_ready_tasks(tasks, completed)

    # No ready tasks
    assert sorted(ready) == []


def test_algorithm_get_ready_tasks_partial_dependencies():
    """Test that task with partial dependencies is not ready."""
    algo = Algorithm()

    # Create tasks: 1, 2, 3 no dependencies, 4 depends on 1, 2, 3
    task1 = SolverTask(SuccessSolver, (), {}, [], 1)
    task2 = SolverTask(SuccessSolver, (), {}, [], 2)
    task3 = SolverTask(SuccessSolver, (), {}, [], 3)
    task4 = SolverTask(SuccessSolver, (), {}, [1, 2, 3], 4)

    tasks = {1: task1, 2: task2, 3: task3, 4: task4}

    # After tasks 1 and 2 complete (but not 3) - mark them as completed
    task1.state = "completed"
    task2.state = "completed"
    completed = {1, 2}
    ready = algo._get_ready_tasks(tasks, completed)

    # Task 3 should be ready (no deps), but not task 4 (missing dep 3)
    assert sorted(ready) == [3]


def test_algorithm_merge_register():
    """Test that _merge_register() merges source into target."""
    algo = Algorithm()

    # Create source and target registers
    target = Register[RegisterKey]()
    target[Id][(Index,)][(0,)] = "target_value"

    source = Register[RegisterKey]()
    source[Id][(Index,)][(1,)] = "source_value"
    source[Id][(Index,)][(0,)] = "overwrite_value"

    # Merge source into target
    algo._merge_register(target, source)

    # Target should have both values, with source overwriting
    assert target[Id][(Index,)][(0,)] == "overwrite_value"
    assert target[Id][(Index,)][(1,)] == "source_value"
