# Parallel DAG-Based Solver Execution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add parallel execution capability to Algorithm using pickle-and-merge approach with DAG-based lazy dependency resolution.

**Architecture:** Each solver receives a pickled Register copy, runs in separate process, returns modified Register. Results are merged back into main Register as tasks complete. Dependent tasks receive Register with predecessors' results already merged.

**Tech Stack:** Python standard library (concurrent.futures.ProcessPoolExecutor, pickle), register package, pytest

---

### Task 1: Modify SolverTask.execute() to return Register

**Files:**
- Modify: `or_algo/task.py`

- [ ] **Step 1: Write failing test for execute() return value**

```python
# tests/test_task.py - add to existing file
import pickle
from register import Register, Parameter

def test_solver_task_execute_returns_register():
    """Test that execute() returns the modified Register."""
    task = SolverTask(DummySolver, (), {}, [], 1)
    reg = Register[Parameter]()
    reg._data["test"] = "input"

    result_reg = task.execute(reg)

    assert result_reg is reg  # Returns the same Register instance
    assert isinstance(result_reg, Register)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_task.py::test_solver_task_execute_returns_register -v`
Expected: FAIL with "execute() takes 2 positional arguments but 3 were given" or similar (execute doesn't return anything)

- [ ] **Step 3: Modify execute() to capture and return Register result**

```python
# or_algo/task.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_task.py::test_solver_task_execute_returns_register -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add or_algo/task.py tests/test_task.py
git commit -m "feat: modify SolverTask.execute() to return Register"
```

---

### Task 2: Add Algorithm._merge_register() method

**Files:**
- Modify: `or_algo/algorithm.py`
- Test: `tests/test_algorithm.py`

- [ ] **Step 1: Write failing test for _merge_register()**

```python
# tests/test_algorithm.py - add to existing file
def test_algorithm_merge_register():
    """Test that _merge_register() merges source into target."""
    from register import Register, Parameter, Id, Index

    algo = Algorithm()

    # Create source and target registers
    target = Register[Parameter]()
    target[Id][(Index,)][(0,)] = "target_value"

    source = Register[Parameter]()
    source[Id][(Index,)][(1,)] = "source_value"
    source[Id][(Index,)][(0,)] = "overwrite_value"

    # Merge source into target
    algo._merge_register(target, source)

    # Target should have both values, with source overwriting
    assert target[Id][(Index,)][(0,)] == "overwrite_value"
    assert target[Id][(Index,)][(1,)] == "source_value"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_algorithm.py::test_algorithm_merge_register -v`
Expected: FAIL with "AttributeError: 'Algorithm' object has no attribute '_merge_register'"

- [ ] **Step 3: Implement _merge_register() method**

```python
# or_algo/algorithm.py - add method to Algorithm class
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
            target[var][dimensions] = source[var][dimensions]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_algorithm.py::test_algorithm_merge_register -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add or_algo/algorithm.py tests/test_algorithm.py
git commit -m "feat: add _merge_register() method to Algorithm"
```

---

### Task 3: Modify parallel_solve() signature and basic structure

**Files:**
- Modify: `or_algo/algorithm.py`

- [ ] **Step 1: Update parallel_solve() signature**

Change from:
```python
def parallel_solve(
    self,
    data: SharedRegister[Parameter],
    executor: ProcessPoolExecutor
) -> SharedRegister[Parameter]:
```

To:
```python
def parallel_solve(
    self,
    reg: Register[Parameter],
    executor: ProcessPoolExecutor
) -> None:
```

- [ ] **Step 2: Remove SharedRegister import**

Remove this line from imports:
```python
from .shared_register import SharedRegister
```

- [ ] **Step 3: Update docstring**

```python
def parallel_solve(
    self,
    reg: Register[Parameter],
    executor: ProcessPoolExecutor
) -> None:
    """Execute solvers in parallel using DAG-based lazy resolution.

    Args:
        reg: Register containing input parameters; solutions are
             merged back into this same Register.
        executor: ProcessPoolExecutor for parallel execution

    Raises:
        OrAlgoException: If cycle detected or any solver fails
    """
```

- [ ] **Step 4: Commit**

```bash
git add or_algo/algorithm.py
git commit -m "refactor: update parallel_solve() signature to use Register"
```

---

### Task 4: Update parallel_solve() to capture future results

**Files:**
- Modify: `or_algo/algorithm.py`

- [ ] **Step 1: Modify future completion handling to capture result**

Find this code in parallel_solve():
```python
try:
    future.result()
    completed.add(task_id)
except Exception as e:
```

Change to:
```python
try:
    result_reg = future.result()
    self._merge_register(reg, result_reg)
    completed.add(task_id)
except Exception as e:
```

- [ ] **Step 2: Commit**

```bash
git add or_algo/algorithm.py
git commit -m "feat: capture and merge Register results from completed futures"
```

---

### Task 5: Update parallel_solve() to pass pickle copies to workers

**Files:**
- Modify: `or_algo/algorithm.py`

- [ ] **Step 1: Add pickle import**

Add to top of file:
```python
import pickle
```

- [ ] **Step 2: Modify initial task submission**

Find this code:
```python
for task_id in self._get_ready_tasks(tasks, completed):
    task = tasks[task_id]
    future = executor.submit(task.execute, data)
    futures[future] = task_id
```

Change to:
```python
for task_id in self._get_ready_tasks(tasks, completed):
    task = tasks[task_id]
    reg_copy = pickle.loads(pickle.dumps(reg))
    future = executor.submit(task.execute, reg_copy)
    futures[future] = task_id
```

- [ ] **Step 3: Modify newly-ready task submission**

Find this code:
```python
for ready_id in self._get_ready_tasks(tasks, completed):
    if ready_id not in completed and ready_id not in futures.values():
        ready_task = tasks[ready_id]
        new_future = executor.submit(ready_task.execute, data)
        futures[new_future] = ready_id
```

Change to:
```python
for ready_id in self._get_ready_tasks(tasks, completed):
    if ready_id not in completed and ready_id not in futures.values():
        ready_task = tasks[ready_id]
        reg_copy = pickle.loads(pickle.dumps(reg))
        new_future = executor.submit(ready_task.execute, reg_copy)
        futures[new_future] = ready_id
```

- [ ] **Step 4: Change return statement**

Find:
```python
return data
```

Change to:
```python
return  # None, data is modified in place
```

Or just remove the return statement.

- [ ] **Step 5: Commit**

```bash
git add or_algo/algorithm.py
git commit -m "feat: pass pickle copies of Register to worker processes"
```

---

### Task 6: Update parallel execution tests to use Register

**Files:**
- Modify: `tests/test_algorithm_parallel.py`

- [ ] **Step 1: Remove SharedRegister import**

Remove:
```python
from or_algo.shared_register import SharedRegister
```

- [ ] **Step 2: Update all test functions to use Register**

Replace all instances of:
```python
data = SharedRegister[Parameter]()
```

With:
```python
reg = Register[Parameter]()
```

- [ ] **Step 3: Update parallel_solve() calls**

Replace all instances of:
```python
algo.parallel_solve(data, executor)
```

With:
```python
algo.parallel_solve(reg, executor)
```

- [ ] **Step 4: Remove SimpleDictSolver and use proper Register access**

Remove the SimpleDictSolver class and replace test assertions to use Register's nested structure.

For example, change:
```python
def test_parallel_solve_returns_same_register():
    algo = Algorithm()
    algo.append(SimpleDictSolver)
    data = SharedRegister[Parameter]()
    with ProcessPoolExecutor(max_workers=2) as executor:
        result = algo.parallel_solve(data, executor)
    assert data._data.get("test") == "done"
```

To:
```python
def test_parallel_solve_returns_same_register():
    class ResultSolver(Solver):
        def solve(self, data: Register[Parameter]) -> Register[Parameter]:
            data[Id][(Index,)][(0,)] = "done"
            return data

    algo = Algorithm()
    algo.append(ResultSolver)
    reg = Register[Parameter]()
    with ProcessPoolExecutor(max_workers=2) as executor:
        algo.parallel_solve(reg, executor)
    assert reg[Id][(Index,)][(0,)] == "done"
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_algorithm_parallel.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add tests/test_algorithm_parallel.py
git commit -m "test: update parallel tests to use Register instead of SharedRegister"
```

---

### Task 7: Add test for merge behavior with dependencies

**Files:**
- Test: `tests/test_algorithm_parallel.py`

- [ ] **Step 1: Write test for dependent tasks seeing merged results**

```python
# tests/test_algorithm_parallel.py - add new test
def test_parallel_solve_dependent_tasks_see_merged_results():
    """Test that dependent tasks receive Register with predecessors' results."""
    order = []

    class OrderAndWriteSolver(Solver):
        def __init__(self, name: str, write_key: str = None, read_key: str = None):
            super().__init__()
            self.name = name
            self.write_key = write_key
            self.read_key = read_key

        def solve(self, data: Register[Parameter]) -> Register[Parameter]:
            order.append(self.name)

            # Read from predecessor if specified
            if self.read_key:
                param, dim, idx = self.read_key
                value = data[param][dim][idx]
                data[Id][(Index,)][(0,)] = f"{self.name}_saw_{value}"

            # Write our result if specified
            if self.write_key:
                param, dim, idx = self.write_key
                data[param][dim][idx] = self.name

            return data

    algo = Algorithm()
    # Task A writes "A"
    id_a = algo.append(OrderAndWriteSolver, "A", (Id, (Index,), (0,)))
    # Task B reads what A wrote, writes "B"
    id_b = algo.append(OrderAndWriteSolver, "B", (Id, (Index,), (1,)), (Id, (Index,), (0,)), after=[id_a])

    reg = Register[Parameter]()

    with ProcessPoolExecutor(max_workers=2) as executor:
        algo.parallel_solve(reg, executor)

    # Verify A ran before B
    assert order.index("A") < order.index("B")

    # Verify B saw A's output (B merged A's result)
    assert reg[Id][(Index,)][(0,)] == "B_saw_A"
    assert reg[Id][(Index,)][(1,)] == "B"
```

- [ ] **Step 2: Run test to verify it passes**

Run: `pytest tests/test_algorithm_parallel.py::test_parallel_solve_dependent_tasks_see_merged_results -v`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_algorithm_parallel.py
git commit -m "test: add test for dependent tasks seeing merged results"
```

---

### Task 8: Remove SharedRegister files

**Files:**
- Remove: `or_algo/shared_register.py`
- Remove: `tests/test_shared_register.py`

- [ ] **Step 1: Remove SharedRegister implementation**

```bash
git rm or_algo/shared_register.py
```

- [ ] **Step 2: Remove SharedRegister tests**

```bash
git rm tests/test_shared_register.py
```

- [ ] **Step 3: Update __init__.py to remove SharedRegister export**

Find and remove in `or_algo/__init__.py`:
```python
from .shared_register import SharedRegister
```

And remove from `__all__`:
```python
"SharedRegister",
```

- [ ] **Step 4: Verify import still works**

Run: `python -c "from or_algo import Algorithm, SolverTask; print('Import successful')"`
Expected: "Import successful"

- [ ] **Step 5: Commit**

```bash
git add or_algo/__init__.py
git commit -m "refactor: remove SharedRegister class and tests"
```

---

### Task 9: Update documentation

**Files:**
- Modify: `README.md` (if it mentions parallel_solve)

- [ ] **Step 1: Check if README mentions parallel_solve or SharedRegister**

```bash
grep -n "parallel_solve\|SharedRegister" README.md
```

- [ ] **Step 2: Update README if needed**

If found, update to reflect new API using Register instead of SharedRegister.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: update README for new parallel_solve API"
```

---

## Self-Review

**1. Spec coverage:**
- ✅ SolverTask.execute() returns Register - Task 1
- ✅ Algorithm._merge_register() - Task 2
- ✅ parallel_solve() signature change - Task 3
- ✅ Capture future results - Task 4
- ✅ Pass pickle copies - Task 5
- ✅ Update tests - Task 6
- ✅ Test merge behavior - Task 7
- ✅ Remove SharedRegister - Task 8
- ✅ Update docs - Task 9

**2. Placeholder scan:** No TBD, TODO, or incomplete sections found.

**3. Type consistency:**
- `reg: Register[Parameter]` used consistently throughout
- `parallel_solve()` returns `None` consistently
- `execute()` returns `Register[Parameter]` consistently
- Method signatures match across tasks

**Plan is complete and ready for execution.**
