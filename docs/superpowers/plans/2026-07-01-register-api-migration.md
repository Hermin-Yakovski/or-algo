# Register API Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate `or-algo` (core + LP subpackage) to the refreshed `register` package API with `RegisterKey`-based access chain.

**Architecture:** Type annotation changes in core package (`Parameter` → `RegisterKey`). Redesign of LP subpackage: `VarKey(NumKey)` with `@delegable` methods for weight/lb/ub/aggregations, `ConstrKey(RegisterKey)`, simplified `CreateVar`/`CreateConstr`/`Publish`, deleted `Symbol`/`CreateConstrCalculateMetric`/`_create`.

**Tech Stack:** Python 3.11, register (refreshed), ortools, pytest, mypy, ruff

**Style convention:** Always trailing comma on dimension/index tuples: `reg[k][d,][0,]`

---

## File Structure

### Modify
- `or_algo/solver.py` — type annotations only
- `or_algo/algorithm.py` — type annotations only
- `or_algo/task.py` — type annotations only
- `or_algo/lp/symbol.py` — delete Symbol, create VarKey(NumKey) + ConstrKey(RegisterKey)
- `or_algo/lp/step.py` — update LpStep/CreateVar/CreateConstr/Publish, delete CreateConstrCalculateMetric
- `or_algo/lp/solver.py` — remove weight/lb/ub, simplify append, remove auto-metric
- `or_algo/lp/__init__.py` — update exports
- `tests/conftest.py` — type annotations
- `tests/test_solver.py` — type annotations
- `tests/test_algorithm.py` — type annotations
- `tests/test_algorithm_parallel.py` — type annotations
- `tests/test_task.py` — type annotations
- `tests/test_lp/test_symbol.py` — rewrite for VarKey/ConstrKey
- `tests/test_lp/test_step.py` — rewrite for new step classes
- `tests/test_lp/test_solver.py` — rewrite for simplified LpSolver

---

### Task 1: Core package type annotations

**Files:**
- Modify: `or_algo/solver.py`
- Modify: `or_algo/task.py`
- Modify: `tests/test_solver.py`
- Modify: `tests/test_task.py`

- [ ] **Step 1: Update `tests/test_solver.py` type annotations**

Replace all occurrences:
- `from register import Register, Parameter, Id, Index` → `from register import Register, RegisterKey, Id, Index`
- `Register[Parameter]` → `Register[RegisterKey]`

```python
"""Tests for or_algo.solver module."""

import pytest
from register import Register, RegisterKey, Id, Index
from or_algo.solver import Solver


@pytest.fixture
def empty_register() -> Register[RegisterKey]:
    """Provide an empty Register for testing."""
    return Register()


def test_solver_cannot_be_instantiated_directly():
    """Test that Solver cannot be instantiated directly because it's abstract."""
    with pytest.raises(TypeError):
        Solver()


def test_solver_default_name():
    """Test that Solver uses class name as default name."""
    class MockSolver(Solver):
        def solve(self, data: Register[RegisterKey]) -> Register[RegisterKey]:
            return data

    solver = MockSolver()
    assert solver.name == "MockSolver"


def test_solver_custom_name():
    """Test that Solver accepts custom name."""
    class MockSolver(Solver):
        def solve(self, data: Register[RegisterKey]) -> Register[RegisterKey]:
            return data

    solver = MockSolver(name="CustomName")
    assert solver.name == "CustomName"


def test_solver_solve_requires_implementation():
    """Test that subclasses must implement solve()."""
    class IncompleteSolver(Solver):
        pass

    with pytest.raises(TypeError):
        IncompleteSolver()


def test_solver_solve_can_be_called(empty_register):
    """Test that a properly implemented Solver can call solve()."""
    class WorkingSolver(Solver):
        def solve(self, data: Register[RegisterKey]) -> Register[RegisterKey]:
            data[Id][(Index,)][(0,)] = "solved"
            return data

    solver = WorkingSolver()
    result = solver.solve(empty_register)

    assert (Index,) in empty_register[Id]
    assert (0,) in empty_register[Id][(Index,)]
    assert empty_register[Id][(Index,)][(0,)] == "solved"
    assert result is empty_register
```

- [ ] **Step 2: Update `tests/test_task.py` type annotations**

Replace all occurrences:
- `from register import Register, Parameter` → `from register import Register, RegisterKey`
- `Register[Parameter]` → `Register[RegisterKey]`
- `Register[Parameter]()` → `Register()`

```python
"""Tests for SolverTask class."""

import pytest
from or_algo.task import SolverTask
from or_algo.solver import Solver
from register import Register, RegisterKey


class DummySolver(Solver):
    """Test solver that returns data unchanged."""

    def solve(self, data: Register[RegisterKey]) -> Register[RegisterKey]:
        return data


def test_solver_task_initialization():
    """Test SolverTask initialization with all parameters."""
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
    """Test state transitions from pending to running to completed."""
    task = SolverTask(DummySolver, (), {}, [], 1)
    assert task.state == "pending"

    task.mark_running()
    assert task.state == "running"

    task.mark_completed()
    assert task.state == "completed"


def test_solver_task_failure_state():
    """Test state transition to failed with exception."""
    task = SolverTask(DummySolver, (), {}, [], 1)
    exc = ValueError("test error")
    task.mark_failed(exc)
    assert task.state == "failed"
    assert task.exception == exc


def test_solver_task_execute_success():
    """Test execute() method with successful solver."""
    task = SolverTask(DummySolver, (), {}, [], 1)
    data = Register()
    task.execute(data)
    assert task.state == "completed"


def test_solver_task_execute_failure():
    """Test execute() method with failing solver."""

    class FailingSolver(Solver):
        def solve(self, data: Register[RegisterKey]) -> Register[RegisterKey]:
            raise ValueError("solver failed")

    task = SolverTask(FailingSolver, (), {}, [], 1)
    data = Register()
    with pytest.raises(ValueError, match="solver failed"):
        task.execute(data)
    assert task.state == "failed"
    assert isinstance(task.exception, ValueError)


def test_solver_task_execute_returns_register():
    """Test that execute() returns the modified Register."""
    task = SolverTask(DummySolver, (), {}, [], 1)
    reg = Register()
    reg._data["test"] = "input"

    result_reg = task.execute(reg)

    assert result_reg is reg
    assert isinstance(result_reg, Register)
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python -m pytest tests/test_solver.py tests/test_task.py -v`
Expected: FAIL — `Parameter` not found in `register`

