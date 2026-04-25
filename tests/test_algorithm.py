"""Tests for or_algo.algorithm module."""

import pytest
from register import Register, Parameter, Id, Index
from or_algo.solver import Solver
from or_algo.algorithm import Algorithm
from or_algo.exception import OrAlgoException


class SuccessSolver(Solver):
    """A solver that always succeeds."""

    def __init__(self, marker: str = "default"):
        super().__init__()
        self.marker = marker
        self.called = False

    def solve(self, data: Register[Parameter]) -> None:
        self.called = True
        data[Id][(Index,)][(0,)] = self.marker


class FailingSolver(Solver):
    """A solver that always fails."""

    def solve(self, data: Register[Parameter]) -> None:
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

        def solve(self, data: Register[Parameter]) -> None:
            execution_order.append(self.marker)

    algo = Algorithm()
    algo.append(OrderSolver, "first")
    algo.append(OrderSolver, "second")
    algo.append(OrderSolver, "third")

    algo.solve(Register[Parameter]())
    assert execution_order == ["first", "second", "third"]


def test_algorithm_solve_stops_on_first_failure():
    """Test that solve() stops and raises on first solver failure."""
    execution_order = []

    class TrackingSolver(Solver):
        def __init__(self, marker: str):
            super().__init__()
            self.marker = marker

        def solve(self, data: Register[Parameter]) -> None:
            execution_order.append(self.marker)
            if self.marker == "fail":
                raise ValueError("intentional failure")

    algo = Algorithm()
    algo.append(TrackingSolver, "first")
    algo.append(TrackingSolver, "fail")
    algo.append(TrackingSolver, "never_reached")

    with pytest.raises(OrAlgoException) as exc_info:
        algo.solve(Register[Parameter]())

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

        def solve(self, data: Register[Parameter]) -> None:
            data[Id][(Index,)][(0,)] = f"value={self.value}"

    algo = Algorithm()
    algo.append(ConfiguredSolver, 42)

    register = Register[Parameter]()
    algo.solve(register)

    assert register[Id][(Index,)][(0,)] == "value=42"


def test_algorithm_solve_with_solver_kwargs():
    """Test that solver keyword args are passed correctly."""
    class ConfiguredSolver(Solver):
        def __init__(self, value: int, flag: bool = False):
            super().__init__()
            self.value = value
            self.flag = flag

        def solve(self, data: Register[Parameter]) -> None:
            data[Id][(Index,)][(0,)] = f"value={self.value},flag={self.flag}"

    algo = Algorithm()
    algo.append(ConfiguredSolver, 42, flag=True)

    register = Register[Parameter]()
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

        def solve(self, data: Register[Parameter]) -> None:
            data[Id][(Index,)][(0,)] = f"a={self.a},b={self.b},c={self.c}"

    algo = Algorithm()
    algo.append(ConfiguredSolver, 1, "two", c=True)

    register = Register[Parameter]()
    algo.solve(register)

    assert register[Id][(Index,)][(0,)] == "a=1,b=two,c=True"


def test_algorithm_exception_message():
    """Test that OrAlgoException includes useful information."""
    algo = Algorithm()
    algo.append(FailingSolver)

    with pytest.raises(OrAlgoException) as exc_info:
        algo.solve(Register[Parameter]())

    assert "FailingSolver" in str(exc_info.value)
    assert "solve()" in str(exc_info.value)
