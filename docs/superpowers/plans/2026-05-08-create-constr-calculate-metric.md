# CreateConstrCalculateMetric Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `CreateConstrCalculateMetric` class to create OR-Tools constraints for metric aggregation (SUM, MAX, MIN, RANGE)

**Architecture:** Single `CreateConstrCalculateMetric` class that iterates through variables with Metric dimension and creates appropriate OR-Tools constraints using `model.Add()`

**Tech Stack:** OR-Tools linear solver, register package, existing `or_algo.lp.step` module

---

## File Structure

**Files to modify:**
- `or_algo/lp/step.py` - Add `CreateConstrCalculateMetric` class after `CreateVar` class
- `tests/test_lp/test_step.py` - Add unit tests

**No new files** - this adds functionality to existing module

---

### Task 1: Add CreateConstrCalculateMetric class skeleton

**Files:**
- Modify: `or_algo/lp/step.py` (after line 223, after CreateVar class ends)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_lp/test_step.py

def test_create_constr_calculate_metric_is_create_constr():
    """Test that CreateConstrCalculateMetric is a CreateConstr subclass."""
    from or_algo.lp.step import CreateConstr, CreateConstrCalculateMetric

    assert issubclass(CreateConstrCalculateMetric, CreateConstr)

    step = CreateConstrCalculateMetric()
    assert isinstance(step, CreateConstr)
    assert step._symbol.name == 'CalculateMetric'
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_lp/test_step.py::test_create_constr_calculate_metric_is_create_constr -v`

Expected: FAIL with "CreateConstrCalculateMetric not defined"

- [ ] **Step 3: Write minimal class skeleton**

Add to `or_algo/lp/step.py` after the `CreateVar` class (around line 223):

```python
class CreateConstrCalculateMetric(CreateConstr):
    """Create metric aggregation constraints for variables with Metric dimension.

    Supports SUM, MAX, MIN, and RANGE metrics from or_register.Register.
    Constraints are created but not stored.
    """

    def __init__(self):
        from or_algo.lp.symbol import Constr

        super().__init__(Constr('CalculateMetric', '', 'CalculateMetric'))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_lp/test_step.py::test_create_constr_calculate_metric_is_create_constr -v`

Expected: PASS

- [ ] **Step 5: Export the new class**

Modify `or_algo/lp/__init__.py`:

```python
# Change this line:
from .step import LpStep, CreateVar, CreateConstr

# To:
from .step import LpStep, CreateVar, CreateConstr, CreateConstrCalculateMetric
```

Also update the `__all__` list:

```python
__all__ = [
    "Symbol",
    "Var",
    "Constr",
    "LpStep",
    "CreateVar",
    "CreateConstr",
    "CreateConstrCalculateMetric",  # Add this line
    "LpSolver",
    "exception",
]
```

- [ ] **Step 6: Run tests to verify import works**

Run: `pytest tests/test_lp/test_step.py::test_create_constr_calculate_metric_is_create_constr -v`

Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add or_algo/lp/step.py or_algo/lp/__init__.py tests/test_lp/test_step.py
git commit -m "feat: add CreateConstrCalculateMetric class skeleton"
```

---

### Task 2: Implement run() method - iterate variables with Metric dimension

**Files:**
- Modify: `or_algo/lp/step.py`
- Test: `tests/test_lp/test_step.py`

- [ ] **Step 1: Write test for run() method - skip when no Metric dimension**

```python
# tests/test_lp/test_step.py

def test_create_constr_calculate_metric_no_metric_dimension():
    """Test that run() skips variables without Metric dimension."""
    from or_algo.lp.step import CreateConstrCalculateMetric
    from or_algo.lp.symbol import Var
    from or_register import Register, Parameter, Dimension
    from ortools.linear_solver import pywraplp
    from unittest.mock import Mock

    # Create a mock parameter
    mock_param = Mock(spec=Parameter)
    mock_param.vtype = float

    # Create a variable symbol with non-Metric dimension
    test_dim = Dimension('TestDim')
    var_symbol = Var(p=mock_param, sign='x')

    # Create register with variable but no Metric dimension
    var_register = Register()
    var_register[var_symbol][(test_dim,)][(0,)] = Mock()

    # Create solver
    model = pywraplp.Solver.CreateSolver('CBC')

    # Create step and run
    step = CreateConstrCalculateMetric()
    data = Register()

    # Should not raise any errors
    step.run(data, model, var_register)

    # Verify no constraints were created (model has only 0 constraints)
    # Note: OR-Tools doesn't expose a direct constraint count, but we can verify it doesn't crash
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_lp/test_step.py::test_create_constr_calculate_metric_no_metric_dimension -v`

