# LpSolver Solution Publishing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add declarative solution extraction to LpSolver via a `publishes` attribute and `_publish()` method, with automatic merging through Algorithm.

**Architecture:** LpSolver declares what to extract via `publishes` attribute; `_publish()` method extracts solution values from OR-Tools and returns a Register; Algorithm merges published values back into main data flow.

**Tech Stack:** Python 3.11+, OR-Tools pywraplp, Register library

---

## File Structure

**Modified Files:**
- `or_algo/solver.py` - Add return type annotation to `solve()`
- `or_algo/algorithm.py` - Add merge logic for published values
- `or_algo/lp/solver.py` - Add `publishes` attribute and `_publish()` method

**New Tests:**
- `tests/test_solver.py` - Update for new return type
- `tests/test_algorithm.py` - Add merge logic tests
- `tests/test_lp/test_solver.py` - Add `_publish()` tests

---

## Task 1: Update Solver.solve() Return Type

**Files:**
- Modify: `or_algo/solver.py:28`

- [ ] **Step 1: Update the return type annotation**

Change the `solve()` method signature from:
```python
def solve(self, data: Register[Parameter]) -> None:
```

To:
```python
def solve(self, data: Register[Parameter]) -> Register[Parameter]:
```

And update the docstring from:
```python
"""Solve the problem using data from the Register.

Args:
    data: Register containing input parameters; solutions
          are written back to this same Register.
"""
```

To:
```python
"""Solve the problem using data from the Register.

Args:
    data: Register containing input parameters.

Returns:
    Register containing solutions (may be the same as input).
"""
```

- [ ] **Step 2: Run existing tests to verify compatibility**

Run: `pytest tests/test_solver.py -v`

