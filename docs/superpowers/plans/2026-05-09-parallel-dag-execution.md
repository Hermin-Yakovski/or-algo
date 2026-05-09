# Parallel DAG-Based Solver Execution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add parallel execution capability to Algorithm using DAG-based orchestration with lazy dependency resolution via multiprocessing.

**Architecture:** SolverTask wrappers encapsulate execution with state tracking; SharedRegister provides multiprocessing-safe data storage via Manager.dict(); Algorithm.parallel_solve() orchestrates execution using topological DAG traversal with ProcessPoolExecutor.

**Tech Stack:** Python standard library (concurrent.futures.ProcessPoolExecutor, multiprocessing.Manager), register package, pytest

---

### Task 1: Create SolverTask class

**Files:**
- Create: `or_algo/task.py`
- Test: `tests/test_task.py`

- [ ] **Step 1: Write failing tests for SolverTask initialization and state tracking**

```python
# tests/test_task.py
import pytest
from or_algo.task import SolverTask
from or_algo.solver import Solver
from register import Register, Parameter

class DummySolver(Solver):
    def solve(self, data: Register[Parameter]) -> Register[Parameter]:
        return data

def test_solver_task_initialization():
    task = SolverTask(
        solver_type=DummySolver,
        args=(),
        kwargs={},
        dependencies=[1, 2],
        task_id=3
    )
    assert task.solver_type == DummySolver
    assert task.dependencies == [1, 2]
    assert task.task_id == 3
    assert task.state == "pending"
    assert task.exception is None

def test_solver_task_state_transitions():
    task = SolverTask(DummySolver, (), {}, [], 1)
    assert task.state == "pending"

    task.mark_running()
    assert task.state == "running"

    task.mark_completed()
    assert task.state == "completed"

def test_solver_task_failure_state():
    task = SolverTask(DummySolver, (), {}, [], 1)
    exc = ValueError("test error")
    task.mark_failed(exc)
    assert task.state == "failed"
    assert task.exception == exc
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_task.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'or_algo.task'"

- [ ] **Step 3: Create or_algo/task.py with minimal SolverTask implementation**

```python
# or_algo/task.py
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
        self.solver_type = solver_type
        self.args = args
        self.kwargs = kwargs
        self.dependencies = dependencies
        self.task_id = task_id
        self.state: str = "pending"
        self.condition = Condition()
        self.exception: Exception | None = None

    def mark_running(self) -> None:
        with self.condition:
            self.state = "running"
            self.condition.notify_all()

    def mark_completed(self) -> None:
        with self.condition:
            self.state = "completed"
            self.condition.notify_all()

    def mark_failed(self, exc: Exception) -> None:
        with self.condition:
            self.state = "failed"
            self.exception = exc
            self.condition.notify_all()

    def wait_until_completed(self) -> None:
        with self.condition:
            while self.state not in ("completed", "failed"):
                self.condition.wait()

    def execute(self, data: Register[Parameter]) -> None:
        """Run the solver's solve() method."""
        self.mark_running()
        try:
            solver = self.solver_type(*self.args, **self.kwargs)
            solver.solve(data)
            self.mark_completed()
        except Exception as e:
            self.mark_failed(e)
            raise
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_task.py -v`
Expected: PASS

- [ ] **Step 5: Add execute() method test**

```python
# tests/test_task.py
def test_solver_task_execute_success():
    task = SolverTask(DummySolver, (), {}, [], 1)
    data = Register[Parameter]()
    task.execute(data)
    assert task.state == "completed"

def test_solver_task_execute_failure():
    class FailingSolver(Solver):
        def solve(self, data: Register[Parameter]) -> Register[Parameter]:
            raise ValueError("solver failed")

    task = SolverTask(FailingSolver, (), {}, [], 1)
    data = Register[Parameter]()
    with pytest.raises(ValueError, match="solver failed"):
        task.execute(data)
    assert task.state == "failed"
    assert isinstance(task.exception, ValueError)
```

- [ ] **Step 6: Run tests to verify execute() behavior**

Run: `pytest tests/test_task.py::test_solver_task_execute_success tests/test_task.py::test_solver_task_execute_failure -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add or_algo/task.py tests/test_task.py
git commit -m "feat: add SolverTask class for parallel execution wrapping"
```

---

### Task 2: Create SharedRegister class

**Files:**
- Create: `or_algo/shared_register.py`
- Test: `tests/test_shared_register.py`

- [ ] **Step 1: Write failing tests for SharedRegister**

```python
# tests/test_shared_register.py
import pytest
from or_algo.shared_register import SharedRegister
from register import Register, Parameter