Expected: FAIL with "run() not implemented" or similar

- [ ] **Step 3: Implement basic run() method skeleton**

Add to `CreateConstrCalculateMetric` class in `or_algo/lp/step.py`:

```python
class CreateConstrCalculateMetric(CreateConstr):
    """Create metric aggregation constraints for variables with Metric dimension.

    Supports SUM, MAX, MIN, and RANGE metrics from or_register.Register.
    Constraints are created but not stored.
    """

    def __init__(self):
        from or_algo.lp.symbol import Constr

        super().__init__(Constr('CalculateMetric', '', 'CalculateMetric'))

    def run(self, data: "Register[Parameter]", model: "pywraplp.Solver",
            var: "Register[Symbol]") -> None:
        """Create metric aggregation constraints for variables with Metric dimension.

        Args:
            data: Register containing input parameters
            model: OR-Tools solver instance
            var: Register for storing variables/constraints
        """
        from or_register import Register as Reg
        from or_algo.lp.symbol import Var
        from ortools.linear_solver import pywraplp

        # Iterate through all Var instances in var
        for var_symbol in [v for v in var if isinstance(v, Var)]:
            # Check each dimension for Metric
            for dimension in var[var_symbol]:
                # Skip if last dimension is not Metric
                if not dimension or dimension[-1] is not Reg.Metric:
                    continue

                # TODO: Create constraints based on metric type
                # This will be implemented in subsequent tasks
                pass
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_lp/test_step.py::test_create_constr_calculate_metric_no_metric_dimension -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add or_algo/lp/step.py tests/test_lp/test_step.py
git commit -m "feat: implement CreateConstrCalculateMetric.run() skeleton with Metric dimension detection"
```

---

### Task 3: Implement SUM metric constraints

**Files:**
- Modify: `or_algo/lp/step.py`
- Test: `tests/test_lp/test_step.py`

- [ ] **Step 1: Write test for SUM metric**

```python
# tests/test_lp/test_step.py

def test_create_constr_calculate_metric_sum():
    """Test that SUM metric creates equality constraint with sum of base variables."""
    from or_algo.lp.step import CreateConstrCalculateMetric
    from or_algo.lp.symbol import Var
    from or_register import Register, Parameter, Dimension
    from ortools.linear_solver import pywraplp

    # Create mock parameter
    mock_param = Mock(spec=Parameter)
    mock_param.vtype = float

    # Create dimensions
    test_dim = Dimension('TestDim')

    # Create variable symbol
    var_symbol = Var(p=mock_param, sign='x')

    # Create solver
    model = pywraplp.Solver.CreateSolver('CBC')

    # Create base variables
    base1 = model.NumVar(0, 10, 'x_base1')
    base2 = model.NumVar(0, 10, 'x_base2')
    base3 = model.NumVar(0, 10, 'x_base3')

    # Create metric variable
    metric_var = model.NumVar(0, 100, 'x_sum')

    # Create register with base and metric variables
    var_register = Register()
    var_register[var_symbol][(test_dim,)][(0,)] = base1
    var_register[var_symbol][(test_dim,)][(1,)] = base2
    var_register[var_symbol][(test_dim,)][(2,)] = base3
    var_register[var_symbol][(test_dim, Reg.Metric)][(0, Reg.SUM)] = metric_var

    # Create data register with primary key
    data = Register()
    data[Parameter][(test_dim,)][(0,)] = (0,)
    data[Parameter][(test_dim,)][(1,)] = (1,)
    data[Parameter][(test_dim,)][(2,)] = (2,)

    # Create step and run
    step = CreateConstrCalculateMetric()
    step.run(data, model, var_register)

    # Verify constraint was created by solving and checking
    # If base1=1, base2=2, base3=3, then metric_var should equal 6
    model.Add(base1 == 1)
    model.Add(base2 == 2)
    model.Add(base3 == 3)

    status = model.Solve()
    assert status == pywraplp.Solver.OPTIMAL
    assert metric_var.solution_value() == 6.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_lp/test_step.py::test_create_constr_calculate_metric_sum -v`

