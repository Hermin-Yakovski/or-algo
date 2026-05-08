# LP Module OR-Tools Refactoring Design

**Date:** 2026-04-26
**Status:** Approved
**Version:** 0.2.0

## Overview

Refactor the or-algo LP module from PySCIPOpt to Google OR-Tools for better ecosystem support and active maintenance. The refactoring maintains core architectural patterns (Register integration, step-based building, Symbol hierarchy) while replacing the underlying solver implementation.

## Motivation

Switch to OR-Tools for:
- **Better ecosystem/maintenance** - OR-Tools has more active development and community support
- **Built-in solvers** - GLOP (LP) and CBC (MIP) are included, no external dependencies
- **Simpler licensing** - Apache 2.0 vs PySCIPOpt's more complex licensing

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    or-algo Framework                    │
│  (Algorithm orchestrates Solver execution)              │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                      LpSolver                           │
│  (inherits from Solver, manages LP model building)      │
│  ┌─────────────────────────────────────────────────┐   │
│  │  _build_steps: CreateVar, CreateConstr          │   │
│  └─────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
        ┌─────────┐                 ┌──────────┐
        │  Var    │                 │ Constr   │
        │(Symbol) │                 │ (Symbol) │
        └─────────┘                 └──────────┘
              │                           │
              └───────────┬───────────────┘
                          ▼
              ┌──────────────────────────┐
              │  ortools.linear_solver   │
              │  (GLOP, CBC, etc.)       │
              └──────────────────────────┘
                          │
                          ▼
              ┌──────────────────────────┐
              │  Register[Parameter]     │
              │  (shared data interface) │
              └──────────────────────────┘
```

## Core Components

### Symbol Hierarchy (lp/symbol.py)

```python
class Symbol:
    """Base class for LP model elements."""
    _name: str
    _name_cn: str
    _sign: str
    vtype: Type

    def __init__(self, name: str, name_cn: str, sign: str):
        self._name = name
        self._name_cn = name_cn
        self._sign = sign

    @property
    def name(self) -> str: return self._name
    @property
    def name_cn(self) -> str: return self._name_cn
    @property
    def sign(self) -> str: return self._sign


class Var(Symbol):
    """Decision variable wrapper around OR-Tools Variable."""
    _parameter: Parameter

    def __init__(self, p: Parameter, sign: str):
        super().__init__(name=p.name, name_cn=p.name_cn, sign=sign)
        self._parameter = p
        self.vtype = pywraplp.Variable

    @property
    def id(self) -> int: return self._parameter.id
    @property
    def parameter(self) -> Parameter: return self._parameter


class Constr(Symbol):
    """Constraint wrapper around OR-Tools Constraint."""
    def __init__(self, name: str, name_cn: str, sign: str):
        super().__init__(name, name_cn, sign)
        self.vtype = pywraplp.Constraint
```

**Note:** No `Obj` class - OR-Tools handles objectives directly via `solver.Maximize()`/`solver.Minimize()`.

### LpStep Hierarchy (lp/step.py)

```python
class LpStep(ABC):
    """Abstract base class for LP model building steps."""
    def __init__(self, symbol: Symbol):
        super().__init__()
        self._symbol = symbol

    @abstractmethod
    def run(self, data: Register[Parameter], model: pywraplp.Solver,
            var: Register[Symbol]) -> None:
        """Execute this step to build the LP model."""
        pass


class CreateVar(LpStep, ABC):
    """Base class for variable creation steps."""
    _weight: Register[Symbol]
    _lb: Register[Symbol]
    _ub: Register[Symbol]

    def __init__(self, symbol: Var, weight: Register[Symbol],
                 lb: Register[Symbol], ub: Register[Symbol]):
        super().__init__(symbol)
        self._weight = weight
        self._lb = lb
        self._ub = ub

    @property
    def vtype(self) -> str:
        """Map Parameter vtype to OR-Tools variable type."""
        return {
            int: 'INTEGER',
            float: 'CONTINUOUS',
            bool: 'INTEGER',  # OR-Tools uses [0,1] integer for binary
        }[self._symbol.parameter.vtype]

    @abstractmethod
    def run(self, data: Register[Parameter], model: pywraplp.Solver,
            var: Register[Symbol]) -> None:
        pass


