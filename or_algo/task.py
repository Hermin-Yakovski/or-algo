"""SolverTask class for parallel execution wrapping."""

from typing import Any
from register import Register, Parameter
from .solver import Solver


class SolverTask:
    """Wraps a solver for parallel execution with state tracking."""

    def __init__(
        self,
        solver_type: type[Solver],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        dependencies: list[int],
        task_id: int,
    ):
        """Initialize a SolverTask.

        Args:
            solver_type: The Solver class to instantiate and run.
            args: Positional arguments to pass to solver constructor.
            kwargs: Keyword arguments to pass to solver constructor.
            dependencies: List of task IDs that must complete before this task.
            task_id: Unique identifier for this task.
        """
        self.solver_type = solver_type
        self.args = args
        self.kwargs = kwargs
        self.dependencies = dependencies
        self.task_id = task_id
        self.state: str = "pending"
        self.exception: Exception | None = None

    def mark_running(self) -> None:
        """Mark task as running."""
        self.state = "running"

    def mark_completed(self) -> None:
        """Mark task as completed."""
        self.state = "completed"

    def mark_failed(self, exc: Exception) -> None:
        """Mark task as failed with exception.

        Args:
            exc: The exception that caused the failure.
        """
        self.state = "failed"
        self.exception = exc

    def execute(self, reg: Register[Parameter]) -> Register[Parameter]:
        """Run solver and return modified Register.

        Args:
            reg: Register containing parameters for the solver.

        Returns:
            The modified Register with solver results.

        Raises:
            Exception: If solver.solve() raises an exception.
        """
        self.mark_running()
        try:
            solver = self.solver_type(*self.args, **self.kwargs)
            result = solver.solve(reg)
            self.mark_completed()
            return result
        except Exception as e:
            self.mark_failed(e)
            raise