Expected: FAIL (SUM constraint not implemented yet)

- [ ] **Step 3: Implement SUM metric constraint creation**

Update the `run()` method in `or_algo/lp/step.py` to handle SUM:

```python
    def run(self, data: "Register[Parameter]", model: "pywraplp.Solver",
            var: "Register[Symbol]") -> None:
        """Create metric aggregation constraints for variables with Metric dimension.

        Args:
            data: Register containing input parameters
            model: OR-Tools solver instance
            var: Register for storing variables/constraints
        """
        from or_register import Register as Reg
        from or_algo.lp.symbol import Var
        from ortools.linear_solver import pywraplp
        from or_algo.lp import exception as lp_exception

        # Iterate through all Var instances in var
        for var_symbol in [v for v in var if isinstance(v, Var)]:
            # Check each dimension for Metric
            for dimension in var[var_symbol]:
                # Skip if last dimension is not Metric
                if not dimension or dimension[-1] is not Reg.Metric:
                    continue

                # Extract base dimension (all except last)
                dimension_ = dimension[:-1]

                # Process each index in the metric dimension
                for index in var[var_symbol][dimension]:
                    metric = index[-1]

                    # Create constraint based on metric type
                    if metric is Reg.SUM:
                        # metric_var == sum(base_vars)
                        metric_var = var[var_symbol][dimension][index]

                        # Get base indices by removing last element (metric type)
                        base_index_prefix = index[:-1]

                        # Sum all base variables
                        base_vars = [
                            var[var_symbol][dimension_][base_index]
                            for base_index in var.select(var_symbol, dimension_, base_index_prefix)
                        ]

                        # Create equality constraint
                        constraint = model.Add(
                            metric_var == sum(base_vars),
                            name=f'{self._symbol.name}-{var_symbol.sign}({",".join(d.sign for d in dimension)})({",".join(str(ix) for ix in index)})_'
                        )

                    elif metric is Reg.MAX:
                        # TODO: Implement in next task
                        pass

                    elif metric is Reg.MIN:
                        # TODO: Implement in next task
                        pass

                    elif metric is Reg.RANGE:
                        # TODO: Implement in next task
                        pass

                    else:
                        raise lp_exception.BuildLpStepException(
                            f"Unknown metric type: {metric}. Expected SUM, MAX, MIN, or RANGE."
                        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_lp/test_step.py::test_create_constr_calculate_metric_sum -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add or_algo/lp/step.py tests/test_lp/test_step.py
git commit -m "feat: implement SUM metric constraint creation"
```

---

### Task 4: Implement MAX metric constraints

**Files:**
- Modify: `or_algo/lp/step.py`
- Test: `tests/test_lp/test_step.py`

- [ ] **Step 1: Write test for MAX metric**

