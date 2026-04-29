# LpSolver Solution Publishing Design

**Date:** 2026-04-29
**Status:** Approved
**Version:** 0.2.0

## Overview

Add declarative solution extraction to `LpSolver` via a `publishes` attribute and internal `_publish()` method. Published values merge back into the main data flow through `Algorithm`, completing the solve-extract-publish loop.

## Motivation

Currently, `LpSolver.solve()` leaves solution extraction entirely to users, requiring manual access to `self._var` and OR-Tools variables. This design provides:
- **Declarative publishing** - Specify what to extract during construction
- **Automatic extraction** - Solution values extracted when OPTIMAL
- **Clean data flow** - Published values merge back into the main Register through `Algorithm`

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Algorithm                            │
│  (orchestrates sequential Solver execution)             │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                      LpSolver                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │  publishes: List[Tuple[Symbol, dims, indexes]]  │   │
│  └─────────────────────────────────────────────────┘   │
│                          │                              │
│  solve() ──────────────► OPTIMAL?                      │
│                          │ YES                          │
│                          ▼                              │
│  _publish(data) ──────────────────┐                    │
│    │                                │                    │
│    │  ┌─────────────────────────┐  │                    │
│    └──│ Extract from self._var  │──┘                    │
│       │ variable.solution_value()                       │
│       └─────────────────────────┘                       │
│                    │                                    │
│                    ▼                                    │
│  return Register[Parameter] (published)                 │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼ merge
┌─────────────────────────────────────────────────────────┐
│  Algorithm.solve():                                     │
│    publish = solver.solve(data)                         │
│    for param in publish:                                │
│        for dims in publish[param]:                      │
│            data[param][dims] = publish[param][dims]     │
└─────────────────────────────────────────────────────────┘
```

## Components

### 1. `LpSolver.publishes` Attribute

```python
publishes: List[Tuple[Symbol, Tuple[Dimension, ...], Tuple[int, ...]]]
```

**Purpose:** Declarative specification of what solution values to extract.

**Structure:**
- `symbol`: The Var symbol to extract from
- `dimensions`: Tuple of dimensions (None for scalar)
- `indexes`: Tuple of indexes (None for all)

**Lifecycle:**
- Fixed during construction (set in `__init__`)
- Not modified after initialization

### 2. `LpSolver._publish()` Method

```python
def _publish(self, data: Register[Parameter]) -> Register[Parameter]:
    publish = Register[Parameter]()
    for symbol, dims, index in self.publishes:
        # Get OR-Tools Variable
        variable = self._var[symbol][dims][index]  # Type: pywraplp.Variable
        # Extract solution value
        value = variable.solution_value()
        # Write to output Register
        publish[symbol.parameter][dims][index] = value
    return publish
```

**Purpose:** Extract solution values from OR-Tools and build output Register.

**Flow:**
1. Create empty output Register
2. Iterate through `self.publishes`
3. Navigate `self._var` to get OR-Tools Variable
4. Extract solution value via `variable.solution_value()`
5. Write to output Register using `symbol.parameter`

### 3. `LpSolver.solve()` Update

**Before:**
```python
if status == pywraplp.Solver.OPTIMAL:
    pass  # Users handle solution extraction
```

**After:**
```python
if status == pywraplp.Solver.OPTIMAL:
    return self._publish(data)
```

**Change:** Return the published Register instead of passing through `data`.

### 4. `Algorithm.solve()` Merge

**Current:**
```python
solver(*args, **kwargs).solve(data)
```

**Updated:**
```python
publish = solver(*args, **kwargs).solve(data)
for param in publish:
    for dims in publish[param]:
        data[param][dims] = publish[param][dims]
```

**Purpose:** Merge published values back into the main data Register.

**Flow:**
1. Capture the Register returned by `solve()`
2. Iterate through published parameters
3. Update `data` at dimension level

### 5. `Solver.solve()` Return Type Annotation

**Before:**
```python
def solve(self, data: Register[Parameter]) -> Register[Parameter] | None:
```

**After:**
```python
def solve(self, data: Register[Parameter]) -> Register[Parameter]:
```

**Purpose:** Ensure consistent return type across all Solver implementations.

## Data Flow Example

```python
# 1. Create solver with publishes
solver = LpSolver(
    name="production_plan",
    publishes=[
        (production_var, (factory, week), (0,)),  # Single value
        (inventory_var, None, None),               # All scalar values
    ]
)

# 2. Solve
algo = Algorithm()
algo.append(MySolver)
data = algo.solve(input_data)

# 3. Solution automatically extracted and merged
# - Variable values from OR-Tools
# - Written to data by Algorithm.merge()
# - Available for subsequent solvers
```

## Type Annotations

```python
from typing import List, Tuple

class LpSolver(Solver):
    publishes: List[Tuple[Symbol, Tuple[Dimension, ...], Tuple[int, ...]]]
    
    def _publish(self, data: Register[Parameter]) -> Register[Parameter]:
        ...

    def solve(self, data: Register[Parameter]) -> Register[Parameter]:
        ...
```

## Error Handling

No new exceptions introduced. Existing exception handling covers:
- `BuildLpStepException` - Build step failures
- `LpModelOptimizeException` - Non-OPTIMAL statuses

## Testing

### Unit Tests for `_publish()`
- Empty `publishes` returns empty Register
- Single value extraction (dims + index specified)
- All values extraction (None, None)
- Multiple symbols in `publishes`
- Solution value correctly extracted from OR-Tools Variable

### Unit Tests for `Algorithm.solve()` Merge
- Published values merged into `data`
- Multi-dimensional parameter handling
- Empty publish Register (no-op merge)

### Integration Tests
- Full flow: `LpSolver.solve()` → `_publish()` → `Algorithm.merge()`
- Multiple solvers with different publishes
- Data flowing through solver chain

## Scope

### v0.2.1 (Solution Publishing)
- `publishes` attribute on `LpSolver`
- `_publish()` method implementation
- `LpSolver.solve()` return update
- `Algorithm.solve()` merge logic
- `Solver.solve()` return type annotation
- Comprehensive test coverage

### Out of Scope
- Constraint dual value publishing (Var only for now)
- Objective value publishing
- Custom publishing logic (extension point for future)
- Publishing from non-LP solvers

## Compatibility

**Breaking Changes:** None - this is additive functionality.

**Backward Compatibility:**
- Existing code continues to work (OPTIMAL returns `data` by default)
- New code can opt-in via `publishes` attribute