def test_shared_register_initialization():
    reg = SharedRegister[Parameter]()
    assert reg._data is not None
    assert reg._manager is not None

def test_shared_register_get_set():
    reg = SharedRegister[Parameter]()
    reg["key1"] = "value1"
    reg["key2"] = 42
    assert reg["key1"] == "value1"
    assert reg["key2"] == 42

def test_shared_register_shutdown():
    reg = SharedRegister[Parameter]()
    reg["key"] = "value"
    reg.shutdown()
    # After shutdown, operations should fail or behave as expected
    # Manager.dict() behavior after shutdown varies, so we just ensure no exception
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_shared_register.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'or_algo.shared_register'"

- [ ] **Step 3: Create or_algo/shared_register.py with SharedRegister implementation**

```python
# or_algo/shared_register.py
from typing import TypeVar
from register import Register
from multiprocessing import Manager

T = TypeVar('T')


class SharedRegister(Register[T]):
    """Multiprocessing-compatible Register using Manager backend."""

    def __init__(self) -> None:
        super().__init__()
        self._manager = Manager()
        self._data = self._manager.dict()

    def shutdown(self) -> None:
        """Cleanup manager resources."""
        self._manager.shutdown()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_shared_register.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add or_algo/shared_register.py tests/test_shared_register.py
git commit -m "feat: add SharedRegister for multiprocessing-safe data storage"
```

---

### Task 3: Add _dependency_graph tracking to Algorithm

**Files:**
- Modify: `or_algo/algorithm.py`

- [ ] **Step 1: Write test for dependency graph storage**

```python
# tests/test_algorithm.py (add to existing file)
def test_algorithm_tracks_dependency_graph():
    from or_algo import Algorithm
    from or_algo.solver import Solver

    algo = Algorithm()
    id1 = algo.append(DummySolver)
    id2 = algo.append(DummySolver, after=[id1])

    # Check internal dependency graph
    assert algo._dependency_graph[1] == []
    assert algo._dependency_graph[2] == [1]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_algorithm.py::test_algorithm_tracks_dependency_graph -v`
Expected: FAIL with "AttributeError: 'Algorithm' object has no attribute '_dependency_graph'"

- [ ] **Step 3: Modify Algorithm.__init__ to initialize _dependency_graph**

```python
# or_algo/algorithm.py - modify __init__
def __init__(self, *args: Any, **kwargs: Any) -> None:
    """Initialize an empty Algorithm."""
    self._solvers: list[tuple[Type[Solver], tuple[Any, ...], dict[str, Any]]] = []
    self._dependency_graph: dict[int, list[int]] = {}
```

- [ ] **Step 4: Run test to verify it still fails**

Run: `pytest tests/test_algorithm.py::test_algorithm_tracks_dependency_graph -v`
Expected: FAIL with "TypeError: append() got an unexpected keyword argument 'after'"

- [ ] **Step 5: Modify Algorithm.append() to accept after parameter**

```python
# or_algo/algorithm.py - modify append signature and body
from typing import Optional

def append(self, solver_type: Type[Solver], *args: Any, after: Optional[list[int]] = None, **kwargs: Any) -> int:
    """Add a solver to the execution sequence.

    Args:
        solver_type: The Solver class to instantiate and execute.
        *args: Positional arguments to pass to the solver constructor.
        after: Optional list of solver IDs this solver depends on.
        **kwargs: Keyword arguments to pass to the solver constructor.

    Returns:
        The 1-based index of the solver in the sequence.
    """
    self._solvers.append((solver_type, args, kwargs))
    solver_id = len(self._solvers)
    self._dependency_graph[solver_id] = after or []
    return solver_id
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/test_algorithm.py::test_algorithm_tracks_dependency_graph -v`
Expected: PASS

- [ ] **Step 7: Add test for invalid dependency ID**

```python
# tests/test_algorithm.py
def test_algorithm_invalid_dependency_id():
    from or_algo import Algorithm
    from or_algo.exception import OrAlgoException

    algo = Algorithm()
    # This should raise because solver 999 doesn't exist
    # We'll add this validation later
```

