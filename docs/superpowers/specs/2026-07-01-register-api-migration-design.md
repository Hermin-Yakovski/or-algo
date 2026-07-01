# Register API Migration

## Overview

Adapt `or-algo` (core + LP subpackage) to the refreshed `register` package API. The new register replaces the old `Parameter`-based access with a `RegisterKey`-based chain: `Register` → `KeyView` → `IndexSpace` → `Selection`.

## Scope

- Core package: `solver.py`, `algorithm.py`, `task.py`
- LP subpackage: `symbol.py`, `step.py`, `solver.py`, `__init__.py`
- All corresponding tests

## Style Convention

Always use a trailing comma when indexing on dimensions and indices for visual unity with single-element tuples:

```python
reg[k][d,][0,]              # single dim/index
reg[k][d1, d2,][0, 1,]      # multi dim/index
reg[k][d1, d2,][:, :,]      # slicing
```

## Global Mappings

| # | Old | New |
|---|---|---|
| 1 | `Parameter` | `RegisterKey` |
| 2 | `Register[Parameter]` | `Register[RegisterKey]` |
| 3 | `Var` | `VarKey` |
| 4 | `Constr` | `ConstrKey` |
| 5 | `Register.ALL` | `slice(None)` |
| 6 | `data.select(key, (d,))` | `data[key][d,].keys()` |
| 7 | `reg[k][(d1, d2)][(0, 1)]` | `reg[k][d1, d2,][0, 1,]` |

## Core Package

### `or_algo/solver.py`

Import and type annotation changes only:

```python
# Old
from register import Register, Parameter
def solve(self, data: Register[Parameter]) -> Register[Parameter]:

# New
from register import Register, RegisterKey
def solve(self, data: Register[RegisterKey]) -> Register[RegisterKey]:
```

### `or_algo/algorithm.py`

Import and type annotation changes. All `Register[Parameter]` → `Register[RegisterKey]`.

`_merge_register` body — unchanged. `KeyView.__iter__`, `KeyView.pop()`, and `IndexSpace.update()` all exist in the new API.

### `or_algo/task.py`

Import and type annotation changes only:

```python
from register import Register, RegisterKey
def execute(self, reg: Register[RegisterKey]) -> Register[RegisterKey]:
```

## LP Subpackage

### `or_algo/lp/symbol.py` — Redesigned

**Deleted:** `Symbol` base class.

**`VarKey(NumKey)`:**

```python
class VarKey(NumKey):
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
```

- Inherits from `NumKey` — gets `id`, `name`, `name_cn`, `vtype` directly
- `sign` is own field
- `validate` checks `isinstance(v, pywraplp.Variable)`
- `@delegable` methods recover weight/lb/ub via `Selection` proxy:
  - `sum` / `min` / `max` / `range` — each creates a half-bounded `pywraplp.Variable` with constraints
  - `set_weight` — sets objective coefficients on the model
  - `set_lb` / `set_ub` — adds bound constraints to the model
- Uses `selected._dims` (protected, accepted for now) for dimension lookup and constraint naming

**Caller usage:**
```python
# After CreateVar.run() creates variables:
var[var_key][dims,].all.set_weight(model=model, weight=weight_reg)
var[var_key][dims,].all.set_lb(model=model, lb=lb_reg)
var[var_key][dims,].all.set_ub(model=model, ub=ub_reg)
```

**`ConstrKey(RegisterKey)`:**

```python
class ConstrKey(RegisterKey):
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

- All fields are own properties
- `id` is explicit constructor argument (prevents hash/eq collisions)

### `or_algo/lp/step.py`

**Imports:**

```python
from register import Register, RegisterKey
# TYPE_CHECKING:
from register import Dimension
```

Remove `from register import Metric` (no longer needed).
Remove `CreateConstrCalculateMetric` references.

**`LpStep`:**

Type annotation changes only:

```python
class LpStep(ABC):
    def __init__(self, symbol: RegisterKey):
        super().__init__()
        self._symbol = symbol

    @abstractmethod
    def run(self,
        data: Register[RegisterKey],
        model: pywraplp.Solver,
        var: Register[VarKey],
    ) -> None:
        pass
```

**`CreateVar`:**

Discard `weight`, `lb`, `ub` from `__init__` and fields. Delete `_create` method entirely.

```python
class CreateVar(LpStep, ABC):
    _symbol: VarKey

    def __init__(self, symbol: VarKey):
        super().__init__(symbol)