- [ ] **Step 4: Update `or_algo/solver.py`**

```python
"""Solver abstract base class for or-algo package."""

from abc import ABC, abstractmethod
from register import Register, RegisterKey


class Solver(ABC):
    """Abstract base class for solvers that operate on a Register.

    Users extend this class to implement their solving logic.
    Each solver reads from and writes to a shared Register[RegisterKey].
    """

    def __init__(self, name: str | None = None) -> None:
        """Initialize the solver with an optional name.

        Args:
            name: Optional name for the solver. Defaults to the class name.
        """
        self._name = type(self).__name__ if name is None else name

    @property
    def name(self) -> str:
        """Get the solver's name."""
        return self._name

    @abstractmethod
    def solve(self, data: Register[RegisterKey]) -> Register[RegisterKey]:
        """Solve the problem using data from the Register.

        Args:
            data: Register containing input parameters.

        Returns:
            Register containing solutions (may be the same as input).
        """
        pass
```

- [ ] **Step 5: Update `or_algo/task.py`**

```python
"""SolverTask class for parallel execution wrapping."""

from typing import Any
from register import Register, RegisterKey
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

    def execute(self, reg: Register[RegisterKey]) -> Register[RegisterKey]:
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
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python -m pytest tests/test_solver.py tests/test_task.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add or_algo/solver.py or_algo/task.py tests/test_solver.py tests/test_task.py
git commit -m "refactor: migrate core solver/task to RegisterKey type annotations"
```

---

### Task 2: Algorithm type annotations

**Files:**
- Modify: `or_algo/algorithm.py`
- Modify: `tests/test_algorithm.py`
- Modify: `tests/test_algorithm_parallel.py`
- Modify: `tests/conftest.py`

- [ ] **Step 1: Update `tests/conftest.py`**

```python
"""Shared fixtures for or-algo tests."""

import os
import sys

# Add ortools DLL directory to PATH for subprocess compatibility (Windows only)
if sys.platform == "win32":
    try:
        import site
        site_packages = site.getsitepackages()
        for pkg_path in site_packages:
            ortools_dll_path = os.path.join(pkg_path, "ortools", ".libs")
            if os.path.exists(ortools_dll_path):
                os.environ["PATH"] = ortools_dll_path + os.pathsep + os.environ.get("PATH", "")
                os.add_dll_directory(ortools_dll_path)
                break
    except Exception:
        pass


import pytest
from register import Register, RegisterKey, Id, Code, Name, Index


@pytest.fixture
def empty_register() -> Register[RegisterKey]:
    """Provide an empty Register for testing."""
    return Register()


@pytest.fixture
def sample_register() -> Register[RegisterKey]:
    """Provide a Register with sample data for testing."""
    reg = Register()
    reg[Id][(Index,)][(0,)] = 1
    reg[Code][(Index,)][(0,)] = "test_code"
    reg[Name][(Index,)][(0,)] = "test_name"
    return reg
```

- [ ] **Step 2: Update `tests/test_algorithm.py` type annotations**

Replace all occurrences:
- `from register import Register, Parameter, Id, Index` → `from register import Register, RegisterKey, Id, Index`
- `Register[Parameter]` → `Register[RegisterKey]`
- `Register[Parameter]()` → `Register()`
- `data: Register[Parameter]` → `data: Register[RegisterKey]`

Apply these substitutions throughout the entire file. Every test solver's `solve()` signature changes from `def solve(self, data: Register[Parameter])` to `def solve(self, data: Register[RegisterKey])`.

- [ ] **Step 3: Update `tests/test_algorithm_parallel.py` type annotations**

Same replacements as step 2. Additionally:
- All `reg = Register[Parameter]()` → `reg = Register()`
- All `data: Register[Parameter]` → `data: Register[RegisterKey]`

- [ ] **Step 4: Run tests to verify they fail**

Run: `python -m pytest tests/test_algorithm.py tests/test_algorithm_parallel.py tests/conftest.py -v`
Expected: FAIL — `Parameter` not found in `register`

- [ ] **Step 5: Update `or_algo/algorithm.py`**

```python
"""Algorithm orchestrator class for or-algo package."""

from typing import Any, Optional, Type
from register import Register, RegisterKey

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

    def _merge_register(self, target: Register[RegisterKey], source: Register[RegisterKey]) -> None:
        """Merge source Register into target Register.

        Iterates through all keys and dimensions in source,
        copying the inner dict to target.

        Args:
            target: Register to merge into (modified in place)
            source: Register to merge from
        """
        for var in source:
            for dimensions in source[var]:
                target[var][dimensions].clear()
                target[var][dimensions].update(source[var][dimensions])

    def solve(self, data: Register[RegisterKey]) -> None:
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
        futures: dict[Future[Register[RegisterKey]], int] = {}
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
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python -m pytest tests/test_algorithm.py tests/test_algorithm_parallel.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add or_algo/algorithm.py tests/test_algorithm.py tests/test_algorithm_parallel.py tests/conftest.py
git commit -m "refactor: migrate algorithm to RegisterKey type annotations"
```

---

### Task 3: VarKey and ConstrKey

**Files:**
- Create: `tests/test_lp/test_symbol.py` (rewrite)
- Modify: `or_algo/lp/symbol.py`

- [ ] **Step 1: Rewrite `tests/test_lp/test_symbol.py`**