```python
# tests/test_lp/test_step.py

def test_create_constr_calculate_metric_max():
    """Test that MAX metric creates lower bound constraints (metric >= each base)."""
    from or_algo.lp.step import CreateConstrCalculateMetric
    from or_algo.lp.symbol import Var
    from or_register import Register, Parameter, Dimension
    from ortools.linear_solver import pywraplp

    # Create mock parameter
    mock_param = Mock(spec=Parameter)
    mock_param.vtype = float

    # Create dimensions
    test_dim = Dimension('TestDim')

    # Create variable symbol
    var_symbol = Var(p=mock_param, sign='x')

    # Create solver
    model = pywraplp.Solver.CreateSolver('CBC')

    # Create base variables
    base1 = model.NumVar(0, 10, 'x_base1')
    base2 = model.NumVar(0, 20, 'x_base2')
    base3 = model.NumVar(0, 15, 'x_base3')

    # Create metric variable
    metric_var = model.NumVar(0, 100, 'x_max')

    # Create register with base and metric variables
    var_register = Register()
    var_register[var_symbol][(test_dim,)][(0,)] = base1
    var_register[var_symbol][(test_dim,)][(1,)] = base2
    var_register[var_symbol][(test_dim,)][(2,)] = base3
    var_register[var_symbol][(test_dim, Reg.Metric)][(0, Reg.MAX)] = metric_var

    # Create data register
    data = Register()

    # Create step and run
    step = CreateConstrCalculateMetric()
    step.run(data, model, var_register)

    # Verify constraints: metric >= each base
    # To test, we set base variables and minimize metric
    # The optimal metric should be max(base1, base2, base3) = 20
    model.Add(base1 == 5)
    model.Add(base2 == 20)
    model.Add(base3 == 15)
    model.Minimize(metric_var)

    status = model.Solve()
    assert status == pywraplp.Solver.OPTIMAL
    # Metric should be >= 20 (the maximum), and minimized so equals 20
    assert metric_var.solution_value() == 20.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_lp/test_step.py::test_create_constr_calculate_metric_max -v`

Expected: FAIL (MAX constraint not implemented yet)

- [ ] **Step 3: Implement MAX metric constraint creation**

Update the `elif metric is Reg.MAX:` branch in `run()` method:

```python
                    elif metric is Reg.MAX:
                        # metric_var >= each base_var (lower bound for maximum)
                        metric_var = var[var_symbol][dimension][index]
                        base_index_prefix = index[:-1]

                        for base_index in var.select(var_symbol, dimension_, base_index_prefix):
                            base_var = var[var_symbol][dimension_][base_index]
                            model.Add(
                                metric_var >= base_var,
                                name=f'{self._symbol.name}-{var_symbol.sign}({",".join(d.sign for d in dimension_)})({",".join(str(ix) for ix in base_index)})'
                            )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_lp/test_step.py::test_create_constr_calculate_metric_max -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add or_algo/lp/step.py tests/test_lp/test_step.py
git commit -m "feat: implement MAX metric constraint creation"
```

---

### Task 5: Implement MIN metric constraints

**Files:**
- Modify: `or_algo/lp/step.py`
- Test: `tests/test_lp/test_step.py`

- [ ] **Step 1: Write test for MIN metric**

```python
# tests/test_lp/test_step.py

def test_create_constr_calculate_metric_min():
    """Test that MIN metric creates upper bound constraints (metric <= each base)."""
    from or_algo.lp.step import CreateConstrCalculateMetric
    from or_algo.lp.symbol import Var
    from or_register import Register, Parameter, Dimension
    from ortools.linear_solver import pywraplp

    # Create mock parameter
    mock_param = Mock(spec=Parameter)
    mock_param.vtype = float

    # Create dimensions
    test_dim = Dimension('TestDim')

    # Create variable symbol
    var_symbol = Var(p=mock_param, sign='x')

    # Create solver
    model = pywraplp.Solver.CreateSolver('CBC')

    # Create base variables
    base1 = model.NumVar(10, 100, 'x_base1')
    base2 = model.NumVar(20, 100, 'x_base2')
    base3 = model.NumVar(15, 100, 'x_base3')

    # Create metric variable
    metric_var = model.NumVar(0, 100, 'x_min')

    # Create register with base and metric variables
    var_register = Register()
    var_register[var_symbol][(test_dim,)][(0,)] = base1
    var_register[var_symbol][(test_dim,)][(1,)] = base2
    var_register[var_symbol][(test_dim,)][(2,)] = base3
    var_register[var_symbol][(test_dim, Reg.Metric)][(0, Reg.MIN)] = metric_var

    # Create data register
    data = Register()

    # Create step and run
    step = CreateConstrCalculateMetric()
    step.run(data, model, var_register)

    # Verify constraints: metric <= each base
    # To test, we set base variables and maximize metric
    # The optimal metric should be min(base1, base2, base3) = 10
    model.Add(base1 == 10)
    model.Add(base2 == 20)
    model.Add(base3 == 15)
    model.Maximize(metric_var)

    status = model.Solve()
    assert status == pywraplp.Solver.OPTIMAL
    # Metric should be <= 10 (the minimum), and maximized so equals 10
    assert metric_var.solution_value() == 10.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_lp/test_step.py::test_create_constr_calculate_metric_min -v`

