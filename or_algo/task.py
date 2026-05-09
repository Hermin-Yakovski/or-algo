"""SolverTask class for parallel execution wrapping."""

from typing import Any
from register import Register, Parameter
from multiprocessing import Condition
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
        self.condition = Condition()
        self.exception: Exception | None = None

    def mark_running(self) -> None:
        """Mark task as running and notify waiting threads."""
        with self.condition:
            self.state = "running"
            self.condition.notify_all()

    def mark_completed(self) -> None:
        """Mark task as completed and notify waiting threads."""
        with self.condition:
            self.state = "completed"
            self.condition.notify_all()

    def mark_failed(self, exc: Exception) -> None:
        """Mark task as failed with exception and notify waiting threads.

        Args:
            exc: The exception that caused the failure.
        """
        with self.condition:
            self.state = "failed"
            self.exception = exc
            self.condition.notify_all()

    def wait_until_completed(self) -> None:
        """Block until task is in completed or failed state."""
        with self.condition:
            while self.state not in ("completed", "failed"):
                self.condition.wait()

    def execute(self, data: Register[Parameter]) -> None:
        """Run the solver's solve() method.

        Args:
            data: Register containing parameters for the solver.

        Raises:
            Exception: If solver.solve() raises an exception.
        """
        self.mark_running()
        try:
            solver = self.solver_type(*self.args, **self.kwargs)
            solver.solve(data)
            self.mark_completed()
        except Exception as e:
            self.mark_failed(e)
            raise
