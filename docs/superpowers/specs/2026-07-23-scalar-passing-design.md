# Scalar Passing Between Solvers — Design

**Date:** 2026-07-23
**Status:** Approved

## Overview

Enable solvers to pass scalar values (e.g., budget constraints, optimal costs, feasibility flags) to downstream solvers through a dedicated channel separate from the dimensional `Register`. The mechanism is optional, backward compatible, and works in both sequential and parallel execution modes.

## Problem Statement

Solvers interact via `Register[RegisterKey]`, a dimensionalized data structure designed for multi-dimensional data like "cost per (product, warehouse, time_period)". However, solvers also need to communicate scalar control parameters:

- User-provided: `max_iterations`, `tolerance`, `solver_type`
- Computed by upstream solvers: `optimal_objective_value`, `is_feasible`, `budget_limit`

Forcing scalar values into the Register's dimensional structure (e.g., fake singleton dimensions or a `configs` dict) is inelegant — Register is designed for dimensional data, not scalar parameters.

## Design Decision

Add an optional `scalars: dict[str, Any]` parameter to `Solver.solve()` and an optional return value of the same type. Scalars are solver-scoped in practice (produced by predetermined solvers), so a flat shared dict with name-based lookup is sufficient. The dependency graph (`after=[...]`) ensures ordering — if Solver B needs Solver A's scalar, B declares a dependency on A.

### Approach Considered and Rejected

1. **SolverContext object** — bundles data + scalars into a context class. Rejected: breaking change to `solve()` signature, more ceremony, mutating shared state.
2. **Lifecycle hooks** (`consume_scalars` / `produce_scalars`) — separate methods called before/after `solve()`. Rejected: 3 methods instead of 1, lifecycle complexity, state management via instance variables.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                      Algorithm                           │
│                                                          │
│   scalars: dict[str, Any] = {}                           │
│                                                          │
│   ┌──────────┐    scalars    ┌──────────┐               │
│   │ Solver A │───{"budget":──▶ Solver B │               │
│   │          │◀──  100.0}───▶│          │               │
│   └──────────┘  returns      └──────────┘               │
│        │         {"cost":          │                     │
│        │          42.5}            │                     │
│        ▼                          ▼                     │
│   ┌──────────────────────────────────────┐              │
│   │         Register[RegisterKey]        │              │
│   │         (dimensional data)           │              │
│   └──────────────────────────────────────┘              │
└──────────────────────────────────────────────────────────┘
```

## Components

### Solver Base Class (solver.py)

```python
from abc import ABC, abstractmethod
from typing import Any
from register import Register, RegisterKey