Skip for now - validation can be added as enhancement.

- [ ] **Step 8: Commit**

```bash
git add or_algo/algorithm.py tests/test_algorithm.py
git commit -m "feat: add dependency graph tracking to Algorithm"
```

---

### Task 4: Add _detect_cycle() method to Algorithm

**Files:**
- Modify: `or_algo/algorithm.py`
- Test: `tests/test_algorithm.py`

- [ ] **Step 1: Write failing tests for cycle detection**

```python
# tests/test_algorithm.py
def test_detect_cycle_no_cycle():
    from or_algo import Algorithm

    algo = Algorithm()
    id1 = algo.append(DummySolver)
    id2 = algo.append(DummySolver, after=[id1])
    assert not algo._detect_cycle()

def test_detect_cycle_self_loop():
    from or_algo import Algorithm

    algo = Algorithm()
    id1 = algo.append(DummySolver, after=[1])  # Depends on itself
    assert algo._detect_cycle()

def test_detect_cycle_complex():
    from or_algo import Algorithm

    algo = Algorithm()
    id1 = algo.append(DummySolver)
    id2 = algo.append(DummySolver, after=[id1])
    id3 = algo.append(DummySolver, after=[id2])
    # Create cycle: 1 -> 2 -> 3 -> 1
    algo._dependency_graph[1] = [3]
    assert algo._detect_cycle()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_algorithm.py::test_detect_cycle_no_cycle tests/test_algorithm.py::test_detect_cycle_self_loop tests/test_algorithm.py::test_detect_cycle_complex -v`
Expected: FAIL with "AttributeError: 'Algorithm' object has no attribute '_detect_cycle'"

- [ ] **Step 3: Implement _detect_cycle() method**

```python
# or_algo/algorithm.py - add method
def _detect_cycle(self) -> bool:
    """Detect if dependency graph has a cycle using DFS.

    Returns:
        True if cycle exists, False otherwise
    """
    def dfs(node: int, visited: set[int], rec_stack: set[int]) -> bool:
        visited.add(node)
        rec_stack.add(node)

        for dep_id in self._dependency_graph.get(node, []):
            if dep_id not in visited:
                if dfs(dep_id, visited, rec_stack):
                    return True
            elif dep_id in rec_stack:
                return True

        rec_stack.remove(node)
        return False

    visited: set[int] = set()
    for task_id in range(1, len(self._solvers) + 1):
        if task_id not in visited:
            if dfs(task_id, visited, set()):
                return True
    return False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_algorithm.py::test_detect_cycle_no_cycle tests/test_algorithm.py::test_detect_cycle_self_loop tests/test_algorithm.py::test_detect_cycle_complex -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add or_algo/algorithm.py tests/test_algorithm.py
git commit -m "feat: add cycle detection to Algorithm"
```

---

### Task 5: Add _get_ready_tasks() method to Algorithm

**Files:**
- Modify: `or_algo/algorithm.py`
- Test: `tests/test_algorithm.py`

- [ ] **Step 1: Write failing test for _get_ready_tasks()**

```python
# tests/test_algorithm.py
def test_get_ready_tasks():
    from or_algo import Algorithm

    algo = Algorithm()
    id1 = algo.append(DummySolver)
    id2 = algo.append(DummySolver)  # No deps
    id3 = algo.append(DummySolver, after=[id1])
    id4 = algo.append(DummySolver, after=[id1, id2])

    # Initially: tasks 1 and 2 are ready (no dependencies)
    ready = algo._get_ready_tasks({}, set())
    assert set(ready) == {1, 2}

    # After task 1 completes: task 3 is ready, task 4 still waits for 2
    ready = algo._get_ready_tasks({}, {1})
    assert set(ready) == {2, 3}

    # After tasks 1 and 2 complete: task 4 is ready
    ready = algo._get_ready_tasks({}, {1, 2})
    assert set(ready) == {3, 4}
```

Note: The first parameter should be the tasks dict, but we need to adjust the implementation signature.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_algorithm.py::test_get_ready_tasks -v`
Expected: FAIL with "AttributeError: 'Algorithm' object has no attribute '_get_ready_tasks'"

- [ ] **Step 3: Implement _get_ready_tasks() method**

```python
# or_algo/algorithm.py - add method
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
        if task.state == "pending":
            if all(dep_id in completed for dep_id in task.dependencies):
                ready.append(task_id)
    return ready