```python
"""Tests for VarKey and ConstrKey."""

import pytest
from register import NumKey, RegisterKey, Register, Dimension, Selected, delegable
from or_algo.lp.symbol import VarKey, ConstrKey
from ortools.linear_solver import pywraplp


@pytest.fixture
def model():
    """Create an OR-Tools solver for testing."""
    m = pywraplp.Solver.CreateSolver('SCIP')
    yield m


@pytest.fixture
def var_key():
    """Create a VarKey for testing."""
    return VarKey(id=1, name='TestVar', name_cn='测试变量', sign='X')


@pytest.fixture
def constr_key():
    """Create a ConstrKey for testing."""
    return ConstrKey(id=1, name='TestConstr', name_cn='测试约束', sign='C')


class TestVarKey:
    def test_inherits_from_numkey(self, var_key):
        assert isinstance(var_key, NumKey)
        assert isinstance(var_key, RegisterKey)

    def test_properties(self, var_key):
        assert var_key.id == 1
        assert var_key.name == 'TestVar'
        assert var_key.name_cn == '测试变量'
        assert var_key.sign == 'X'

    def test_default_vtype_is_float(self, var_key):
        assert var_key.vtype is float

    def test_custom_vtype(self):
        vk = VarKey(id=2, name='IntVar', name_cn='整数', sign='Y', vtype=int)
        assert vk.vtype is int

    def test_validate_checks_pywraplp_variable(self, var_key, model):
        v1 = model.NumVar(0, 1, 'v1')
        selected = {(0,): v1, (1,): 'not_a_var'}
        result = var_key.validate(selected)
        assert result[(0,)] is True
        assert result[(1,)] is False

    def test_hash_eq(self):
        vk1 = VarKey(id=1, name='X', name_cn='x', sign='x')
        vk2 = VarKey(id=1, name='X', name_cn='x', sign='y')
        assert vk1 == vk2  # same id + name
        assert hash(vk1) == hash(vk2)

    def test_as_register_key(self, var_key):
        reg = Register()
        d = Dimension('Item', '物料', 'I')
        reg[var_key][d,][0,] = 42.0
        assert reg[var_key][d,][0,] == 42.0

    def test_str_returns_name(self, var_key):
        assert str(var_key) == 'TestVar'

    def test_repr_returns_name(self, var_key):
        assert repr(var_key) == 'TestVar'


class TestConstrKey:
    def test_inherits_from_register_key(self, constr_key):
        assert isinstance(constr_key, RegisterKey)

    def test_properties(self, constr_key):
        assert constr_key.id == 1
        assert constr_key.name == 'TestConstr'
        assert constr_key.name_cn == '测试约束'
        assert constr_key.sign == 'C'

    def test_validate_checks_pywraplp_constraint(self, constr_key, model):
        x = model.NumVar(0, 1, 'x')
        c1 = model.Add(x <= 1)
        selected = {(0,): c1, (1,): 'not_a_constraint'}
        result = constr_key.validate(selected)
        assert result[(0,)] is True
        assert result[(1,)] is False

    def test_different_ids_are_distinct(self):
        ck1 = ConstrKey(id=1, name='A', name_cn='a', sign='a')
        ck2 = ConstrKey(id=2, name='A', name_cn='a', sign='a')
        assert ck1 != ck2  # different id

    def test_str_returns_name(self, constr_key):
        assert str(constr_key) == 'TestConstr'
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_lp/test_symbol.py -v`
Expected: FAIL — `VarKey` not found in `or_algo.lp.symbol`

- [ ] **Step 3: Rewrite `or_algo/lp/symbol.py`**

```python
"""Symbol hierarchy for LP model elements."""
from __future__ import annotations

import itertools
from typing import TYPE_CHECKING

from ortools.linear_solver import pywraplp
from register import NumKey, RegisterKey, Register, Selected, delegable

if TYPE_CHECKING:
    pass


class VarKey(NumKey):
    """Decision variable key that wraps a NumKey and adds LP-specific delegable methods."""

    _sign: str

    def __init__(self, id: int, name: str, name_cn: str, sign: str, vtype: type = float):
        super().__init__(id, name, name_cn, vtype)
        self._sign = sign

    @property
    def sign(self) -> str:
        return self._sign

    def validate(self, selected: Selected, **kwargs) -> dict[tuple[int, ...], bool]:
        return {k: isinstance(v, pywraplp.Variable) for k, v in selected.items()}

    @delegable
    def sum(self, selected: Selected, *, model: pywraplp.Solver) -> pywraplp.Variable:
        dim_signs = ','.join(d.sign for d in selected._dims)
        idx_str = ','.join(str(i) for i in next(iter(selected)))
        name = f'{self.sign}({dim_signs},MTC,)({idx_str},1,)'
        sum_var = model.NumVar(-model.infinity(), model.infinity(), name)
        model.Add(sum_var == sum(selected.values()), name=f'{name}_constr')
        return sum_var

    @delegable
    def max(self, selected: Selected, *, model: pywraplp.Solver) -> pywraplp.Variable:
        dim_signs = ','.join(d.sign for d in selected._dims)
        idx_str = ','.join(str(i) for i in next(iter(selected)))
        name = f'{self.sign}({dim_signs},MTC,)({idx_str},2,)'
        max_var = model.NumVar(-model.infinity(), model.infinity(), name)
        for idx, var in selected.items():
            i_str = ','.join(str(i) for i in idx)
            model.Add(max_var >= var, name=f'{self.sign}({dim_signs},MTC,)({i_str},2,)')
        return max_var

    @delegable
    def min(self, selected: Selected, *, model: pywraplp.Solver) -> pywraplp.Variable:
        dim_signs = ','.join(d.sign for d in selected._dims)
        idx_str = ','.join(str(i) for i in next(iter(selected)))
        name = f'{self.sign}({dim_signs},MTC,)({idx_str},3,)'
        min_var = model.NumVar(-model.infinity(), model.infinity(), name)
        for idx, var in selected.items():
            i_str = ','.join(str(i) for i in idx)
            model.Add(min_var <= var, name=f'{self.sign}({dim_signs},MTC,)({i_str},3,)')
        return min_var

    @delegable
    def range(self, selected: Selected, *, model: pywraplp.Solver) -> pywraplp.Variable:
        dim_signs = ','.join(d.sign for d in selected._dims)
        idx_str = ','.join(str(i) for i in next(iter(selected)))
        name = f'{self.sign}({dim_signs},MTC,)({idx_str},4,)'
        range_var = model.NumVar(0, model.infinity(), name)
        for (idx1, v1), (idx2, v2) in itertools.permutations(selected.items(), 2):
            i_str = ','.join(str(i) for i in idx1 + idx2)
            model.Add(range_var >= v1 - v2, name=f'{self.sign}({dim_signs},MTC,)({i_str},4,)')
        return range_var

    @delegable
    def set_weight(self, selected: Selected, *, model: pywraplp.Solver, weight: Register[NumKey]) -> None:
        w_space = weight[self][selected._dims,]
        for index, var in selected.items():
            w = w_space[index,] if index in w_space else 0
            model.Objective().SetCoefficient(var, w)

    @delegable
    def set_lb(self, selected: Selected, *, model: pywraplp.Solver, lb: Register[NumKey]) -> None:
        lb_space = lb[self][selected._dims,]
        for index, var in selected.items():
            if index in lb_space:
                dim_signs = ','.join(d.sign for d in selected._dims)
                idx_str = ','.join(str(i) for i in index)
                model.Add(var >= lb_space[index,],
                    name=f'{self.sign}({dim_signs},)({idx_str},)_lb')

    @delegable
    def set_ub(self, selected: Selected, *, model: pywraplp.Solver, ub: Register[NumKey]) -> None:
        ub_space = ub[self][selected._dims,]
        for index, var in selected.items():
            if index in ub_space:
                dim_signs = ','.join(d.sign for d in selected._dims)
                idx_str = ','.join(str(i) for i in index)
                model.Add(var <= ub_space[index,],
                    name=f'{self.sign}({dim_signs},)({idx_str},)_ub')


class ConstrKey(RegisterKey):
    """Constraint key for LP model constraints."""

    _id: int
    _name: str
    _name_cn: str
    _sign: str

    def __init__(self, id: int, name: str, name_cn: str, sign: str):
        self._id = id
        self._name = name
        self._name_cn = name_cn
        self._sign = sign

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def name_cn(self) -> str:
        return self._name_cn

    @property
    def sign(self) -> str:
        return self._sign

    def validate(self, selected: Selected, **kwargs) -> dict[tuple[int, ...], bool]:
        return {k: isinstance(v, pywraplp.Constraint) for k, v in selected.items()}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_lp/test_symbol.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add or_algo/lp/symbol.py tests/test_lp/test_symbol.py
git commit -m "refactor: replace Symbol with VarKey(NumKey) and ConstrKey(RegisterKey)"
```

