"""SolverTask class for parallel execution wrapping."""

from typing import Any

from or_register import Register, RegisterKey

from .solver import Solver


class SolverTask:
    def __init__(
        self,
        solver_type: type[Solver],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        dependencies: list[int],
        task_id: int,
    ):
        self.solver_type = solver_type
        self.args = args
        self.kwargs = kwargs
        self.dependencies = dependencies
        self.task_id = task_id
        self.state: str = "pending"
        self.exception: Exception | None = None

    def mark_running(self) -> None:
        self.state = "running"

    def mark_completed(self) -> None:
        self.state = "completed"

    def mark_failed(self, exc: Exception) -> None:
        self.state = "failed"
        self.exception = exc

    def execute(self, reg: Register[RegisterKey]) -> Register[RegisterKey]:
        self.mark_running()
        try:
            solver = self.solver_type(*self.args, **self.kwargs)
            result = solver.solve(reg)
            self.mark_completed()
            return result
        except Exception as e:
            self.mark_failed(e)
            raise
