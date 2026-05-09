"""Algorithm orchestrator class for or-algo package."""

from typing import Any, Optional, Type
from register import Register, Parameter

from concurrent.futures import ProcessPoolExecutor, as_completed, Future

from .solver import Solver
from .exception import OrAlgoException
from .task import SolverTask


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

    def _get_ready_tasks(
        self,
        tasks: dict[int, "SolverTask"],
        completed: set[int]
    ) -> list[int]:
        """Find tasks whose dependencies are all satisfied.

        Args:
            tasks: Map of task_id to SolverTask
            completed: Set of completed task IDs

        Returns:
            List of task IDs ready to execute
        """
        ready = []
        for task_id, task in tasks.items():
            if task_id not in completed and task.state == "pending":
                if all(dep_id in completed for dep_id in task.dependencies):
                    ready.append(task_id)
        return ready

    def _merge_register(self, target: Register[Parameter], source: Register[Parameter]) -> None:
        """Merge source Register into target Register.

        Iterates through all Parameters and dimensions in source,
        copying the inner dict to target. This preserves Register's
        nested structure: Parameter -> DimensionAsKey -> dict.

        Args:
            target: Register to merge into (modified in place)
            source: Register to merge from
        """
        for var in source:
            for dimensions in source[var]:
                target[var][dimensions].clear()
                target[var][dimensions].update(source[var][dimensions])

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

    def parallel_solve(
        self,
        data: Register[Parameter],
        executor: ProcessPoolExecutor
    ) -> None:
        """Execute solvers in parallel using DAG-based lazy resolution.

        Args:
            data: Register containing input parameters; solutions are
                 merged back into this same Register.
            executor: ProcessPoolExecutor for parallel execution

        Raises:
            OrAlgoException: If cycle detected or any solver fails
        """
        # 1. Validate DAG
        if self._detect_cycle():
            raise OrAlgoException("Dependency graph contains a cycle")

        # 2. Build SolverTask wrappers
        tasks: dict[int, SolverTask] = {}
        for task_id, (solver_type, args, kwargs) in enumerate(self._solvers, start=1):
            dependencies = self._dependency_graph.get(task_id, [])
            tasks[task_id] = SolverTask(solver_type, args, kwargs, dependencies, task_id)

        # 3. Track running futures and completed tasks
        futures: dict[Future, int] = {}
        completed: set[int] = set()

        # 4. Submit initially ready tasks
        for task_id in self._get_ready_tasks(tasks, completed):
            task = tasks[task_id]
            future = executor.submit(task.execute, data)
            futures[future] = task_id

        # 5. Main loop
        try:
            while futures:
                for future in as_completed(futures.keys()):
                    task_id = futures.pop(future)
                    task = tasks[task_id]

                    try:
                        solution = future.result()
                        self._merge_register(data, solution)
                        completed.add(task_id)
                    except Exception as e:
                        for f in futures:
                            f.cancel()
                        raise OrAlgoException(
                            f"Task {task_id} ({task.solver_type.__name__}) failed"
                        ) from e

                    # Submit newly ready tasks
                    for ready_id in self._get_ready_tasks(tasks, completed):
                        if ready_id not in completed and ready_id not in futures.values():
                            ready_task = tasks[ready_id]
                            new_future = executor.submit(ready_task.execute, data)
                            futures[new_future] = ready_id

        except Exception as e:
            raise OrAlgoException(f"parallel_solve failed: {e}") from e

        return