class CreateConstr(LpStep, ABC):
    """Base class for constraint creation steps."""
    def __init__(self, symbol: Constr):
        super().__init__(symbol)

    @abstractmethod
    def run(self, data: Register[Parameter], model: pywraplp.Solver,
            var: Register[Symbol]) -> None:
        pass
```

**Key OR-Tools mappings:**
- `Model` → `pywraplp.Solver`
- Variable types: `'I'/'C'/'B'` → `'INTEGER'/'CONTINUOUS'`
- `register` parameter renamed to `var` for clarity

### LpSolver Class (lp/solver.py)

```python
from ortools.linear_solver import pywraplp

class LpSolver(Solver):
    """Linear Programming solver using OR-Tools.

    Inherits from or-algo's Solver base class and integrates
    with Register[Parameter] for data flow.
    """

    _name: str
    _weight: Register[Symbol]
    _lb: Register[Symbol]
    _ub: Register[Symbol]
    _var: Register[Symbol]
    _build_steps: list[tuple[Type[LpStep], tuple, dict]]
    _model: pywraplp.Solver

    def __init__(
            self,
            name: str,
            weight: Register[Symbol] = None,
            lb: Register[Symbol] = None,
            ub: Register[Symbol] = None,
            solver_type: str = 'CBC'
    ):
        super().__init__(name)
        self._name = name
        self._weight = Register[Symbol]() if weight is None else weight
        self._lb = Register[Symbol]() if lb is None else lb
        self._ub = Register[Symbol]() if ub is None else ub
        self._var = Register[Symbol]()
        self._build_steps = list()
        self._model = pywraplp.Solver.CreateSolver(solver_type)
        if not self._model:
            raise exception.LpSolverException(
                f"Failed to create OR-Tools solver with type '{solver_type}'"
            )

    def solve(self, data: Register[Parameter]) -> Register[Parameter]:
        """Build and solve the LP model."""
        # Execute build steps
        for step_type, args, kwargs in self._build_steps:
            try:
                step_type(*args, **kwargs).run(data, self._model, self._var)
            except Exception as e:
                raise exception.BuildLpStepException(
                    f"Failed {step_type.__name__}.run()! args={args}, kwargs={kwargs}"
                ) from e

        # Solve the model
        status = self._model.Solve()

        # Handle OR-Tools status codes
        if status == pywraplp.Solver.OPTIMAL:
            pass  # Users handle solution extraction
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

        return data

    def append(self, step: Type[LpStep], *args, **kwargs):
        """Add a build step to the execution sequence."""
        if issubclass(step, CreateVar):
            # Fill args with (weight, lb, ub) if not provided
            args = args + (self._weight, self._lb, self._ub)[len(args):]
            self._build_steps.append((step, args, kwargs))
        elif issubclass(step, CreateConstr):
            self._build_steps.append((step, args, kwargs))
        else:
            raise exception.LpSolverException(
                f"Unsupported step type {step} in {type(self).__name__}.append()"
            )
```

**Key features:**
- Default solver: CBC (handles both LP and MIP)
- Solver created in `__init__()` with immediate validation
- Solution extraction left to user implementation
- `append()` auto-fills weight/lb/ub for CreateVar steps

### Exception Hierarchy (lp/exception.py)

```python
from .. import exception as base_exception

class LpSolverException(base_exception.OrAlgoException):
    """Base exception for LP solver errors."""
    pass


class BuildLpStepException(LpSolverException):
    """Raised when an LpStep fails during model building."""
    pass


class LpModelOptimizeException(LpSolverException):
    """Raised when model optimization fails or no solution is found."""
    pass