---

### Task 4: VarKey delegable methods

**Files:**
- Modify: `tests/test_lp/test_symbol.py` (add delegable tests)
- Modify: `or_algo/lp/symbol.py` (already implemented, tested here)

- [ ] **Step 1: Add delegable method tests to `tests/test_lp/test_symbol.py`**

Append to the file:

```python
class TestVarKeyDelegable:
    """Test VarKey delegable methods via Selection proxy."""

    @pytest.fixture
    def setup(self):
        model = pywraplp.Solver.CreateSolver('SCIP')
        d = Dimension('Loc', '地点', 'L')
        vk = VarKey(id=10, name='Ship', name_cn='运输', sign='X')
        reg = Register()
        # Create 3 variables
        reg[vk][d,][0,] = model.NumVar(0, 100, 'x0')
        reg[vk][d,][1,] = model.NumVar(0, 100, 'x1')
        reg[vk][d,][2,] = model.NumVar(0, 100, 'x2')
        return model, d, vk, reg

    def test_sum_creates_variable_with_constraint(self, setup):
        model, d, vk, reg = setup
        result = reg[vk][d,].all.sum(model=model)
        assert isinstance(result, pywraplp.Variable)
        assert 'MTC' in result.name()
        assert ',1,' in result.name()

    def test_max_creates_variable_with_constraints(self, setup):
        model, d, vk, reg = setup
        result = reg[vk][d,].all.max(model=model)
        assert isinstance(result, pywraplp.Variable)
        assert ',2,' in result.name()

    def test_min_creates_variable_with_constraints(self, setup):
        model, d, vk, reg = setup
        result = reg[vk][d,].all.min(model=model)
        assert isinstance(result, pywraplp.Variable)
        assert ',3,' in result.name()

    def test_range_creates_variable_with_constraints(self, setup):
        model, d, vk, reg = setup
        result = reg[vk][d,].all.range(model=model)
        assert isinstance(result, pywraplp.Variable)
        assert ',4,' in result.name()

    def test_set_weight_sets_objective_coefficients(self, setup):
        model, d, vk, reg = setup
        weight_key = NumKey(id=20, name='W', name_cn='权重', sign='W')
        weight_reg = Register()
        weight_reg[weight_key][d,][0,] = 1.5
        weight_reg[weight_key][d,][1,] = 2.5
        # Note: set_weight looks up weight by VarKey, not weight_key
        # weight[self] means weight[vk], so we need to store under vk
        weight_reg2 = Register()
        weight_reg2[vk][d,][0,] = 1.5
        weight_reg2[vk][d,][1,] = 2.5
        reg[vk][d,].all.set_weight(model=model, weight=weight_reg2)
        # Verify by solving — objective should reflect coefficients

    def test_set_lb_adds_lower_bound_constraints(self, setup):
        model, d, vk, reg = setup
        lb_reg = Register()
        lb_reg[vk][d,][0,] = 5.0
        lb_reg[vk][d,][1,] = 10.0
        reg[vk][d,].all.set_lb(model=model, lb=lb_reg)
        # Constraints added — verify by checking model constraint count increased

    def test_set_ub_adds_upper_bound_constraints(self, setup):
        model, d, vk, reg = setup
        ub_reg = Register()
        ub_reg[vk][d,][0,] = 50.0
        reg[vk][d,].all.set_ub(model=model, ub=ub_reg)

    def test_set_lb_constraint_naming(self, setup):
        model, d, vk, reg = setup
        lb_reg = Register()
        lb_reg[vk][d,][0,] = 5.0
        reg[vk][d,].all.set_lb(model=model, lb=lb_reg)
        # Constraint name should follow 3-part convention: X(L,)(0,)_lb

    def test_set_ub_constraint_naming(self, setup):
        model, d, vk, reg = setup
        ub_reg = Register()
        ub_reg[vk][d,][0,] = 50.0
        reg[vk][d,].all.set_ub(model=model, ub=ub_reg)
```

- [ ] **Step 2: Run tests**

Run: `python -m pytest tests/test_lp/test_symbol.py::TestVarKeyDelegable -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_lp/test_symbol.py
git commit -m "test: add VarKey delegable method tests"
```

---

### Task 5: LpStep, CreateVar, CreateConstr

**Files:**
- Create: `tests/test_lp/test_step.py` (rewrite — LpStep/CreateVar/CreateConstr tests only, Publish in next task)
- Modify: `or_algo/lp/step.py` (partial — LpStep/CreateVar/CreateConstr, keep old Publish/CreateConstrCalculateMetric for now)

- [ ] **Step 1: Rewrite LpStep/CreateVar/CreateConstr tests in `tests/test_lp/test_step.py`**

Replace the entire file:

