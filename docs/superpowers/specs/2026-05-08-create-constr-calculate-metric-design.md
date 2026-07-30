# CreateConstrCalculateMetric Design

## Overview

`CreateConstrCalculateMetric` is a `CreateConstr` subclass that creates metric aggregation constraints for variables in the register. It finds variables with a `Metric` dimension and creates OR-Tools constraints to calculate:

- **SUM**: The metric variable equals the sum of base variables
- **MAX**: The metric variable is ≥ all base variables (lower bound for maximum)
- **MIN**: The metric variable is ≤ all base variables (upper bound for minimum)
- **RANGE**: For each pair of base variables, `metric ≥ base1 - base2`

## Motivation

When working with aggregated variables (sums, maximums, minimums, ranges), we need auxiliary constraints to define their relationship to base variables. This class automates constraint creation for metric variables that were created with the `Metric` dimension.

## API Translations (PySCIPOpt → OR-Tools)

### Constraint Creation

| PySCIPOpt | OR-Tools |
|-----------|----------|
| `model.addCons(lhs == rhs, name=name)` | `model.Add(lhs == rhs, name)` |
| `model.addCons(lhs >= rhs, name=name)` | `model.Add(lhs >= rhs, name)` |
| `model.addCons(lhs <= rhs, name=name)` | `model.Add(lhs <= rhs, name=name)` |

### Summation

| PySCIPOpt | OR-Tools |
|-----------|----------|
| `quicksum(expressions)` | `sum(expressions)` (Python built-in) |

**Note:** OR-Tools has better Python integration - no `quicksum` equivalent needed because Python's `sum()` works natively with OR-Tools linear expressions.

## Class Structure

```python
class CreateConstrCalculateMetric(CreateConstr):
    """Create metric aggregation constraints for variables with Metric dimension.

    Supports SUM, MAX, MIN, and RANGE metrics from or_register.Register.
    Constraints are created but not stored.
    """

    def __init__(self):
        super().__init__(Constr('CalculateMetric', '', 'CalculateMetric'))

    def run(self, data: "Register[Parameter]", model: "pywraplp.Solver",
            var: "Register[Symbol]") -> None:
```

## Implementation Details

### Logic Flow

1. Iterate through all `Var` instances in `var`
2. For each var, check dimensions ending with `Metric`
3. Extract base dimension (all dimensions except last)
4. For each index in the metric dimension, create constraints based on metric type

### Metric Implementations

#### SUM Metric

```python
if metric is Register.SUM:
    constraint = model.Add(
        var[var_symbol][dimension][index] == sum(
            var[var_symbol][dimension_][index_]
            for index_ in var.select(var_symbol, dimension_, index[:-1])
        ),
        name=f"{symbol_}(Index,)(0,)"
    )
```

#### MAX Metric

```python
elif metric is Register.MAX:
    for index_ in var.select(var_symbol, dimension_, index[:-1]):
        model.Add(
            var[var_symbol][dimension][index] >= var[var_symbol][dimension_][index_],
            name=f"{symbol_}({','.join(d.sign for d in dimension_)})({','.join(str(ix) for ix in index_)})"
        )
```

#### MIN Metric

```python
elif metric is Register.MIN:
    for index_ in var.select(var_symbol, dimension_, index[:-1]):
        model.Add(
            var[var_symbol][dimension][index] <= var[var_symbol][dimension_][index_],
            name=f"{symbol_}({','.join(d.sign for d in dimension_)})({','.join(str(ix) for ix in index_)})"
        )
```

#### RANGE Metric

```python
elif metric is Register.RANGE:
    for index1, index2 in itertools.permutations(
        var.select(var_symbol, dimension_, index[:-1]), r=2
    ):
        model.Add(
            var[var_symbol][dimension][index] >=
            var[var_symbol][dimension_][index1] - var[var_symbol][dimension_][index2],
            name=f'{symbol_}({','.join(d.sign for d in dimension_ * 2)})({','.join(str(ix) for ix in index1 + index2)})'
        )
```

## Edge Cases

| Case | Behavior |
|------|----------|
| Variable has no Metric dimension | Skip gracefully |
| register.select() returns empty | SUM: `metric == 0`; MAX/MIN/RANGE: no constraints |
| Unknown metric type | Raise `BuildLpStepException` |

## Imports & Dependencies

**File:** `or_algo/lp/step.py`

**New imports needed:**
```python
# Already imported:
import itertools  # for permutations in RANGE
from ortools.linear_solver import pywraplp  # already in TYPE_CHECKING

# Need to ensure available:
from or_register import Register  # for Register.SUM, Register.MAX, Register.MIN, Register.RANGE
```

**Exception handling:**
- Raise `BuildLpStepException` if metric type is unknown

## Testing Strategy

**Unit tests in `tests/test_lp/test_step.py`:**

1. `test_create_constr_calculate_metric_is_create_constr` - Verify class hierarchy
2. `test_create_constr_calculate_metric_sum` - Test SUM constraint creation
3. `test_create_constr_calculate_metric_max` - Test MAX constraints (≥)
4. `test_create_constr_calculate_metric_min` - Test MIN constraints (≤)
5. `test_create_constr_calculate_metric_range` - Test RANGE pairwise constraints
6. `test_create_constr_calculate_metric_unknown_metric` - Test error handling
7. `test_create_constr_calculate_metric_no_metric_dimension` - Test graceful skip

**Integration test:**
- Create a simple LP with metric variables and verify solver can solve

## Code Location

Add after `CreateVar` class (around line 223), before the existing `CreateConstr` base class.

## Differences from PySCIPOpt Version

1. **API calls:** `model.addCons()` → `model.Add()`
2. **Summation:** `quicksum()` → `sum()`
3. **No constraint storage:** Constraints are created but not stored in register (OR-Tools `Add()` returns constraint but we don't use it)
4. **Exception type:** `AlgoServiceException` → `BuildLpStepException`