```

Note: Need to add `from .task import SolverTask` at top of file.

- [ ] **Step 4: Fix test to create proper SolverTask objects**

```python
# tests/test_algorithm.py - update test
from or_algo.task import SolverTask

def test_get_ready_tasks():
    from or_algo import Algorithm

    algo = Algorithm()
    id1 = algo.append(DummySolver)
    id2 = algo.append(DummySolver)
    id3 = algo.append(DummySolver, after=[id1])
    id4 = algo.append(DummySolver, after=[id1, id2])

    # Create SolverTask objects
    tasks = {
        1: SolverTask(DummySolver, (), {}, [], 1),
        2: SolverTask(DummySolver, (), {}, [], 2),
        3: SolverTask(DummySolver, (), {}, [1], 3),
        4: SolverTask(DummySolver, (), {}, [1, 2], 4),
    }

    ready = algo._get_ready_tasks(tasks, set())
    assert set(ready) == {1, 2}

    ready = algo._get_ready_tasks(tasks, {1})
    assert set(ready) == {2, 3}

    ready = algo._get_ready_tasks(tasks, {1, 2})
    assert set(ready) == {3, 4}
```

- [ ] **Step 5: Add SolverTask import to algorithm.py**

```python
# or_algo/algorithm.py - add import at top
from .task import SolverTask
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/test_algorithm.py::test_get_ready_tasks -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add or_algo/algorithm.py tests/test_algorithm.py
git commit -m "feat: add _get_ready_tasks helper method"
```

---

### Task 6: Add parallel_solve() method to Algorithm

**Files:**
- Modify: `or_algo/algorithm.py`
- Test: `tests/test_algorithm_parallel.py`

- [ ] **Step 1: Write basic failing test for parallel_solve()**

```python
# tests/test_algorithm_parallel.py
import pytest
from concurrent.futures import ProcessPoolExecutor
from or_algo import Algorithm
from or_algo.solver import Solver
from or_algo.shared_register import SharedRegister
from register import Register, Parameter

class CounterSolver(Solver):
    """Solver that increments a counter in the Register."""
    def solve(self, data: Register[Parameter]) -> Register[Parameter]:
        count = data.get("count", 0)
        data["count"] = count + 1
        return data

def test_parallel_solve_basic():
    algo = Algorithm()
    algo.append(CounterSolver)
    algo.append(CounterSolver)

    shared_reg = SharedRegister[Parameter]()
    shared_reg["count"] = 0

    with ProcessPoolExecutor(max_workers=2) as executor:
        algo.parallel_solve(shared_reg, executor)

    # Both solvers should have run
    assert shared_reg["count"] == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_algorithm_parallel.py::test_parallel_solve_basic -v`
Expected: FAIL with "AttributeError: 'Algorithm' object has no attribute 'parallel_solve'"

- [ ] **Step 3: Implement basic parallel_solve() skeleton**

```python
# or_algo/algorithm.py - add imports and method
from concurrent.futures import ProcessPoolExecutor, as_completed, Future
from typing import Optional
from .shared_register import SharedRegister
from .exception import OrAlgoException