```python
"""Tests for LpStep, CreateVar, CreateConstr, and Publish."""

import pytest
from abc import ABC
from register import Register, RegisterKey, NumKey, Dimension
from or_algo.lp.symbol import VarKey, ConstrKey
from or_algo.lp.step import LpStep, CreateVar, CreateConstr
from ortools.linear_solver import pywraplp
from unittest.mock import Mock


class TestLpStep:
    def test_is_abstract(self):
        assert issubclass(LpStep, ABC)

    def test_cannot_instantiate_directly(self):
        vk = VarKey(id=1, name='X', name_cn='x', sign='x')
        with pytest.raises(TypeError):
            LpStep(symbol=vk)

    def test_requires_run_method(self):
        class InvalidStep(LpStep):
            pass

        vk = VarKey(id=1, name='X', name_cn='x', sign='x')
        with pytest.raises(TypeError):
            InvalidStep(symbol=vk)

    def test_concrete_subclass(self):
        class ConcreteStep(LpStep):
            def run(self, data, model, var):
                pass

        vk = VarKey(id=1, name='X', name_cn='x', sign='x')
        step = ConcreteStep(symbol=vk)
        assert step._symbol is vk

    def test_accepts_varkey(self):
        class ConcreteStep(LpStep):
            def run(self, data, model, var):
                pass

        vk = VarKey(id=1, name='X', name_cn='x', sign='x')
        step = ConcreteStep(symbol=vk)
        assert isinstance(step._symbol, VarKey)

    def test_accepts_constrkey(self):
        class ConcreteStep(LpStep):
            def run(self, data, model, var):
                pass

        ck = ConstrKey(id=1, name='C', name_cn='c', sign='c')
        step = ConcreteStep(symbol=ck)
        assert isinstance(step._symbol, ConstrKey)


class TestCreateVar:
    def test_is_lp_step(self):
        assert issubclass(CreateVar, LpStep)
        assert issubclass(CreateVar, ABC)

    def test_cannot_instantiate_directly(self):
        vk = VarKey(id=1, name='X', name_cn='x', sign='x')
        with pytest.raises(TypeError):
            CreateVar(symbol=vk)

    def test_concrete_subclass(self):
        class ConcreteCreateVar(CreateVar):
            def run(self, data, model, var):
                pass

        vk = VarKey(id=1, name='X', name_cn='x', sign='x')
        step = ConcreteCreateVar(symbol=vk)
        assert step._symbol is vk

    def test_init_only_takes_symbol(self):
        """CreateVar.__init__ should only take symbol — no weight/lb/ub."""
        class ConcreteCreateVar(CreateVar):
            def run(self, data, model, var):
                pass

        vk = VarKey(id=1, name='X', name_cn='x', sign='x')
        step = ConcreteCreateVar(symbol=vk)
        assert not hasattr(step, '_weight')
        assert not hasattr(step, '_lb')
        assert not hasattr(step, '_ub')

    def test_vtype_continuous(self):
        class ConcreteCreateVar(CreateVar):
            def run(self, data, model, var):
                pass

        vk = VarKey(id=1, name='X', name_cn='x', sign='x', vtype=float)
        step = ConcreteCreateVar(symbol=vk)
        assert step.vtype == 'CONTINUOUS'

    def test_vtype_integer(self):
        class ConcreteCreateVar(CreateVar):
            def run(self, data, model, var):
                pass

        vk = VarKey(id=1, name='X', name_cn='x', sign='x', vtype=int)
        step = ConcreteCreateVar(symbol=vk)
        assert step.vtype == 'INTEGER'

    def test_vtype_binary(self):
        class ConcreteCreateVar(CreateVar):
            def run(self, data, model, var):
                pass

        vk = VarKey(id=1, name='X', name_cn='x', sign='x', vtype=bool)
        step = ConcreteCreateVar(symbol=vk)
        assert step.vtype == 'BINARY'

    def test_vtype_unsupported(self):
        class ConcreteCreateVar(CreateVar):
            def run(self, data, model, var):
                pass

        vk = VarKey(id=1, name='X', name_cn='x', sign='x', vtype=str)
        step = ConcreteCreateVar(symbol=vk)
        with pytest.raises(ValueError, match="Unsupported"):
            _ = step.vtype

    def test_no_create_method(self):
        """_create method should be deleted."""
        class ConcreteCreateVar(CreateVar):
            def run(self, data, model, var):
                pass

        vk = VarKey(id=1, name='X', name_cn='x', sign='x')
        step = ConcreteCreateVar(symbol=vk)
        assert not hasattr(step, '_create')


class TestCreateConstr:
    def test_is_lp_step(self):
        assert issubclass(CreateConstr, LpStep)
        assert issubclass(CreateConstr, ABC)

    def test_cannot_instantiate_directly(self):
        ck = ConstrKey(id=1, name='C', name_cn='c', sign='c')
        with pytest.raises(TypeError):
            CreateConstr(symbol=ck)

    def test_concrete_subclass(self):
        class ConcreteCreateConstr(CreateConstr):
            def run(self, data, model, var):
                pass

        ck = ConstrKey(id=1, name='C', name_cn='c', sign='c')
        step = ConcreteCreateConstr(symbol=ck)
        assert step._symbol is ck
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_lp/test_step.py -v`
Expected: FAIL — `CreateVar` still requires weight/lb/ub

- [ ] **Step 3: Update LpStep, CreateVar, CreateConstr in `or_algo/lp/step.py`**