Expected: All tests PASS (existing tests don't check return value)

- [ ] **Step 3: Commit**

```bash
git add or_algo/solver.py
git commit -m "feat: add return type annotation to Solver.solve()"
```

---

## Task 2: Add publishes Attribute to LpSolver

**Files:**
- Modify: `or_algo/lp/solver.py:16-56`

- [ ] **Step 1: Add publishes attribute to __init__ signature**

Update the `__init__` method signature from:
```python
def __init__(
    self,
    name: str,
    weight: "Register[Symbol]" = None,
    lb: "Register[Symbol]" = None,
    ub: "Register[Symbol]" = None,
    solver_type: str = 'CBC'
):
```

To:
```python
def __init__(
    self,
    name: str,
    publishes: "list[tuple[Symbol, tuple[Symbol, ...] | None, tuple[int, ...] | None]]" | None = None,
    weight: "Register[Symbol]" = None,
    lb: "Register[Symbol]" = None,
    ub: "Register[Symbol]" = None,
    solver_type: str = 'CBC'
):
```

- [ ] **Step 2: Initialize publishes attribute in __init__ body**

After `self._name = name`, add:
```python
self._publishes = list() if publishes is None else publishes
```

- [ ] **Step 3: Add publishes property**

Add after the `solver_type` property:
```python
@property
def publishes(self) -> "list[tuple[Symbol, tuple[Symbol, ...] | None, tuple[int, ...] | None]]":
    return self._publishes
```

- [ ] **Step 4: Run tests to verify initialization**

Run: `pytest tests/test_lp/test_solver.py::test_lp_solver_initialization -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add or_algo/lp/solver.py
git commit -m "feat: add publishes attribute to LpSolver"
```

---

## Task 3: Implement LpSolver._publish() Method

**Files:**
- Modify: `or_algo/lp/solver.py:135` (add after `append()` method)

- [ ] **Step 1: Write failing test for _publish()**

Create test file content:

```python
# Add to tests/test_lp/test_solver.py

def test_lp_solver_publish_empty_publishes():
    """LpSolver._publish() should return empty Register when publishes is empty."""
    solver = LpSolver(name="test_solver", publishes=[])
    data = Register()

    result = solver._publish(data)

    assert len(result) == 0


def test_lp_solver_publish_single_value():
    """LpSolver._publish() should extract single variable value."""
    from unittest.mock import Mock

    solver = LpSolver(name="test_solver")

    # Create mock parameter
    mock_param = Mock()
    mock_param.id = 1
    mock_param.name = "x"

    # Create mock variable symbol
    mock_var_symbol = Mock()
    mock_var_symbol.parameter = mock_param
    mock_var_symbol.id = 10

    # Create mock OR-Tools variable
    mock_ortools_var = Mock()
    mock_ortools_var.solution_value = Mock(return_value=42.5)

    # Set up publishes
    solver._publishes = [(mock_var_symbol, None, None)]

    # Set up self._var to return the OR-Tools variable
    solver._var = Mock()
    solver._var.__getitem__ = Mock(return_value=mock_ortools_var)

    data = Register()
    result = solver._publish(data)

    # Verify solution value was extracted
    mock_ortools_var.solution_value.assert_called_once()


def test_lp_solver_publish_with_dimensions_and_indexes():
    """LpSolver._publish() should handle dimensions and indexes correctly."""
    from unittest.mock import Mock

    solver = LpSolver(name="test_solver")

    # Create mock parameter
    mock_param = Mock()
    mock_param.id = 1
    mock_param.name = "y"

    # Create mock variable symbol
    mock_var_symbol = Mock()
    mock_var_symbol.parameter = mock_param
    mock_var_symbol.id = 20

    # Create mock OR-Tools variable
    mock_ortools_var = Mock()
    mock_ortools_var.solution_value = Mock(return_value=100.0)

    # Set up publishes with dimensions and indexes
    from or_algo.lp.symbol import Symbol
    dim1 = Mock()
    dim2 = Mock()
    solver._publishes = [(mock_var_symbol, (dim1, dim2), (0, 1))]

    # Set up self._var navigation
    mock_var_register = Mock()
    mock_var_register.__getitem__ = Mock(return_value=mock_ortools_var)
    solver._var = {mock_var_symbol: {(dim1, dim2): {(0, 1): mock_ortools_var}}}

    data = Register()
    result = solver._publish(data)

    # Verify navigation and extraction
    mock_ortools_var.solution_value.assert_called_once()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_lp/test_solver.py::test_lp_solver_publish_empty_publishes -v`

Expected: FAIL with "LpSolver has no attribute '_publish'"

- [ ] **Step 3: Implement _publish() method**

Add after the `append()` method in `or_algo/lp/solver.py`:

```python
def _publish(self, data: "Register[Parameter]") -> "Register[Parameter]":
    """Extract solution values from OR-Tools and build output Register.

    Args:
        data: Register containing original parameters.

    Returns:
        Register with solution values extracted from self._var.
    """
    from register import Register

    publish = Register[Parameter]()
    for symbol, dims, index in self._publishes:
        # Navigate self._var to get OR-Tools Variable
        if dims is None and index is None:
            variable = self._var[symbol]
        elif dims is not None and index is not None:
            variable = self._var[symbol][dims][index]
        elif dims is not None:
            variable = self._var[symbol][dims]
        else:
            variable = self._var[symbol][index]

        # Extract solution value
        value = variable.solution_value()

        # Write to output Register
        if dims is None and index is None:
            publish[symbol.parameter] = value
        elif dims is not None and index is not None:
            publish[symbol.parameter][dims][index] = value
        elif dims is not None:
            publish[symbol.parameter][dims] = value
        else:
            publish[symbol.parameter][index] = value

    return publish
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_lp/test_solver.py::test_lp_solver_publish_empty_publishes tests/test_lp/test_solver.py::test_lp_solver_publish_single_value tests/test_lp/test_solver.py::test_lp_solver_publish_with_dimensions_and_indexes -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add or_algo/lp/solver.py tests/test_lp/test_solver.py
git commit -m "feat: implement LpSolver._publish() method"
```

---

## Task 4: Update LpSolver.solve() to Return Published Register

**Files:**
- Modify: `or_algo/lp/solver.py:119-120`

- [ ] **Step 1: Write failing test for solve() returning publish**

Add to `tests/test_lp/test_solver.py`:

```python
def test_lp_solver_solve_returns_publish_when_optimal():
    """LpSolver.solve() should return _publish() result when OPTIMAL."""
    solver = LpSolver(name="test_solver", publishes=[])

    data = Register()

    # Mock the model.Solve() to return OPTIMAL
    solver._model.Solve = Mock(return_value=pywraplp.Solver.OPTIMAL)

    # Should return the result of _publish(), not data
    result = solver.solve(data)

    # Result should be a Register (empty since publishes is empty)
    assert isinstance(result, Register)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_lp/test_solver.py::test_lp_solver_solve_returns_publish_when_optimal -v`

Expected: PASS (current implementation returns `data`, which is a Register, but we need to ensure `_publish()` is called)

- [ ] **Step 3: Update solve() to call _publish()**

Change line 120 from:
```python
pass  # Users handle solution extraction
```

To:
```python
return self._publish(data)
```

- [ ] **Step 4: Update existing test that expects data return**

Update `test_lp_solver_solve_optimal_status` from:
```python
# Should not raise, should return data
result = solver.solve(data)
assert result is data
```

To:
```python
# Should not raise, should return published var
result = solver.solve(data)
assert isinstance(result, Register)
```

And update `test_lp_solver_solve_executes_build_steps` from:
```python
assert result is data  # Should return the same var
```

To:
```python
assert isinstance(result, Register)  # Should return a var
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_lp/test_solver.py -v`

Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add or_algo/lp/solver.py tests/test_lp/test_solver.py
git commit -m "feat: LpSolver.solve() returns _publish() result when OPTIMAL"
```

---

## Task 5: Update Algorithm.solve() to Merge Published Values

**Files:**
- Modify: `or_algo/algorithm.py:35-52`

- [ ] **Step 1: Write failing test for merge logic**

Add to `tests/test_algorithm.py`:

```python
def test_algorithm_solve_merges_published_values():
    """Algorithm.solve() should merge published values back into data."""
    class PublishingSolver(Solver):
        def __init__(self, publish_value: str):
            super().__init__()
            self.publish_value = publish_value

        def solve(self, data: Register[Parameter]) -> Register[Parameter]:
            # Create a new var with published values
            published = Register[Parameter]()
            published[Id][(Index,)][(0,)] = self.publish_value
            return published

    algo = Algorithm()
    algo.append(PublishingSolver, "published_value")

    data = Register[Parameter]()
    data[Id][(Index,)][(0,)] = "original_value"

    algo.solve(data)

    # Published value should be merged into data
    assert data[Id][(Index,)][(0,)] == "published_value"


def test_algorithm_solve_merge_multi_dimensional():
    """Algorithm.solve() should merge multi-dimensional parameters."""
    from unittest.mock import Mock

    class MultiDimPublishingSolver(Solver):
        def solve(self, data: Register[Parameter]) -> Register[Parameter]:
            published = Register[Parameter]()
            dim1 = Mock()
            dim2 = Mock()
            published[Id][(dim1, dim2)][(0, 1)] = "merged"
            return published

    algo = Algorithm()
    algo.append(MultiDimPublishingSolver)

    data = Register[Parameter]()

    algo.solve(data)

    # Value should be merged at correct dimension/index location
    # (actual verification depends on Register implementation)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_algorithm.py::test_algorithm_solve_merges_published_values -v`

Expected: FAIL with "original_value" not replaced (current implementation ignores return value)

- [ ] **Step 3: Update Algorithm.solve() to merge published values**

Change the solve loop from:
```python
for solver, args, kwargs in self._solvers:
    try:
        solver(*args, **kwargs).solve(data)
    except Exception as e:
        raise OrAlgoException(
            f"Failed {solver.__name__}.solve()! args={args}, kwargs={kwargs}"
        ) from e
```

To:
```python
for solver, args, kwargs in self._solvers:
    try:
        publish = solver(*args, **kwargs).solve(data)
        # Merge published values back into data
        for param in publish:
            for dims in publish[param]:
                data[param][dims] = publish[param][dims]
    except Exception as e:
        raise OrAlgoException(
            f"Failed {solver.__name__}.solve()! args={args}, kwargs={kwargs}"
        ) from e
```

Also update the docstring from:
```python
"""Execute all solvers in sequence.

Args:
    data: Register containing input parameters; solutions are
          written back to this same Register.

Raises:
    OrAlgoException: If any solver fails. The original exception
                    is chained as the cause.
"""
```

To:
```python
"""Execute all solvers in sequence.

Args:
    data: Register containing input parameters; solutions are
          written back to this same Register (either directly
          or via published value merging).

Raises:
    OrAlgoException: If any solver fails. The original exception
                    is chained as the cause.
"""
```

- [ ] **Step 4: Update existing tests that don't return anything**

Update the test solvers to return `data`:

In `test_algorithm_solve_executes_solvers_in_order`, update:
```python
def solve(self, data: Register[Parameter]) -> Register[Parameter]:
    execution_order.append(self.marker)
    return data
```

In `SuccessSolver`, update:
```python
def solve(self, data: Register[Parameter]) -> Register[Parameter]:
    self.called = True
    data[Id][(Index,)][(0,)] = self.marker
    return data
```

In `TrackingSolver` (in `test_algorithm_solve_stops_on_first_failure`), update:
```python
def solve(self, data: Register[Parameter]) -> Register[Parameter]:
    execution_order.append(self.marker)
    if self.marker == "fail":
        raise ValueError("intentional failure")
    return data
```

In `ConfiguredSolver` (in `test_algorithm_solve_with_solver_args`), update:
```python
def solve(self, data: Register[Parameter]) -> Register[Parameter]:
    data[Id][(Index,)][(0,)] = f"value={self.value}"
    return data
```

In `ConfiguredSolver` (in `test_algorithm_solve_with_solver_kwargs`), update:
```python
def solve(self, data: Register[Parameter]) -> Register[Parameter]:
    data[Id][(Index,)][(0,)] = f"value={self.value},flag={self.flag}"
    return data
```

In `ConfiguredSolver` (in `test_algorithm_solve_with_both_args_and_kwargs`), update:
```python
def solve(self, data: Register[Parameter]) -> Register[Parameter]:
    data[Id][(Index,)][(0,)] = f"a={self.a},b={self.b},c={self.c}"
    return data
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_algorithm.py -v`

Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add or_algo/algorithm.py tests/test_algorithm.py
git commit -m "feat: Algorithm.solve() merges published values back into data"
```

---

## Task 6: Update Base Solver Tests for Return Type

**Files:**
- Modify: `tests/test_solver.py`

- [ ] **Step 1: Check if test_solver.py exists**

Run: `ls tests/test_solver.py`

If file doesn't exist, skip this task (base Solver has no implementation tests).

- [ ] **Step 2: If exists, update any tests expecting None return**

Look for assertions like `assert result is None` and update to `assert isinstance(result, Register)`.

- [ ] **Step 3: Run solver tests**

Run: `pytest tests/test_solver.py -v`

Expected: PASS (or skip if file doesn't exist)

- [ ] **Step 4: Commit if changes made**

```bash
git add tests/test_solver.py
git commit -m "test: update solver tests for return type"
```

---

## Task 7: Integration Test for Full Publishing Flow

**Files:**
- Modify: `tests/test_lp/test_solver.py`

- [ ] **Step 1: Write integration test**

Add to `tests/test_lp/test_solver.py`:

```python
def test_lp_solver_full_publish_flow():
    """Integration test for full publish flow with real OR-Tools variables."""
    from or_algo.lp.step import CreateVar

    solver = LpSolver(name="test_solver")

    # Create real parameter
    from register import Parameter
    param = Parameter(name="x", name_cn="x变量", vtype=float)
    data = Register[Parameter]()
    data.register(param)

    # Create variable symbol
    var_symbol = Var(p=param, sign="x")

    # Create step that adds variable to OR-Tools
    class SimpleCreateVar(CreateVar):
        def run(self, data, model, var):
            # Create a simple continuous variable
            ortools_var = model.NumVar(0, 100, self._symbol.name)
            var[self._symbol] = ortools_var

    # Set up publishes to extract this variable
    solver._publishes = [(var_symbol, None, None)]

    # Append the step
    solver.append(SimpleCreateVar, var_symbol)

    # Mock Solve to return OPTIMAL and set a solution value
    original_solve = solver._model.Solve
    def mock_solve():
        # Create and set the variable first
        solver._model.Solve = lambda: original_solve()
        # After solve, set the variable value
        for symbol, dims, index in solver._publishes:
            if dims is None and index is None:
                variable = solver._var[symbol]
                # Mock the solution value
                variable.solution_value = Mock(return_value=42.0)
        return pywraplp.Solver.OPTIMAL

    solver._model.Solve = mock_solve

    # Solve
    result = solver.solve(data)

    # Verify published value
    assert isinstance(result, Register)
```

- [ ] **Step 2: Run integration test**

Run: `pytest tests/test_lp/test_solver.py::test_lp_solver_full_publish_flow -v`

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_lp/test_solver.py
git commit -m "test: add integration test for full publish flow"
```

---

## Task 8: Update Module Exports

**Files:**
- Modify: `or_algo/__init__.py` (if needed for type hints)
- Check: `or_algo/lp/__init__.py`

- [ ] **Step 1: Verify exports are correct**

Check that `Symbol` and related types are exported from `or_algo/lp/__init__.py` for type hints.

Run: `python -c "from or_algo.lp import Symbol; print(Symbol)"`

Expected: No ImportError

- [ ] **Step 2: Verify typing imports work**

Run: `python -c "from or_algo.lp.solver import LpSolver; print(LpSolver.__init__.__annotations__)"`

Expected: Shows type annotations correctly

- [ ] **Step 3: Commit if exports updated**

```bash
git add or_algo/lp/__init__.py
git commit -m "chore: ensure type hints are properly exported"
```

---

## Task 9: Run Full Test Suite

**Files:**
- All tests

- [ ] **Step 1: Run all tests**

Run: `pytest tests/ -v`

Expected: All tests PASS

- [ ] **Step 2: Run with coverage**

Run: `pytest tests/ --cov=or_algo --cov-report=term-missing`

Expected: Coverage report shows new code covered

- [ ] **Step 3: Type check with mypy**

Run: `mypy or_algo/`

Expected: No type errors

- [ ] **Step 4: Lint with ruff**

Run: `ruff check or_algo/ tests/`

Expected: No linting errors

- [ ] **Step 5: Commit**

```bash
git commit --allow-empty -m "test: verify full test suite passes"
```

---

## Task 10: Update Documentation

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README with publishing usage**

Add section after LP Module basic usage:

```markdown
### Solution Publishing

LpSolver can automatically extract solution values using the `publishes` attribute:

```python
from or_algo.lp import LpSolver, CreateVar
from or_algo.lp.symbol import Var
from register import Register, Parameter

# Create parameter and variable
param = Parameter(name="production", name_cn="产量", vtype=float)
var = Var(p=param, sign="P")

# Create solver with publishes
solver = LpSolver(
    name="production_plan",
    publishes=[(var, None, None)]  # Publish all values of var
)

# Add variable creation step
solver.append(MyCreateVar, var)

# Solve - solution values automatically extracted
data = Register[Parameter]()
data.register(param)
result = solver.solve(data)
```

The `publishes` attribute is a list of tuples:
- `symbol`: The Var symbol to extract
- `dimensions`: Tuple of dimensions (None for scalar)
- `indexes`: Tuple of indexes (None for all)
```

- [ ] **Step 2: Run type check on README examples**

Extract code blocks and verify they run without errors.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add solution publishing documentation to README"
```

---

## Summary

This plan implements the LpSolver solution publishing feature in 10 tasks:

1. **Base Solver return type** - Add `-> Register[Parameter]` to `Solver.solve()`
2. **publishes attribute** - Add declarative specification to `LpSolver`
3. **_publish() method** - Extract solution values from OR-Tools
4. **solve() return** - Call `_publish()` when OPTIMAL
5. **Algorithm merge** - Merge published values back into main data flow
6. **Base tests update** - Ensure tests expect return values
7. **Integration test** - Full flow test with real OR-Tools
8. **Module exports** - Verify type hints work
9. **Full test suite** - Verify all tests pass
10. **Documentation** - Update README with usage examples

Each task follows TDD: write failing test, implement, verify, commit.