class Solver(ABC):
    """Abstract base class for solvers that operate on a Register."""

    def __init__(self, name: str | None = None):
        self._name = type(self).__name__ if name is None else name

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    def solve(
        self,
        data: Register[RegisterKey],
        scalars: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """Solve the problem using data from the Register.

        Args:
            data: Register containing input parameters; solutions
                  are written back to this same Register.
            scalars: Optional dict of scalar values from upstream solvers.
                     Read values as needed, return new scalars for downstream.

        Returns:
            Optional dict of scalar values to pass to downstream solvers.
        """
        pass
```

### Algorithm Sequential Execution (algorithm.py)

```python
def solve(self, data: Register[RegisterKey]) -> None:
    """Execute all solvers in sequence.

    Args:
        data: Register containing input parameters; solutions are
              written back to this same Register.

    Raises:
        OrAlgoException: If any solver fails. The original exception
                        is chained as the cause.
    """
    scalars: dict[str, Any] = {}

    for solver, args, kwargs in self._solvers:
        try:
            result = solver(*args, **kwargs).solve(data, scalars)
            if result is not None:
                scalars.update(result)
        except Exception as e:
            raise OrAlgoException(
                f"Failed {solver.__name__}.solve()! args={args}, kwargs={kwargs}"
            ) from e
```

**Key behaviors:**
- `scalars` starts empty
- Each solver receives the accumulated scalars from all upstream solvers
- If a solver returns a dict, those scalars are merged into the shared dict
- If a solver returns `None`, the dict is unchanged
- Scopes are cumulative — solver N sees all scalars from solvers 1..N-1

### Algorithm Parallel Execution (algorithm.py)

```python
def parallel_solve(
    self,
    data: Register[RegisterKey],
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
    futures: dict[Future[tuple[Register[RegisterKey], dict[str, Any] | None]], int] = {}
    completed: set[int] = set()
    scalars: dict[str, Any] = {}  # Shared scalar dict in main process

    # 4. Submit initially ready tasks
    for task_id in self._get_ready_tasks(tasks, completed):
        task = tasks[task_id]
        future = executor.submit(task.execute, data, scalars)
        futures[future] = task_id

    # 5. Main loop
    try:
        while futures:
            for future in as_completed(futures.keys()):
                task_id = futures.pop(future)
                task = tasks[task_id]

                try:
                    solution, new_scalars = future.result()
                    self._merge_register(data, solution)
                    if new_scalars is not None:
                        scalars.update(new_scalars)
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
                        new_future = executor.submit(ready_task.execute, data, scalars)
                        futures[new_future] = ready_id

    except Exception as e:
        raise OrAlgoException(f"parallel_solve failed: {e}") from e
```

**Key differences from sequential:**
- `scalars` dict lives in the main process
- Each task receives a **snapshot** of `scalars` at submit time (pickled across process boundary)
- Tasks return `tuple[Register, dict[str, Any] | None]`
- When a task completes, both Register and scalars are merged back
- Newly ready tasks get the updated `scalars` snapshot

### SolverTask Wrapper (task.py)

```python
from typing import Any
from register import Register, RegisterKey
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

    def execute(
        self,
        reg: Register[RegisterKey],
        scalars: dict[str, Any]
    ) -> tuple[Register[RegisterKey], dict[str, Any] | None]:
        """Execute the solver with data and scalars.

        Args:
            reg: Register to solve on
            scalars: Scalar values from upstream solvers

        Returns:
            Tuple of (modified Register, optional scalars dict)
        """
        self.mark_running()
        try:
            solver = self.solver_type(*self.args, **self.kwargs)
            result = solver.solve(reg, scalars)
            self.mark_completed()
            return reg, result
        except Exception as e:
            self.mark_failed(e)
            raise
```

## Data Flow

### Sequential Mode

```
Solver A ──solve(data, {})──▶ returns {"budget": 100}
                                    │
                            scalars = {"budget": 100}
                                    │
                                    ▼
Solver B ──solve(data, {"budget": 100})──▶ returns {"cost": 42.5}
                                                │
                                    scalars = {"budget": 100, "cost": 42.5}
                                                │
                                                ▼
Solver C ──solve(data, {"budget": 100, "cost": 42.5})──▶ returns None
                                                              │
                                    scalars unchanged
```

### Parallel Mode

```
Main Process                    Process Pool
─────────────────────────────────────────────────────────
scalars = {}

Submit A ──────────────────▶  A.solve(data, {})
Submit B ──────────────────▶  B.solve(data, {})
                                    │
                              A returns (data, {"budget": 100})
                                    │
scalars = {"budget": 100}     ◀─────┘

                              B returns (data, {"flag": True})
                                    │
scalars = {"budget": 100,     ◀─────┘
            "flag": True}

Submit C ──────────────────▶  C.solve(data, {"budget": 100, "flag": True})
```

## Backward Compatibility

Existing solvers require **no changes**. The `scalars` parameter defaults to `None` and the return value defaults to `None` (implicit).

### Migration Example

```python
# Before: existing solver
class MySolver(Solver):
    def solve(self, data):
        # ... solve logic
        pass

# After: optionally adopt scalar passing
class MySolver(Solver):
    def solve(self, data, scalars=None):
        budget = scalars["budget"] if scalars else None
        # ... solve logic
        return {"metric": 42.5}
```

## Testing

### Coverage Areas

- **test_solver.py**: Base class signature with optional scalars parameter and return value
- **test_algorithm.py**: Sequential scalar passing, cumulative merge, edge cases
- **test_algorithm_parallel.py**: Parallel scalar flow through DAG, snapshot behavior
- **test_task.py**: SolverTask with scalar input/output

### Key Test Cases

1. **Backward compatibility**: Existing solvers without `scalars` parameter continue to work
2. **Scalar flow**: Solver A returns scalars, Solver B reads them (both sequential and parallel)
3. **Cumulative merge**: Multiple solvers return scalars, all visible to downstream
4. **Overwrite semantics**: Later solver overwrites earlier scalar with same name (last writer wins)
5. **None returns**: Solver returns `None` → no scalar update
6. **Empty returns**: Solver returns `{}` → no scalar update
7. **Empty input**: Solver receives empty dict `{}` when no upstream has produced any (Algorithm always passes a dict, never `None`)
8. **Parallel snapshot**: Independently running solvers get same scalar snapshot at submit time

**Note:** When called through `Algorithm`, solvers always receive a dict (empty or populated). The `None` default in the `Solver.solve()` signature is for direct calls outside of Algorithm orchestration.

## What Doesn't Change

- `Register` API — stays pure for dimensional data
- Existing solvers — continue to work without modification
- Dependency graph mechanism (`after=[...]`) — unchanged
- Register merge logic (`_merge_register`) — unchanged
- Cycle detection — unchanged
- Error handling — unchanged

## Scope

- Update `Solver` base class signature
- Update `Algorithm.solve()` for sequential scalar passing
- Update `Algorithm.parallel_solve()` for parallel scalar passing
- Update `SolverTask.execute()` for scalar input/output
- Add comprehensive tests for all scalar passing scenarios
- Update README with scalar passing usage example