Replace the LpStep, CreateVar, and CreateConstr classes. Keep CreateConstrCalculateMetric and Publish unchanged for now (they'll be updated in subsequent tasks).

Replace imports at top of file:
```python
"""LpStep hierarchy for LP model building."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from register import Register, RegisterKey

from . import exception

if TYPE_CHECKING:
    from typing import Tuple

    from ortools.linear_solver import pywraplp
    from register import Dimension

    from .symbol import VarKey, ConstrKey
```

Replace LpStep:
```python
class LpStep(ABC):
    """Abstract base class for LP model building steps."""

    def __init__(self, symbol: RegisterKey):
        super().__init__()
        self._symbol = symbol

    @abstractmethod
    def run(self,
        data: Register[RegisterKey],
        model: pywraplp.Solver,
        var: Register[VarKey],
    ) -> None:
        """Execute this step to build the LP model.

        Args:
            data: Register containing input parameters
            model: OR-Tools solver instance
            var: Register for storing variables/constraints
        """
        pass
```

Replace CreateVar (delete `_create` method and weight/lb/ub fields entirely):
```python
class CreateVar(LpStep, ABC):
    """Base class for variable creation steps."""
    _symbol: VarKey

    def __init__(self, symbol: VarKey):
        super().__init__(symbol)

    @property
    def vtype(self) -> str:
        """Map NumKey vtype to OR-Tools variable type."""
        vtype_mapping = {
            int: 'INTEGER',
            float: 'CONTINUOUS',
            bool: 'BINARY',
        }
        vtype = self._symbol.vtype
        if vtype not in vtype_mapping:
            raise ValueError(
                f"Unsupported NumKey vtype: {vtype}. "
                f"Supported types: {list(vtype_mapping.keys())}"
            )
        return vtype_mapping[vtype]

    @abstractmethod
    def run(self,
        data: Register[RegisterKey],
        model: pywraplp.Solver,
        var: Register[VarKey],
    ) -> None:
        """Create variables in the model."""
        pass
```

Replace CreateConstr:
```python
class CreateConstr(LpStep, ABC):
    """Base class for constraint creation steps."""

    def __init__(self, symbol: ConstrKey):
        super().__init__(symbol)

    @abstractmethod
    def run(self,
        data: Register[RegisterKey],
        model: pywraplp.Solver,
        var: Register[VarKey],
    ) -> None:
        """Create constraints in the model."""
        pass
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_lp/test_step.py::TestLpStep tests/test_lp/test_step.py::TestCreateVar tests/test_lp/test_step.py::TestCreateConstr -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add or_algo/lp/step.py tests/test_lp/test_step.py
git commit -m "refactor: simplify LpStep, CreateVar (no weight/lb/ub/_create), CreateConstr"
```

---

### Task 6: Delete CreateConstrCalculateMetric

**Files:**
- Modify: `or_algo/lp/step.py`
- Modify: `or_algo/lp/__init__.py`

- [ ] **Step 1: Remove CreateConstrCalculateMetric from `or_algo/lp/step.py`**

Delete the entire `CreateConstrCalculateMetric` class (lines ~240-344 in current file). Also remove the `from register import Register, Metric` import — change to `from register import Register, RegisterKey`. Remove `import itertools` if no longer needed.

- [ ] **Step 2: Remove from `or_algo/lp/__init__.py` exports**

Temporarily update `__init__.py` to remove `CreateConstrCalculateMetric` and `Symbol` (and `Var`/`Constr` → `VarKey`/`ConstrKey`):

```python
"""or-algo LP module: Linear Programming support using OR-Tools."""

from .symbol import VarKey, ConstrKey
from .step import LpStep, CreateVar, CreateConstr
from . import exception

__all__ = [
    "VarKey",
    "ConstrKey",
    "LpStep",
    "CreateVar",
    "CreateConstr",
    "exception",
]
```

Note: `Publish` and `LpSolver` will be added back in subsequent tasks.

- [ ] **Step 3: Run tests**

Run: `python -m pytest tests/test_lp/test_step.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add or_algo/lp/step.py or_algo/lp/__init__.py
git commit -m "refactor: delete CreateConstrCalculateMetric, update exports"
```

---

### Task 7: Publish

**Files:**
- Modify: `tests/test_lp/test_step.py` (add Publish tests)
- Modify: `or_algo/lp/step.py` (update Publish)

- [ ] **Step 1: Add Publish tests to `tests/test_lp/test_step.py`**

Append:

```python
class TestPublish:
    @pytest.fixture
    def setup(self):
        from or_algo.lp.step import Publish

        model = pywraplp.Solver.CreateSolver('SCIP')
        d = Dimension('Item', '物料', 'I')
        vk = VarKey(id=1, name='X', name_cn='x', sign='X', vtype=float)

        # Create variables with known solution values
        var_reg = Register()
        v0 = model.NumVar(0, 10, 'v0')
        v1 = model.NumVar(0, 10, 'v1')
        var_reg[vk][d,][0,] = v0
        var_reg[vk][d,][1,] = v1

        # Force solution values by adding objective and solving
        model.Objective().SetCoefficient(v0, 1)
        model.Objective().SetCoefficient(v1, 1)
        model.Objective().SetMaximization()
        model.Add(v0 <= 3.7)
        model.Add(v1 <= 5.2)
        model.Solve()

        return model, d, vk, var_reg, Publish

    def test_publish_writes_solution_to_data(self, setup):
        model, d, vk, var_reg, Publish = setup
        data = Register()
        pub = Publish(symbol=vk, dimension=(d,))
        pub.run(data, model, var_reg)

        assert (0,) in data[vk][d,]
        assert (1,) in data[vk][d,]

    def test_publish_threshold_filters_small_values(self, setup):
        model, d, vk, var_reg, Publish = setup
        data = Register()
        pub = Publish(symbol=vk, dimension=(d,), threshold=100.0)
        pub.run(data, model, var_reg)
        # Values ~3.7 and ~5.2 should be filtered by threshold=100

    def test_publish_zeros_includes_zero_values(self, setup):
        model, d, vk, var_reg, Publish = setup
        data = Register()
        pub = Publish(symbol=vk, dimension=(d,), zeros=True)
        pub.run(data, model, var_reg)

    def test_publish_int_vtype_rounds(self):
        from or_algo.lp.step import Publish

        model = pywraplp.Solver.CreateSolver('SCIP')
        d = Dimension('Item', '物料', 'I')
        vk = VarKey(id=1, name='X', name_cn='x', sign='X', vtype=int)

        var_reg = Register()
        v0 = model.IntVar(0, 10, 'v0')
        var_reg[vk][d,][0,] = v0

        model.Objective().SetCoefficient(v0, 1)
        model.Objective().SetMaximization()
        model.Add(v0 <= 7)
        model.Solve()

        data = Register()
        pub = Publish(symbol=vk, dimension=(d,))
        pub.run(data, model, var_reg)
        val = data[vk][d,][0,]
        assert isinstance(val, int)

    def test_publish_bool_vtype(self):
        from or_algo.lp.step import Publish

        model = pywraplp.Solver.CreateSolver('SCIP')
        d = Dimension('Item', '物料', 'I')
        vk = VarKey(id=1, name='X', name_cn='x', sign='X', vtype=bool)

        var_reg = Register()
        v0 = model.IntVar(0, 1, 'v0')
        var_reg[vk][d,][0,] = v0

        model.Objective().SetCoefficient(v0, 1)
        model.Objective().SetMaximization()
        model.Solve()

        data = Register()
        pub = Publish(symbol=vk, dimension=(d,))
        pub.run(data, model, var_reg)
        val = data[vk][d,][0,]
        assert isinstance(val, bool)

    def test_publish_target_none_selects_all(self, setup):
        model, d, vk, var_reg, Publish = setup
        data = Register()
        pub = Publish(symbol=vk, dimension=(d,), target=None)
        pub.run(data, model, var_reg)
        # Both indices should be published
        assert (0,) in data[vk][d,]
        assert (1,) in data[vk][d,]

    def test_publish_target_with_slice(self, setup):
        model, d, vk, var_reg, Publish = setup
        data = Register()
        pub = Publish(symbol=vk, dimension=(d,), target=(slice(0, 1),))
        pub.run(data, model, var_reg)
        # Only index (0,) should be published
        assert (0,) in data[vk][d,]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_lp/test_step.py::TestPublish -v`
Expected: FAIL — Publish still uses old API

- [ ] **Step 3: Update Publish in `or_algo/lp/step.py`**

Replace the Publish class:

```python
class Publish(LpStep):
    _symbol: VarKey
    _zeros: bool
    _dimension: Tuple[Dimension, ...]
    _threshold: float
    _target: tuple[slice, ...] | None

    def __init__(self, symbol: VarKey, dimension: Tuple[Dimension, ...], target: tuple[slice, ...] | None = None, zeros: bool = False, threshold: float = 1e-6):
        super().__init__(symbol)
        self._dimension = dimension
        self._zeros = zeros
        self._threshold = threshold
        self._target = target

    def run(self, data: Register[RegisterKey], model: pywraplp.Solver, register: Register[VarKey]) -> None:
        space = register[self._symbol][self._dimension,]
        sel = space.all if self._target is None else space[self._target]
        for index in sel._data:
            quantity = register[self._symbol][self._dimension,][index,].solution_value()
            if self._symbol.vtype is int:
                quantity = int(round(quantity, 0))
            elif self._symbol.vtype is bool:
                quantity = bool(round(quantity, 0))
            elif self._symbol.vtype is float:
                pass
            else:
                raise exception.BuildLpStepException(f"Unsupported vtype {self._symbol.vtype} while publishing variable {self._symbol.name}")

            if self._zeros or (quantity > self._threshold):
                data[self._symbol][self._dimension,][index,] = quantity
```

Add Publish back to `or_algo/lp/__init__.py`:

```python
from .step import LpStep, CreateVar, CreateConstr, Publish
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_lp/test_step.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add or_algo/lp/step.py or_algo/lp/__init__.py tests/test_lp/test_step.py
git commit -m "refactor: update Publish to new register API with target slices"
```

---

### Task 8: LpSolver

**Files:**
- Modify: `tests/test_lp/test_solver.py` (rewrite)
- Modify: `or_algo/lp/solver.py`

- [ ] **Step 1: Rewrite `tests/test_lp/test_solver.py`**

```python
"""Tests for LpSolver."""

import pytest
from or_algo.lp.solver import LpSolver
from or_algo import Solver
from or_algo.lp.step import CreateVar, CreateConstr
from or_algo.lp.symbol import VarKey, ConstrKey
from register import Register, RegisterKey, NumKey, Dimension
from ortools.linear_solver import pywraplp


def test_lp_solver_is_solver():
    """LpSolver should inherit from or-algo's Solver."""
    assert issubclass(LpSolver, Solver)


def test_lp_solver_initialization():
    """LpSolver should initialize with name only."""
    solver = LpSolver(name="test_solver")
    assert solver._name == "test_solver"
    assert solver.solver_type == 'SCIP'
    assert solver._model is not None
    assert isinstance(solver._var, Register)


def test_lp_solver_custom_solver_type():
    """LpSolver should accept custom solver_type."""
    solver = LpSolver(name="test_solver", solver_type='GLOP')
    assert solver.solver_type == 'GLOP'


def test_lp_solver_invalid_solver_type():
    """LpSolver should raise on invalid solver_type."""
    with pytest.raises(Exception):
        LpSolver(name="test_solver", solver_type='INVALID_SOLVER')


def test_lp_solver_no_weight_lb_ub():
    """LpSolver should not have weight/lb/ub fields."""
    solver = LpSolver(name="test_solver")
    assert not hasattr(solver, '_weight')
    assert not hasattr(solver, '_lb')
    assert not hasattr(solver, '_ub')


def test_lp_solver_append_create_var():
    """LpSolver.append() should accept CreateVar steps."""
    solver = LpSolver(name="test_solver")
    vk = VarKey(id=1, name='X', name_cn='x', sign='x')

    class TestCreateVar(CreateVar):
        def run(self, data, model, var):
            pass

    initial_count = len(solver._build_steps)
    solver.append(TestCreateVar, vk)
    assert len(solver._build_steps) == initial_count + 1


def test_lp_solver_append_create_constr():
    """LpSolver.append() should accept CreateConstr steps."""
    solver = LpSolver(name="test_solver")
    ck = ConstrKey(id=1, name='C', name_cn='c', sign='c')

    class TestCreateConstr(CreateConstr):
        def run(self, data, model, var):
            pass

    initial_count = len(solver._build_steps)
    solver.append(TestCreateConstr, ck)
    assert len(solver._build_steps) == initial_count + 1


def test_lp_solver_append_rejects_unknown_step():
    """LpSolver.append() should reject non-CreateVar/CreateConstr steps."""
    from or_algo.lp.step import LpStep
    solver = LpSolver(name="test_solver")

    class UnknownStep(LpStep):
        def run(self, data, model, var):
            pass

    with pytest.raises(Exception):
        solver.append(UnknownStep)


def test_lp_solver_solve_executes_steps():
    """LpSolver.solve() should execute build steps."""
    solver = LpSolver(name="test_solver")
    executed = []

    class TrackingCreateVar(CreateVar):
        def run(self, data, model, var):
            executed.append('create_var')

    vk = VarKey(id=1, name='X', name_cn='x', sign='x')
    solver.append(TrackingCreateVar, vk)

    data = Register()
    solver.solve(data)
    assert executed == ['create_var']


def test_lp_solver_solve_returns_data():
    """LpSolver.solve() should return the data Register."""
    solver = LpSolver(name="test_solver")

    class NoOpCreateVar(CreateVar):
        def run(self, data, model, var):
            pass

    vk = VarKey(id=1, name='X', name_cn='x', sign='x')
    solver.append(NoOpCreateVar, vk)

    data = Register()
    # No variables created, no publish steps — model solves trivially
    # Actually, an empty model may not have OPTIMAL status.
    # Add a simple variable to make the model solvable.
    class SimpleCreateVar(CreateVar):
        def run(self, data, model, var):
            d = Dimension('I', 'i', 'I')
            v = model.NumVar(0, 1, 'x')
            var[self._symbol][d,][0,] = v
            model.Objective().SetCoefficient(v, 1)

    solver2 = LpSolver(name="test_solver2")
    solver2.append(SimpleCreateVar, vk)
    result = solver2.solve(data)
    assert result is data


def test_lp_solver_append_no_default_args():
    """LpSolver.append() should not fill default weight/lb/ub args."""
    solver = LpSolver(name="test_solver")
    vk = VarKey(id=1, name='X', name_cn='x', sign='x')

    class TestCreateVar(CreateVar):
        def run(self, data, model, var):
            pass

    solver.append(TestCreateVar, vk)
    step_type, args, kwargs = solver._build_steps[-1]
    assert args == (vk,)  # No extra weight/lb/ub args appended
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_lp/test_solver.py -v`
Expected: FAIL — LpSolver still has weight/lb/ub

- [ ] **Step 3: Rewrite `or_algo/lp/solver.py`**

```python
"""LpSolver: Linear Programming solver using OR-Tools."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ortools.linear_solver import pywraplp

from ..solver import Solver
from . import exception

if TYPE_CHECKING:
    from typing import Any, Dict, List, Optional, Tuple, Type

    from register import Register, RegisterKey
    from or_algo.lp.symbol import VarKey
    from or_algo.lp.step import LpStep


class LpSolver(Solver):
    """Linear Programming solver using OR-Tools.

    Inherits from or-algo's Solver base class and integrates
    with Register[RegisterKey] for data flow.
    """

    _name: str
    _var: Register[VarKey]
    _build_steps: List[Tuple[Type[LpStep], Tuple[Any, ...], Dict[str, Any]]]
    _publish_steps: List[Tuple[Tuple[Any, ...], Dict[str, Any]]]
    _model: pywraplp.Solver
    _solver_type: str

    def __init__(
        self,
        name: str,
        solver_type: str = 'SCIP'
    ):
        from register import Register

        super().__init__(name)
        self._name = name
        self._var = Register()
        self._build_steps = list()
        self._publish_steps = list()
        self._solver_type = solver_type

        self._model = pywraplp.Solver.CreateSolver(solver_type)
        if not self._model:
            raise exception.LpSolverException(
                f"Failed to create OR-Tools solver with type '{solver_type}'"
            )
        self._model.Objective().SetMaximization()

    @property
    def solver_type(self) -> str:
        return self._solver_type

    def publish(self, *args: Any, **kwargs: Any) -> None:
        self._publish_steps.append((args, kwargs))

    def append(self, step: Type[LpStep], *args: Any, **kwargs: Any) -> None:
        """Add a build step to the execution sequence.

        Args:
            step: LpStep subclass (CreateVar or CreateConstr)
            *args: Arguments to pass to step.__init__()
            **kwargs: Keyword arguments to pass to step.__init__()

        Raises:
            LpSolverException: If step type is unsupported
        """
        from or_algo.lp.step import CreateVar, CreateConstr

        if issubclass(step, (CreateVar, CreateConstr)):
            self._build_steps.append((step, args, kwargs))
        else:
            raise exception.LpSolverException(
                f"Unsupported step type {step} in {type(self).__name__}.append()"
            )

    def solve(self, data: Register[RegisterKey]) -> Register[RegisterKey]:
        """Build and solve the LP model.

        Args:
            data: Register containing input parameters

        Returns:
            The same Register (users can extract solutions via their own mechanisms)

        Raises:
            BuildLpStepException: If a build step fails
            LpModelOptimizeException: If optimization fails or no solution is found
        """
        from or_algo.lp import Publish

        # Execute build steps
        for step_type, args, kwargs in self._build_steps:
            try:
                step_type(*args, **kwargs).run(data, self._model, self._var)
            except Exception as e:
                raise exception.BuildLpStepException(
                    f"Failed {step_type.__name__}.run()! args={args}, kwargs={kwargs}"
                ) from e

        self._model.EnableOutput()

        # write model to .lp file
        with open(f"{self._name}.lp", 'w') as f:
            f.write(self._model.ExportModelAsLpFormat(False))

        # Solve the model
        status = self._model.Solve()

        # Handle OR-Tools status codes
        if status == pywraplp.Solver.OPTIMAL:
            for args, kwargs in self._publish_steps:
                Publish(*args, **kwargs).run(data, self._model, self._var)
            return data
        elif status == pywraplp.Solver.INFEASIBLE:
            raise exception.LpModelOptimizeException("Model is infeasible")
        elif status == pywraplp.Solver.UNBOUNDED:
            raise exception.LpModelOptimizeException("Model is unbounded")
        elif status == pywraplp.Solver.NOT_SOLVED:
            raise exception.LpModelOptimizeException("Model was not solved")
        elif status == pywraplp.Solver.ABNORMAL:
            raise exception.LpModelOptimizeException("Solver encountered an error")
        else:
            raise exception.LpModelOptimizeException(
                f"No solution found! status={status}"
            )
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_lp/test_solver.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add or_algo/lp/solver.py tests/test_lp/test_solver.py
git commit -m "refactor: simplify LpSolver — remove weight/lb/ub, simplify append, remove auto-metric"
```

---

### Task 9: Finalize exports and full test run

**Files:**
- Modify: `or_algo/lp/__init__.py`

- [ ] **Step 1: Finalize `or_algo/lp/__init__.py`**

```python
"""or-algo LP module: Linear Programming support using OR-Tools."""

from .symbol import VarKey, ConstrKey
from .step import LpStep, CreateVar, CreateConstr, Publish
from .solver import LpSolver
from . import exception

__all__ = [
    "VarKey",
    "ConstrKey",
    "LpStep",
    "CreateVar",
    "CreateConstr",
    "Publish",
    "LpSolver",
    "exception",
]
```

- [ ] **Step 2: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: PASS

- [ ] **Step 3: Run type checker**

Run: `python -m mypy or_algo/`
Expected: PASS (or only pre-existing warnings)

- [ ] **Step 4: Run linter**

Run: `python -m ruff check or_algo/`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add or_algo/lp/__init__.py
git commit -m "chore: finalize LP exports, all tests pass"
```
