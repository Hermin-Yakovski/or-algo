"""Algorithm orchestrator class for or-algo package."""

from typing import Any, Optional, Type
from register import Register, Parameter

from .solver import Solver
from .exception import OrAlgoException


class Algorithm:
    """Orchestrates sequential execution of multiple Solvers.

    Solvers are executed in the order they are appended. If any solver
    fails, execution stops and an OrAlgoException is raised.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize an empty Algorithm."""
        self._solvers: list[tuple[Type[Solver], tuple[Any, ...], dict[str, Any]]] = []
        self._dependency_graph: dict[int, list[int]] = {}

    def append(self, solver_type: Type[Solver], *args: Any, after: Optional[list[int]] = None, **kwargs: Any) -> int:
        """Add a solver to the execution sequence.

        Args:
            solver_type: The Solver class to instantiate and execute.
            *args: Positional arguments to pass to the solver constructor.
            after: Optional list of solver IDs that must complete before this solver runs.
            **kwargs: Keyword arguments to pass to the solver constructor.

        Returns:
            The 1-based index of the solver in the sequence.
        """
        self._solvers.append((solver_type, args, kwargs))
        solver_id = len(self._solvers)
        self._dependency_graph[solver_id] = after or []
        return solver_id

    def _detect_cycle(self) -> bool:
        """Detect if there is a cycle in the dependency graph.

        Uses DFS with a recursion stack to detect cycles.

        Returns:
            True if a cycle exists, False otherwise.
        """
        visited: set[int] = set()
        rec_stack: set[int] = set()

        def dfs(node: int) -> bool:
            """DFS helper function to detect cycles.

            Args:
                node: Current node being visited.

            Returns:
                True if a cycle is found, False otherwise.
            """
            visited.add(node)
            rec_stack.add(node)

            for dep_id in self._dependency_graph.get(node, []):
                if dep_id not in visited:
                    if dfs(dep_id):
                        return True
                elif dep_id in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for task_id in range(1, len(self._solvers) + 1):
            if task_id not in visited:
                if dfs(task_id):
                    return True

        return False

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