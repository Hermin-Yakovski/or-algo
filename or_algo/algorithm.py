"""Algorithm orchestrator class for or-algo package."""

from typing import Type
from register import Register, Parameter

from .solver import Solver
from .exception import OrAlgoException


class Algorithm:
    """Orchestrates sequential execution of multiple Solvers.

    Solvers are executed in the order they are appended. If any solver
    fails, execution stops and an OrAlgoException is raised.
    """

    def __init__(self, *args, **kwargs) -> None:
        """Initialize an empty Algorithm."""
        self._solvers: list[tuple[Type[Solver], tuple, dict]] = []

    def append(self, solver_type: Type[Solver], *args, **kwargs) -> int:
        """Add a solver to the execution sequence.

        Args:
            solver_type: The Solver class to instantiate and execute.
            *args: Positional arguments to pass to the solver constructor.
            **kwargs: Keyword arguments to pass to the solver constructor.

        Returns:
            The 1-based index of the solver in the sequence.
        """
        self._solvers.append((solver_type, args, kwargs))
        return len(self._solvers)

    def solve(self, data: Register[Parameter]) -> None:
        """Execute all solvers in sequence.

        Args:
            data: Register containing input parameters; solutions are
                  written back to this same Register.

        Raises:
            OrAlgoException: If any solver fails. The original exception
                            is chained as the cause.
        """
        for solver, args, kwargs in self._solvers:
            try:
                solver(*args, **kwargs).solve(data)
            except Exception as e:
                raise OrAlgoException(
                    f"Failed {solver.__name__}.solve()! args={args}, kwargs={kwargs}"
                ) from e