Expected: FAIL (MIN constraint not implemented yet)

- [ ] **Step 3: Implement MIN metric constraint creation**

Update the `elif metric is Reg.MIN:` branch in `run()` method:

```python
                    elif metric is Reg.MIN:
                        # metric_var <= each base_var (upper bound for minimum)
                        metric_var = var[var_symbol][dimension][index]
                        base_index_prefix = index[:-1]

                        for base_index in var.select(var_symbol, dimension_, base_index_prefix):
                            base_var = var[var_symbol][dimension_][base_index]
                            model.Add(
                                metric_var <= base_var,
                                name=f'{self._symbol.name}-{var_symbol.sign}({",".join(d.sign for d in dimension_)})({",".join(str(ix) for ix in base_index)})'
                            )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_lp/test_step.py::test_create_constr_calculate_metric_min -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add or_algo/lp/step.py tests/test_lp/test_step.py
git commit -m "feat: implement MIN metric constraint creation"
```

---

### Task 6: Implement RANGE metric constraints

**Files:**
- Modify: `or_algo/lp/step.py`
- Test: `tests/test_lp/test_step.py`

- [ ] **Step 1: Write test for RANGE metric**

```python
# tests/test_lp/test_step.py

def test_create_constr_calculate_metric_range():
    """Test that RANGE metric creates pairwise difference constraints."""
    from or_algo.lp.step import CreateConstrCalculateMetric
    from or_algo.lp.symbol import Var
    from or_register import Register, Parameter, Dimension
    from ortools.linear_solver import pywraplp
    import itertools

    # Create mock parameter
    mock_param = Mock(spec=Parameter)
    mock_param.vtype = float

    # Create dimensions
    test_dim = Dimension('TestDim')

    # Create variable symbol
    var_symbol = Var(p=mock_param, sign='x')

    # Create solver
    model = pywraplp.Solver.CreateSolver('CBC')

    # Create base variables
    base1 = model.NumVar(0, 100, 'x_base1')
    base2 = model.NumVar(0, 100, 'x_base2')
    base3 = model.NumVar(0, 100, 'x_base3')

    # Create metric variable
    metric_var = model.NumVar(0, 100, 'x_range')

    # Create register with base and metric variables
    var_register = Register()
    var_register[var_symbol][(test_dim,)][(0,)] = base1
    var_register[var_symbol][(test_dim,)][(1,)] = base2
    var_register[var_symbol][(test_dim,)][(2,)] = base3
    var_register[var_symbol][(test_dim, Reg.Metric)][(0, Reg.RANGE)] = metric_var

    # Create data register
    data = Register()

    # Create step and run
    step = CreateConstrCalculateMetric()
    step.run(data, model, var_register)

    # Verify constraints: metric >= |base1 - base2|, metric >= |base1 - base3|, etc.
    # Set specific values: base1=10, base2=25, base3=15
    # Range should be max - min = 25 - 10 = 15
    model.Add(base1 == 10)
    model.Add(base2 == 25)
    model.Add(base3 == 15)
    model.Minimize(metric_var)

    status = model.Solve()
    assert status == pywraplp.Solver.OPTIMAL
    # Metric should be >= 15 (the range), and minimized so equals 15
    assert metric_var.solution_value() == 15.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_lp/test_step.py::test_create_constr_calculate_metric_range -v`

Expected: FAIL (RANGE constraint not implemented yet)

- [ ] **Step 3: Implement RANGE metric constraint creation**

