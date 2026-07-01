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
| 7 | `reg.select(v, dims, prefix)` | `reg[v][dims,][*prefix, :]` |
| 8 | `space.get(idx, default)` | `space[idx,] if idx in space else default` |
| 9 | `reg[k][(d1, d2)][(0, 1)]` | `reg[k][d1, d2,][0, 1,]` |

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

**`VarKey(RegisterKey)`:**

```python
class VarKey(RegisterKey):
    _parameter: NumKey
    _sign: str

    def __init__(self, p: NumKey, sign: str):
        self._parameter = p
        self._sign = sign

    @property
    def id(self) -> int:
        return self._parameter.id

    @property
    def name(self) -> str:
        return self._parameter.name

    @property
    def name_cn(self) -> str:
        return self._parameter.name_cn

    @property
    def sign(self) -> str:
        return self._sign

    @property
    def parameter(self) -> NumKey:
        return self._parameter

    def validate(self, selected: Selected, **kwargs) -> dict[tuple[int, ...], bool]:
        return {k: isinstance(v, pywraplp.Variable) for k, v in selected.items()}
```

- `id`, `name`, `name_cn` delegated to wrapped `NumKey`
- `sign` is own field
- `validate` checks `isinstance(v, pywraplp.Variable)`
- Inherits `__hash__`/`__eq__` from `_BaseKey`

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

Discard `weight`, `lb`, `ub` from `__init__` and fields:

```python
class CreateVar(LpStep, ABC):
    _symbol: VarKey

    def __init__(self, symbol: VarKey):
        super().__init__(symbol)
```

`vtype` property — docstring/error message updates only (`Parameter` → `NumKey`).

`_create` signature:

```python
def _create(self,
    data: Register[RegisterKey],
    model: pywraplp.Solver,
    var: Register[VarKey],
    primary_key: RegisterKey,
    dimension: Tuple[Dimension, ...],
    weight: float = 0,
    lb: float = 0,
    ub: Optional[float] = None,
    *,
    min_weight: float = 1e-6,
    metric: Optional[int] = None,
    which: Optional[Tuple[bool, ...]] = None,
    sense: str = 'minimize',
    clear: bool = False,
    skip: Optional[Callable[[tuple[int, ...]], bool]] = None,
) -> int:
```

`_create` body — simplified (no more `self._weight`/`self._lb`/`self._ub` lookups):

```python
# Pop old dimension data — unchanged
data[self._symbol.parameter].pop(dimension_final,)

# Iterate primary key per dimension
# Old: data.select(primary_key, (d,))
# New:
data[primary_key][d,].keys()

# Wildcard index
# Old: Register.ALL
# New:
slice(None)

# Bounds and weight — used directly from parameters, no register lookups
lb_ = lb
ub_ = ub if ub is not None else model.infinity()
weight_ = weight

# Write variable to register
var[self._symbol][dimension_final,][index_final,] = variable
```

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
            parameter = self._symbol.parameter
            quantity = register[self._symbol][self._dimension,][index,].solution_value()
            if parameter.vtype is int:
                quantity = int(round(quantity, 0))
            elif parameter.vtype is bool:
                quantity = bool(round(quantity, 0))
            elif parameter.vtype is float:
                pass
            else:
                raise exception.BuildLpStepException(
                    f"Unsupported vtype {parameter.vtype} while publishing variable {self._symbol.name}"
                )
            if self._zeros or (quantity > self._threshold):
                key = self._symbol.parameter
                data[key][self._dimension,][index,] = quantity
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