```

`vtype` property — uses `self._symbol.vtype` directly (VarKey IS a NumKey, no more `.parameter`).

**`CreateConstr`:**

Type annotation changes only:

```python
class CreateConstr(LpStep, ABC):
    def __init__(self, symbol: ConstrKey):
        super().__init__(symbol)

    @abstractmethod
    def run(self,
        data: Register[RegisterKey],
        model: pywraplp.Solver,
        var: Register[VarKey],
    ) -> None:
        pass
```

**`CreateConstrCalculateMetric`:**

Deleted entirely.

**`Publish`:**

```python
class Publish(LpStep):
    _symbol: VarKey
    _zeros: bool
    _dimension: Tuple[Dimension, ...]
    _threshold: float
    _target: Optional[tuple[slice, ...]]

    def __init__(self,
        symbol: VarKey,
        dimension: Tuple[Dimension, ...],
        target: Optional[tuple[slice, ...]] = None,
        zeros: bool = False,
        threshold: float = 1e-6,
    ):
        super().__init__(symbol)
        self._dimension = dimension
        self._zeros = zeros
        self._threshold = threshold
        self._target = target

    def run(self,
        data: Register[RegisterKey],
        model: pywraplp.Solver,
        register: Register[VarKey],
    ) -> None:
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
                raise exception.BuildLpStepException(
                    f"Unsupported vtype {self._symbol.vtype} while publishing variable {self._symbol.name}"
                )
            if self._zeros or (quantity > self._threshold):
                data[self._symbol][self._dimension,][index,] = quantity
```

### `or_algo/lp/solver.py`

**Imports:**

Remove `from .step import CreateConstrCalculateMetric`.

**Type annotations:**

All `Parameter` → `RegisterKey`, `Var` → `VarKey`.

**`__init__` — discard weight/lb/ub:**

```python
def __init__(self, name: str, solver_type: str = 'SCIP'):
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
```

**`append` — simplified:**

```python
def append(self, step: Type[LpStep], *args: Any, **kwargs: Any) -> None:
    from or_algo.lp.step import CreateVar, CreateConstr

    if issubclass(step, (CreateVar, CreateConstr)):
        self._build_steps.append((step, args, kwargs))
    else:
        raise exception.LpSolverException(
            f"Unsupported step type {step} in {type(self).__name__}.append()"
        )
```

**`solve` — remove auto-metric:**

```python
def solve(self, data: Register[RegisterKey]) -> Register[RegisterKey]:
    # No more self.append(CreateConstrCalculateMetric,)
    for step_type, args, kwargs in self._build_steps:
        try:
            step_type(*args, **kwargs).run(data, self._model, self._var)
        except Exception as e:
            raise exception.BuildLpStepException(
                f"Failed {step_type.__name__}.run()! args={args}, kwargs={kwargs}"
            ) from e
    # ... rest unchanged (model export, solve, status handling, publish)
```

### `or_algo/lp/__init__.py`

```python
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

Remove `Symbol` and `CreateConstrCalculateMetric` from exports.

## Testing Strategy

Update all test files with:
- `Parameter` → `RegisterKey`
- `Var` → `VarKey`, `Constr` → `ConstrKey`
- `Register[Parameter]` → `Register[RegisterKey]`
- Trailing comma convention on all dimension/index access
- Remove `CreateConstrCalculateMetric` tests
- Update `CreateVar` tests (no weight/lb/ub in constructor)
- Update `LpSolver` tests (no weight/lb/ub in constructor, simplified append)
- Update `Publish` tests (new target type)

## Files Modified

| File | Change Type |
|---|---|
| `or_algo/solver.py` | Type annotations |
| `or_algo/algorithm.py` | Type annotations |
| `or_algo/task.py` | Type annotations |
| `or_algo/lp/symbol.py` | Redesign (delete Symbol, VarKey/ConstrKey) |
| `or_algo/lp/step.py` | Redesign (delete CreateConstrCalculateMetric, simplify CreateVar, update Publish) |
| `or_algo/lp/solver.py` | Simplify (discard weight/lb/ub, simplify append, remove auto-metric) |
| `or_algo/lp/__init__.py` | Update exports |
| `tests/test_solver.py` | Type annotations |
| `tests/test_algorithm.py` | Type annotations |
| `tests/test_algorithm_parallel.py` | Type annotations |
| `tests/test_task.py` | Type annotations |
| `tests/conftest.py` | Type annotations |
| `tests/test_lp/test_symbol.py` | Redesign tests |
| `tests/test_lp/test_step.py` | Redesign tests |
| `tests/test_lp/test_solver.py` | Redesign tests |