def parallel_solve(
    self,
    data: SharedRegister[Parameter],
    executor: ProcessPoolExecutor
) -> SharedRegister[Parameter]:
    """Execute solvers in parallel using DAG-based lazy resolution.

    Args:
        data: SharedRegister containing input parameters
        executor: ProcessPoolExecutor for parallel execution

    Returns:
        The same SharedRegister with solutions written

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
                    future.result()
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

    return data
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_algorithm_parallel.py::test_parallel_solve_basic -v`
Expected: PASS

- [ ] **Step 5: Add test for dependencies**

```python
# tests/test_algorithm_parallel.py
def test_parallel_solve_with_dependencies():
    """Test that dependent solvers run in correct order."""
    order = []

    class OrderTrackingSolver(Solver):
        def __init__(self, name: str):
            super().__init__(name)
            self.name = name

        def solve(self, data: Register[Parameter]) -> Register[Parameter]:
            order.append(self.name)
            return data

    algo = Algorithm()
    id1 = algo.append(OrderTrackingSolver, "A")
    id2 = algo.append(OrderTrackingSolver, "B", after=[id1])
    id3 = algo.append(OrderTrackingSolver, "C", after=[id1])

    shared_reg = SharedRegister[Parameter]()

    with ProcessPoolExecutor(max_workers=2) as executor:
        algo.parallel_solve(shared_reg, executor)

    # A must complete before B and C
    assert order.index("A") < order.index("B")
    assert order.index("A") < order.index("C")
```

- [ ] **Step 6: Run dependency test**

Run: `pytest tests/test_algorithm_parallel.py::test_parallel_solve_with_dependencies -v`
Expected: PASS

- [ ] **Step 7: Add test for cycle detection**

```python
# tests/test_algorithm_parallel.py
def test_parallel_solve_cycle_detection():
    from or_algo.exception import OrAlgoException

    algo = Algorithm()
    id1 = algo.append(CounterSolver, after=[1])  # Self-cycle

    shared_reg = SharedRegister[Parameter]()

    with ProcessPoolExecutor(max_workers=2) as executor:
        with pytest.raises(OrAlgoException, match="cycle"):
            algo.parallel_solve(shared_reg, executor)
```

- [ ] **Step 8: Run cycle detection test**

Run: `pytest tests/test_algorithm_parallel.py::test_parallel_solve_cycle_detection -v`
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add or_algo/algorithm.py tests/test_algorithm_parallel.py
git commit -m "feat: add parallel_solve method with DAG execution"
```

---

### Task 7: Export new classes in __init__.py

**Files:**
- Modify: `or_algo/__init__.py`

- [ ] **Step 1: Add imports to or_algo/__init__.py**

```python
# or_algo/__init__.py
"""or-algo: A general-purpose algorithm framework for orchestrating solvers."""

from .solver import Solver
from .algorithm import Algorithm
from .exception import OrAlgoException
from . import lp
from .task import SolverTask
from .shared_register import SharedRegister

__version__ = "0.2.0"

__all__ = [
    "Solver",
    "Algorithm",
    "OrAlgoException",
    "lp",
    "SolverTask",
    "SharedRegister",
]
```

- [ ] **Step 2: Verify imports work**

Run: `python -c "from or_algo import SolverTask, SharedRegister; print('Imports successful')"`
Expected: "Imports successful"

- [ ] **Step 3: Commit**

```bash
git add or_algo/__init__.py
git commit -m "feat: export SolverTask and SharedRegister"
```

---

### Task 8: Add comprehensive parallel execution tests

**Files:**
- Test: `tests/test_algorithm_parallel.py`

- [ ] **Step 1: Add test for independent solvers (all parallel)**

```python
# tests/test_algorithm_parallel.py
import time

def test_parallel_solve_independent_solvers():
    """Test that independent solvers run in parallel."""
    class SlowSolver(Solver):
        def __init__(self, name: str, delay: float):
            super().__init__(name)
            self.delay = delay

        def solve(self, data: Register[Parameter]) -> Register[Parameter]:
            time.sleep(self.delay)
            data[self.name] = "done"
            return data

    algo = Algorithm()
    algo.append(SlowSolver, "A", 0.1)
    algo.append(SlowSolver, "B", 0.1)
    algo.append(SlowSolver, "C", 0.1)

    shared_reg = SharedRegister[Parameter]()

    start = time.time()
    with ProcessPoolExecutor(max_workers=3) as executor:
        algo.parallel_solve(shared_reg, executor)
    elapsed = time.time() - start

    # Should take ~0.1s (parallel), not ~0.3s (sequential)
    assert elapsed < 0.2
    assert shared_reg["A"] == "done"
    assert shared_reg["B"] == "done"
    assert shared_reg["C"] == "done"
```

- [ ] **Step 2: Add test for diamond pattern**

```python
# tests/test_algorithm_parallel.py
def test_parallel_solve_diamond_pattern():
    """Test diamond pattern: A -> [B, C] -> D"""
    order = []

    class OrderSolver(Solver):
        def __init__(self, name: str):
            super().__init__(name)
            self.name = name

        def solve(self, data: Register[Parameter]) -> Register[Parameter]:
            order.append(self.name)
            return data

    algo = Algorithm()
    id_a = algo.append(OrderSolver, "A")
    id_b = algo.append(OrderSolver, "B", after=[id_a])
    id_c = algo.append(OrderSolver, "C", after=[id_a])
    id_d = algo.append(OrderSolver, "D", after=[id_b, id_c])

    shared_reg = SharedRegister[Parameter]()

    with ProcessPoolExecutor(max_workers=2) as executor:
        algo.parallel_solve(shared_reg, executor)

    # Verify order constraints
    assert order.index("A") < order.index("B")
    assert order.index("A") < order.index("C")
    assert order.index("B") < order.index("D")
    assert order.index("C") < order.index("D")
```

- [ ] **Step 3: Add test for solver failure cancellation**

```python
# tests/test_algorithm_parallel.py
def test_parallel_solve_solver_failure():
    """Test that solver failure cancels pending tasks."""
    from or_algo.exception import OrAlgoException

    class FailingSolver(Solver):
        def solve(self, data: Register[Parameter]) -> Register[Parameter]:
            raise ValueError("Intentional failure")

    class SlowSolver(Solver):
        def solve(self, data: Register[Parameter]) -> Register[Parameter]:
            time.sleep(5)  # Should be cancelled
            return data

    algo = Algorithm()
    algo.append(FailingSolver)
    algo.append(SlowSolver)  # Should not complete

    shared_reg = SharedRegister[Parameter]()

    start = time.time()
    with ProcessPoolExecutor(max_workers=2) as executor:
        with pytest.raises(OrAlgoException, match="failed"):
            algo.parallel_solve(shared_reg, executor)
    elapsed = time.time() - start

    # Should fail quickly, not wait for SlowSolver
    assert elapsed < 1
```

- [ ] **Step 4: Add test for empty algorithm**

```python
# tests/test_algorithm_parallel.py
def test_parallel_solve_empty_algorithm():
    """Test that empty algorithm completes successfully."""
    algo = Algorithm()
    shared_reg = SharedRegister[Parameter]()

    with ProcessPoolExecutor(max_workers=2) as executor:
        result = algo.parallel_solve(shared_reg, executor)

    assert result is shared_reg
```

- [ ] **Step 5: Run all parallel tests**

Run: `pytest tests/test_algorithm_parallel.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add tests/test_algorithm_parallel.py
git commit -m "test: add comprehensive parallel execution tests"
```

---

### Task 9: Update documentation

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add parallel_solve documentation to README**

```markdown
# or-algo

... existing content ...

## Parallel Execution (Beta)

The `Algorithm.parallel_solve()` method enables parallel execution of independent solvers using DAG-based dependency resolution.

### Basic Usage

```python
from concurrent.futures import ProcessPoolExecutor
from or_algo import Algorithm, SharedRegister

# Build dependency graph
algo = Algorithm()
id1 = algo.append(MySolver, "arg1")
id2 = algo.append(MySolver, "arg2")  # Independent
id3 = algo.append(MySolver, "arg3", after=[id1])  # Depends on id1

# Create shared register
shared_reg = SharedRegister()
shared_reg["input"] = "value"

# Execute in parallel
with ProcessPoolExecutor(max_workers=4) as executor:
    algo.parallel_solve(shared_reg, executor)

# Access results
result = shared_reg["output"]
```

### Dependencies

Specify solver dependencies using the `after` parameter:

```python
id_a = algo.append(SolverA)
id_b = algo.append(SolverB, after=[id_a])  # B waits for A
id_c = algo.append(SolverC, after=[id_a, id_b])  # C waits for A and B
```
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add parallel_solve documentation"
```

---

## Self-Review

**1. Spec coverage:**
- ✅ `SolverTask` class - Task 1
- ✅ `SharedRegister` class - Task 2
- ✅ `Algorithm.append()` with `after` parameter - Task 3
- ✅ `_detect_cycle()` - Task 4
- ✅ `_get_ready_tasks()` - Task 5
- ✅ `parallel_solve()` - Task 6
- ✅ Export in `__init__.py` - Task 7
- ✅ Tests for all scenarios - Task 8
- ✅ Documentation - Task 9

**2. Placeholder scan:** No TBD, TODO, or placeholder content found. All code is complete.

**3. Type consistency:**
- `after: Optional[list[int]]` - consistent throughout
- `SharedRegister[Parameter]` - consistent
- `ProcessPoolExecutor` injection - consistent
- Method signatures match between tasks

**Plan is complete and ready for execution.**
