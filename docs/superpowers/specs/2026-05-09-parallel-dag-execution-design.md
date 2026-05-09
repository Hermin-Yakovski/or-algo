# Parallel DAG-Based Solver Execution

## Overview

Add parallel execution capability to `Algorithm` using DAG-based orchestration with lazy dependency resolution. Each solver receives a pickled copy of the `Register`, runs in a separate process, and returns its modified `Register`. Results are merged back into the main `Register` as tasks complete, enabling dependent tasks to see their predecessors' output.

## Motivation

`Algorithm.solve()` executes solvers sequentially. For workflows with independent solvers, this wastes CPU cycles. Parallel execution allows independent solvers to run simultaneously while respecting dependencies.

## Key Design Decisions

**Pickle-and-merge approach:** Instead of using `SharedRegister` with `Manager.dict()` (which has compatibility issues with Register's nested structure), we use regular `Register` instances. Each worker receives a pickled copy, modifies it, and returns it. The main process merges results back as tasks complete.

**No SharedRegister class:** Removed the `SharedRegister` class entirely. `parallel_solve()` accepts the same `Register[Parameter]` type as `solve()`.

**In-place modification:** `parallel_solve()` modifies the input `Register` in place (like `solve()`) and returns `None`.

## API Design

### Modified `Algorithm.parallel_solve()`

```python
def parallel_solve(
    self,
    reg: Register[Parameter],
    executor: ProcessPoolExecutor
) -> None:
```

- `reg`: Register containing input parameters; solutions are merged back into this same Register
- `executor`: ProcessPoolExecutor for parallel execution
- Returns: `None` (modifies `reg` in place)
- Raises: `OrAlgoException` on cycle detection or solver failure

### Usage Example

```python
from concurrent.futures import ProcessPoolExecutor
from or_algo import Algorithm
from register import Register, Parameter

# Build DAG
algo = Algorithm()
id1 = algo.append(SolverA)
id2 = algo.append(SolverB)  # Independent of A
id3 = algo.append(SolverC, after=[id1])  # Depends on A
id4 = algo.append(SolverD, after=[id1, id2])  # Depends on A and B

# Sequential (unchanged)
algo.solve(reg)

# Parallel
reg = Register[Parameter]()
reg[Id][(Index,)][(0,)] = input_value

with ProcessPoolExecutor(max_workers=4) as executor:
    algo.parallel_solve(reg, executor)

# Access results
result = reg[Id][(Index,)][(0,)]
```

## Components

### 1. Modified `SolverTask.execute()` (`or_algo/task.py`)

```python
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

**Change:** Now returns `Register[Parameter]` (the result from `solver.solve()`).

### 2. New `Algorithm._merge_register()` (`or_algo/algorithm.py`)

```python
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

**Note:** This is a temporary solution. Future work will add `Register.update()` API to the Register class.

### 3. Modified `Algorithm.parallel_solve()` (`or_algo/algorithm.py`)

**Execution algorithm:**

1. **Validate DAG**: Run `_detect_cycle()` - raise if cycle found
2. **Build tasks**: Wrap each solver with `SolverTask`
3. **Initial submission**: Submit tasks with no dependencies, each gets pickle copy of `reg`
4. **Main loop**:
   - Wait for any future to complete via `as_completed()`
   - Get `result_reg` from `future.result()`
   - Merge `result_reg` into main `reg` via `_merge_register()`
   - Add to `completed` set
   - Find newly-ready tasks (all deps in `completed`)
   - Submit ready tasks with pickle copy of UPDATED `reg` (contains previous merges)
5. **Return:** `None` (main `reg` has been modified in place)

**Code snippet:**
```python
# Submit ready tasks with pickle copy
reg_copy = pickle.loads(pickle.dumps(reg))
future = executor.submit(task.execute, reg_copy)
futures[future] = task_id

# When future completes
for future in as_completed(futures.keys()):
    task_id = futures.pop(future)
    result_reg = future.result()
    self._merge_register(reg, result_reg)
    completed.add(task_id)

# Submit next tasks with updated data
for ready_id in self._get_ready_tasks(tasks, completed):
    reg_copy = pickle.loads(pickle.dumps(reg))
    new_future = executor.submit(tasks[ready_id].execute, reg_copy)
    futures[new_future] = ready_id
```

## Data Flow Example

**Diamond pattern: A → [B, C] → D**

```
Initial state:
  reg = {"input": 1}

Step 1: Submit A (no dependencies)
  reg_copy_A = pickle.loads(pickle.dumps(reg))  # {"input": 1}
  future_A = executor.submit(task_A.execute, reg_copy_A)

Step 2: A completes
  result_A = future_A.result()  # {"input": 1, "A_output": 10}
  _merge_register(reg, result_A)
  # reg = {"input": 1, "A_output": 10}
  completed = {A}

Step 3: Submit B and C (both depend on A, both get updated reg)
  reg_copy_B = pickle.loads(pickle.dumps(reg))  # {"input": 1, "A_output": 10}
  reg_copy_C = pickle.loads(pickle.dumps(reg))  # {"input": 1, "A_output": 10}
  future_B = executor.submit(task_B.execute, reg_copy_B)
  future_C = executor.submit(task_C.execute, reg_copy_C)

Step 4: B completes
  result_B = future_B.result()  # {"input": 1, "A_output": 10, "B_output": 20}
  _merge_register(reg, result_B)
  # reg = {"input": 1, "A_output": 10, "B_output": 20}

Step 5: C completes
  result_C = future_C.result()  # {"input": 1, "A_output": 10, "C_output": 30}
  _merge_register(reg, result_C)
  # reg = {"input": 1, "A_output": 10, "B_output": 20, "C_output": 30}
  completed = {A, B, C}

Step 6: Submit D (depends on B and C)
  reg_copy_D = pickle.loads(pickle.dumps(reg))  # Has A, B, C outputs
  future_D = executor.submit(task_D.execute, reg_copy_D)

Step 7: D completes, merge results
  # reg now has all outputs
```

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Cycle detected | `OrAlgoException` immediately, no execution |
| Solver fails (raises exception) | Cancel pending futures, raise `OrAlgoException` with task ID and original exception chained |
| Executor full | Blocks until worker available (executor manages this) |
| Pickle/unpickle fails | `OrAlgoException` with original exception chained |

## Implementation Scope

**Phase 1 (this spec):**
- Core `parallel_solve()` with pickle-and-merge approach
- Modified `SolverTask.execute()` to return Register
- New `_merge_register()` method in Algorithm
- Update tests to use Register instead of SharedRegister

**Removed from original design:**
- `SharedRegister` class (no longer needed)
- `Manager.dict()` backend (replaced with pickle/merge)

**Out of scope:**
- Dynamic executor management (caller provides executor)
- Async/non-blocking API
- Progress callbacks
- Distributed execution (beyond single machine)
- Collision detection for overlapping keys (assumes solvers write to different keys)

## Dependencies

- `concurrent.futures.ProcessPoolExecutor` - Python standard library
- `pickle` - Python standard library
- `register` package - Existing dependency

## Files to Modify

1. **`or_algo/algorithm.py`**
   - Change `parallel_solve()` signature: remove `SharedRegister`, use `Register[Parameter]`
   - Change return type to `None`
   - Add `_merge_register()` method
   - Update main loop to capture `future.result()` and merge

2. **`or_algo/task.py`**
   - Change `execute()` signature to return `Register[Parameter]`
   - Return `solver.solve(reg)` instead of calling it without capturing result

3. **`tests/test_algorithm_parallel.py`**
   - Update to use `Register` instead of `SharedRegister`
   - Remove `Manager` and `Manager.dict()` usage
   - Test merge behavior directly
   - Verify dependent tasks receive merged results

## Files to Remove

- **`or_algo/shared_register.py`** - No longer needed
- **`tests/test_shared_register.py`** - No longer needed

## Testing Strategy

Test file: `tests/test_algorithm_parallel.py`

1. **Sequential baseline**: Verify `solve()` unchanged
2. **Independent solvers**: All run in parallel
3. **Linear chain**: A→B→C→D (sequential via dependencies)
4. **Diamond pattern**: A→[B, C]→D (B and C parallel, D sees both results)
5. **Complex DAG**: Multiple branches merging
6. **Cycle detection**: Verify graceful failure
7. **Solver failure**: Verify cancellation and error propagation
8. **Empty algorithm**: No solvers appended
9. **Single solver**: No dependencies
10. **Merge behavior**: Verify dependent tasks see predecessors' output
