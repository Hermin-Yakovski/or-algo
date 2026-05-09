# Parallel DAG-Based Solver Execution

## Overview

Add parallel execution capability to `Algorithm` using DAG-based orchestration with lazy dependency resolution. Solvers run as soon as their dependencies are satisfied, maximizing CPU utilization for CPU-bound operations like OR-Tools LP solves.

## Motivation

`Algorithm.solve()` executes solvers sequentially. For workflows with independent solvers, this wastes CPU cycles. Parallel execution allows independent solvers to run simultaneously while respecting dependencies.

## API Design

### Modified `Algorithm.append()`

```python
def append(self, solver_type: Type[Solver], *args: Any, after: Optional[list[int]] = None, **kwargs: Any) -> int
```

- `after`: List of solver IDs that must complete before this solver runs
- Returns solver ID (1-based index) for dependency specification
- `after=None`: No dependencies (immediately ready)

### New `Algorithm.parallel_solve()`

```python
def parallel_solve(self, data: SharedRegister[Parameter], executor: ProcessPoolExecutor) -> SharedRegister[Parameter]
```

- Executes solvers in parallel using dependency graph
- Blocks until all solvers complete or one fails
- Raises `OrAlgoException` on cycle detection or solver failure
- **Beta API** - `solve()` remains unchanged for sequential execution

### Usage Example

```python
from concurrent.futures import ProcessPoolExecutor
from or_algo import Algorithm
from or_algo.shared_register import SharedRegister

# Build DAG
algo = Algorithm()
id1 = algo.append(SolverA)
id2 = algo.append(SolverB)  # Independent of A
id3 = algo.append(SolverC, after=[id1])  # Depends on A
id4 = algo.append(SolverD, after=[id1, id2])  # Depends on A and B

# Sequential (unchanged)
algo.solve(data)

# Parallel (beta)
executor = ProcessPoolExecutor(max_workers=4)
shared_reg = SharedRegister()
for key in data:
    shared_reg[key] = data[key]
algo.parallel_solve(shared_reg, executor)
```

## Components

### 1. `SolverTask` (`or_algo/task.py`)

Wrapper class encapsulating solver execution with state tracking and inter-process signaling.

```python
class SolverTask:
    def __init__(self, solver_type: type[Solver], args: tuple[Any, ...], kwargs: dict[str, Any], dependencies: list[int], task_id: int)
    def execute(self, data: Register[Parameter]) -> None
    def wait_until_completed(self) -> None
    def mark_running(self) -> None
    def mark_completed(self) -> None
    def mark_failed(self, exc: Exception) -> None
```

**State transitions**: `pending` → `running` → `completed` | `failed`

### 2. `SharedRegister` (`or_algo/shared_register.py`)

Multiprocessing-compatible `Register` using `Manager.dict()` backend.

```python
class SharedRegister(Register[T]):
    def __init__(self) -> None
    def shutdown(self) -> None
```

- Inherits from `Register` for eventual migration to `register` package
- Overrides `self._data` with `Manager.dict()`
- Caller manages data copying: `for key in data: shared[key] = data[key]`

### 3. `Algorithm` modifications (`or_algo/algorithm.py`)

**New attributes**:
- `_dependency_graph: dict[int, list[int]]` - Maps solver ID to list of dependency IDs

**New methods**:
- `parallel_solve()` - Main parallel execution orchestrator
- `_detect_cycle() -> bool` - DFS-based cycle detection
- `_get_ready_tasks() -> list[int]` - Find tasks with satisfied dependencies

## Execution Algorithm

1. **Validate DAG**: Run `_detect_cycle()` - raise if cycle found
2. **Build tasks**: Wrap each solver with `SolverTask`
3. **Initial submission**: Submit tasks with no dependencies to executor
4. **Main loop**:
   - Wait for any future to complete via `as_completed()`
   - On success: Add to `completed` set
   - On failure: Cancel pending futures, raise exception
   - Find newly-ready tasks (all deps in `completed`)
   - Submit ready tasks to executor
5. **Return**: `SharedRegister` with results

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Cycle detected | `OrAlgoException` immediately, no execution |
| Solver fails | Cancel pending futures, raise `OrAlgoException` with task ID and original exception chained |
| Executor full | Blocks until worker available (executor manages this) |

## Testing Strategy

Test file: `tests/test_algorithm_parallel.py`

1. **Sequential baseline**: Verify `solve()` unchanged
2. **Independent solvers**: All run in parallel
3. **Linear chain**: A→B→C→D (sequential via dependencies)
4. **Diamond pattern**: A→[B, C]→D (B and C parallel)
5. **Complex DAG**: Multiple branches merging
6. **Cycle detection**: Verify graceful failure
7. **Solver failure**: Verify cancellation and error propagation
8. **Empty algorithm**: No solvers appended
9. **Single solver**: No dependencies

## Implementation Scope

**Phase 1 (this spec)**:
- Core `parallel_solve()` with lazy dependency resolution
- `SolverTask` wrapper
- `SharedRegister` with Manager backend
- DAG cycle detection
- Basic test coverage

**Out of scope**:
- Dynamic executor management (caller provides executor)
- Async/non-blocking API
- Progress callbacks
- Distributed execution (beyond single machine)

## Dependencies

- `concurrent.futures.ProcessPoolExecutor` - Python standard library
- `multiprocessing.Manager` - Python standard library
- `register` package - Existing dependency