```

## Project Structure

```
or-algo/
├── or_algo/
│   ├── __init__.py              # Main package exports
│   ├── solver.py                # Base Solver class
│   ├── algorithm.py             # Algorithm orchestrator
│   ├── exception.py             # Base OrAlgoException
│   └── lp/
│       ├── __init__.py          # LP module exports
│       ├── exception.py         # LP-specific exceptions
│       ├── symbol.py            # Symbol, Var, Constr
│       ├── step.py              # LpStep, CreateVar, CreateConstr
│       └── solver.py            # LpSolver class
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_solver.py           # Base Solver tests
│   ├── test_algorithm.py        # Algorithm tests
│   └── test_lp/
│       ├── __init__.py
│       ├── conftest.py          # LP test fixtures
│       ├── test_symbol.py       # Symbol/Var/Constr tests
│       ├── test_step.py         # LpStep tests
│       └── test_solver.py       # LpSolver tests
├── pyproject.toml
└── README.md
```

## Dependencies

**pyproject.toml:**

```toml
[tool.poetry.dependencies]
python = "^3.11"
register = "0.1.0"
ortools = "^9.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0"
ruff = "^0.8"
mypy = "^1.10"
pytest-cov = "^7.1.0"
```

**Changes:**
- Add: `ortools = "^9.0"`
- Remove: `pyscipopt` (no longer needed)

## Package Exports

**or_algo/lp/__init__.py:**

```python
"""or-algo LP module: Linear Programming support using OR-Tools."""

from .symbol import Symbol, Var, Constr
from .step import LpStep, CreateVar, CreateConstr
from .solver import LpSolver
from . import exception

__all__ = [
    "Symbol",
    "Var",
    "Constr",
    "LpStep",
    "CreateVar",
    "CreateConstr",
    "LpSolver",
    "exception",
]
```

**or_algo/__init__.py (update):**

```python
"""or-algo: A general-purpose algorithm framework for orchestrating solvers."""

from .solver import Solver
from .algorithm import Algorithm
from .exception import OrAlgoException
from . import lp

__version__ = "0.2.0"

__all__ = [
    "Solver",
    "Algorithm",
    "OrAlgoException",
    "lp",
]
```

## OR-Tools API Mapping

| PySCIPOpt | OR-Tools | Notes |
|-----------|----------|-------|
| `Model()` | `pywraplp.Solver.CreateSolver()` | Factory method |
| `model.addVar()` | `solver.NumVar()`, `solver.IntVar()`, `solver.BoolVar()` | Type-specific methods |
| `model.addCons()` | `solver.Add()` | Simpler API |
| `model.setObjective()` | `solver.Maximize()`, `solver.Minimize()` | Direct methods |
| `model.optimize()` | `solver.Solve()` | Returns status enum |
| `model.getVal(var)` | `var.solution_value()` | Method on variable |
| `quicksum()` | Python `sum()` or direct expressions | Built-in |

## Solver Selection

| Solver | Type | Use Case |
|--------|------|----------|
| **GLOP** | LP | Pure continuous problems (fastest) |
| **CBC** | MIP | Mixed integer problems (default) |
| **PDLP** | LP | Large-scale problems |

Default: `CBC` (handles both LP and MIP adequately).

## Features Preserved

- ✅ Register-based integration (`Register[Parameter]`)
- ✅ Step-based model building (`LpStep` pattern)
- ✅ Symbol hierarchy (`Var`, `Constr`)
- ✅ Solver orchestration (`LpSolver` inherits `Solver`)

## Features Removed (Simplification)

- ❌ `PublishVars` / `PublishLpStep` - Solution extraction left to users
- ❌ Warm starts (`_warm`)
- ❌ Callbacks (`_callback`)
- ❌ Custom time limits
- ❌ Metric calculations (`SUM`, `MAX`, `MIN`, `RANGE`)
- ❌ `Obj` class - OR-Tools handles objectives directly

## Testing

Comprehensive testing for LP module:

- **test_symbol.py**: Symbol/Var/Constr creation and properties
- **test_step.py**: LpStep abstract enforcement, vtype mapping
- **test_solver.py**: LpSolver initialization, append(), solve(), status handling

Goal: 100% coverage for LP module code.

## Scope

### v0.2.0 (LP Module with OR-Tools)
- Core LP functionality with OR-Tools
- Symbol hierarchy (Var, Constr)
- LpStep base classes (CreateVar, CreateConstr)
- LpSolver with CBC/GLOP support
- Comprehensive test coverage

### Future Enhancements (Out of Scope)
- Advanced OR-Tools features (CP-SAT, routing)
- Solution extraction helpers
- Constraint definition helpers
- Model serialization/deserialization