Add `import itertools` at the top of the file (if not already present), and update the `elif metric is Reg.RANGE:` branch:

```python
                    elif metric is Reg.RANGE:
                        # metric_var >= |base_var1 - base_var2| for all pairs
                        metric_var = var[var_symbol][dimension][index]
                        base_index_prefix = index[:-1]

                        # Get all base indices
                        base_indices = list(var.select(var_symbol, dimension_, base_index_prefix))

                        # Create pairwise constraints
                        for index1, index2 in itertools.permutations(base_indices, 2):
                            base_var1 = var[var_symbol][dimension_][index1]
                            base_var2 = var[var_symbol][dimension_][index2]

                            # metric >= base1 - base2 (covers both directions with permutations)
                            model.Add(
                                metric_var >= base_var1 - base_var2,
                                name=f'{self._symbol.name}-{var_symbol.sign}({",".join(d.sign for d in dimension_ * 2)})({",".join(str(ix) for ix in index1 + index2)})'
                            )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_lp/test_step.py::test_create_constr_calculate_metric_range -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add or_algo/lp/step.py tests/test_lp/test_step.py
git commit -m "feat: implement RANGE metric constraint creation"
```

---

### Task 7: Test unknown metric type raises exception

**Files:**
- Test: `tests/test_lp/test_step.py`

- [ ] **Step 1: Write test for unknown metric type**

```python
# tests/test_lp/test_step.py

def test_create_constr_calculate_metric_unknown_metric():
    """Test that unknown metric type raises BuildLpStepException."""
    from or_algo.lp.step import CreateConstrCalculateMetric
    from or_algo.lp.symbol import Var
    from or_algo.lp.exception import BuildLpStepException
    from or_register import Register, Parameter, Dimension
    from ortools.linear_solver import pywraplp
    import pytest

    # Create mock parameter
    mock_param = Mock(spec=Parameter)
    mock_param.vtype = float

    # Create dimensions
    test_dim = Dimension('TestDim')

    # Create variable symbol
    var_symbol = Var(p=mock_param, sign='x')

    # Create solver
    model = pywraplp.Solver.CreateSolver('CBC')

    # Create metric variable with unknown metric type
    metric_var = model.NumVar(0, 100, 'x_unknown')

    # Create register with unknown metric
    var_register = Register()
    var_register[var_symbol][(test_dim, Reg.Metric)][(0, "UNKNOWN_METRIC")] = metric_var

    # Create data register
    data = Register()

    # Create step and run
    step = CreateConstrCalculateMetric()

    # Should raise BuildLpStepException
    with pytest.raises(BuildLpStepException, match="Unknown metric type"):
        step.run(data, model, var_register)
```

- [ ] **Step 2: Run test to verify it passes**

Run: `pytest tests/test_lp/test_step.py::test_create_constr_calculate_metric_unknown_metric -v`

Expected: PASS (exception already implemented in Task 3)

- [ ] **Step 3: Commit**

```bash
git add tests/test_lp/test_step.py
git commit -m "test: add unknown metric type exception test"
```

---

### Task 8: Run all tests and verify no regressions

**Files:**
- All modified files

- [ ] **Step 1: Run all LP tests**

Run: `pytest tests/test_lp/ -v`

Expected: All tests PASS (including new tests and existing tests)

- [ ] **Step 2: Run full test suite**

Run: `pytest tests/ -v`

Expected: No regressions in other test modules

- [ ] **Step 3: Run type checking**

Run: `mypy or_algo/lp/step.py`

Expected: No new type errors (may have pre-existing OR-Tools stub warnings)

- [ ] **Step 4: Final commit**

```bash
git add or_algo/lp/step.py or_algo/lp/__init__.py tests/test_lp/test_step.py
git commit -m "test: verify CreateConstrCalculateMetric implementation complete"
```

---

## Verification

After completing all tasks:
1. All unit tests pass
2. Integration test demonstrates solver can solve LP with metric variables
3. No regressions in existing functionality
4. Code follows OR-Tools API patterns
5. Class is properly exported from `or_algo.lp` module
