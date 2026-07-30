# LP Module OR-Tools Refactoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the or-algo LP module from PySCIPOpt to Google OR-Tools while preserving core architectural patterns.

**Architecture:** Direct translation approach - maintain Symbol hierarchy, LpStep pattern, and LpSolver orchestration while replacing PySCIPOpt APIs with OR-Tools equivalents (pywraplp.Solver, GLOP/CBC solvers).

**Tech Stack:** Python 3.11+, OR-Tools 9.0+, register 0.1.0, pytest, ruff, mypy

---

## File Structure

**New files to create:**
- `or_algo/lp/__init__.py` - LP module exports
- `or_algo/lp/exception.py` - LP-specific exceptions (LpSolverException, BuildLpStepException, LpModelOptimizeException)
- `or_algo/lp/symbol.py` - Symbol hierarchy (Symbol base, Var, Constr)
- `or_algo/lp/step.py` - LpStep hierarchy (LpStep base, CreateVar, CreateConstr)
- `or_algo/lp/solver.py` - LpSolver main class

**Files to modify:**
- `or_algo/__init__.py` - Add lp module exports, bump version to 0.2.0
- `pyproject.toml` - Add ortools dependency, remove pyscipopt (if present)

**Test files to create:**
- `tests/test_lp/__init__.py` - Test package marker
- `tests/test_lp/conftest.py` - Shared test fixtures
- `tests/test_lp/test_symbol.py` - Symbol/Var/Constr tests
- `tests/test_lp/test_step.py` - LpStep tests
- `tests/test_lp/test_solver.py` - LpSolver tests

---

### Task 1: Create LP module package structure

**Files:**
- Create: `or_algo/lp/__init__.py`

- [ ] **Step 1: Create LP module __init__.py with exports**

```python
"""or-algo LP module: Linear Programming support using OR-Tools."""

# Will be populated as we implement components
__all__ = []
```

- [ ] **Step 2: Verify package structure**

Run: `python -c "import or_algo.lp; print(or_algo.lp.__file__)"`
Expected: Path to `or_algo/lp/__init__.py`

- [ ] **Step 3: Commit**

```bash
git add or_algo/lp/__init__.py
git commit -m "feat: add lp module package structure"
```

---

### Task 2: Create LP exception hierarchy

**Files:**
- Create: `or_algo/lp/exception.py`
- Modify: `or_algo/lp/__init__.py`
- Test: `tests/test_lp/test_exception.py`

- [ ] **Step 1: Write failing test for exception hierarchy**

Create `tests/test_lp/test_exception.py`:

```python
import pytest
from or_algo.lp import exception
from or_algo import OrAlgoException


def test_lp_solver_exception_is_or_algo_exception():
    """LpSolverException should inherit from OrAlgoException."""
    exc = exception.LpSolverException("test")
    assert isinstance(exc, OrAlgoException)
    assert str(exc) == "test"


def test_build_lp_step_exception_is_lp_solver_exception():
    """BuildLpStepException should inherit from LpSolverException."""
    exc = exception.BuildLpStepException("build failed")
    assert isinstance(exc, exception.LpSolverException)
    assert isinstance(exc, OrAlgoException)
    assert str(exc) == "build failed"


def test_lp_model_optimize_exception_is_lp_solver_exception():
    """LpModelOptimizeException should inherit from LpSolverException."""
    exc = exception.LpModelOptimizeException("no solution")
    assert isinstance(exc, exception.LpSolverException)
    assert isinstance(exc, OrAlgoException)
    assert str(exc) == "no solution"


def test_exception_can_be_raised_and_caught():
    """Exceptions should work with normal exception handling."""
    with pytest.raises(exception.LpSolverException):
        raise exception.LpSolverException("test")

    with pytest.raises(exception.BuildLpStepException):
        raise exception.BuildLpStepException("build failed")

    with pytest.raises(exception.LpModelOptimizeException):
        raise exception.LpModelOptimizeException("no solution")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_lp/test_exception.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'or_algo.lp.exception'"

- [ ] **Step 3: Create exception.py with implementations**

Create `or_algo/lp/exception.py`:

```python
"""LP-specific exceptions for or-algo."""

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

- [ ] **Step 4: Update lp/__init__.py to export exceptions**

Modify `or_algo/lp/__init__.py`:

```python
"""or-algo LP module: Linear Programming support using OR-Tools."""

from . import exception

__all__ = [
    "exception",
]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_lp/test_exception.py -v`
Expected: PASS (4 tests passed)

- [ ] **Step 6: Commit**

```bash
git add or_algo/lp/exception.py or_algo/lp/__init__.py tests/test_lp/test_exception.py
git commit -m "feat: add LP exception hierarchy"
```

---

### Task 3: Create Symbol base class

**Files:**
- Create: `or_algo/lp/symbol.py`
- Modify: `or_algo/lp/__init__.py`
- Test: `tests/test_lp/test_symbol.py`

- [ ] **Step 1: Write failing test for Symbol base class**

Add to `tests/test_lp/test_symbol.py`:

```python
import pytest
from or_algo.lp.symbol import Symbol


def test_symbol_creation():
    """Symbol should store name, name_cn, and sign."""
    symbol = Symbol(name="test", name_cn="测试", sign="t")
    assert symbol.name == "test"
    assert symbol.name_cn == "测试"
    assert symbol.sign == "t"


def test_symbol_str_returns_sign():
    """Symbol.__str__ should return sign."""
    symbol = Symbol(name="test", name_cn="测试", sign="X")
    assert str(symbol) == "X"


def test_symbol_repr_returns_name():
    """Symbol.__repr__ should return name."""
    symbol = Symbol(name="test_var", name_cn="测试变量", sign="x")
    assert repr(symbol) == "test_var"


def test_symbol_has_vtype_attribute():
    """Symbol should have a vtype attribute (initially None)."""
    symbol = Symbol(name="test", name_cn="测试", sign="t")
    # vtype will be set by subclasses
    assert hasattr(symbol, 'vtype')
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_lp/test_symbol.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'or_algo.lp.symbol'"

- [ ] **Step 3: Create Symbol base class**

Create `or_algo/lp/symbol.py`:

```python
"""Symbol hierarchy for LP model elements."""

from typing import Type


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
        self.vtype = type(None)  # Placeholder, set by subclasses

    @property
    def name(self) -> str:
        return self._name

    @property
    def name_cn(self) -> str:
        return self._name_cn

    @property
    def sign(self) -> str:
        return self._sign

    def __str__(self):
        return self._sign

    def __repr__(self):
        return self._name
```

- [ ] **Step 4: Update lp/__init__.py to export Symbol**

Modify `or_algo/lp/__init__.py`:

```python
"""or-algo LP module: Linear Programming support using OR-Tools."""

from .symbol import Symbol
from . import exception

__all__ = [
    "Symbol",
    "exception",
]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_lp/test_symbol.py -v`
Expected: PASS (4 tests passed)

- [ ] **Step 6: Commit**

```bash
git add or_algo/lp/symbol.py or_algo/lp/__init__.py tests/test_lp/test_symbol.py
git commit -m "feat: add Symbol base class"
```

---

### Task 4: Create Var class

**Files:**
- Modify: `or_algo/lp/symbol.py`
- Modify: `or_algo/lp/__init__.py`
- Test: `tests/test_lp/test_symbol.py`

- [ ] **Step 1: Write failing test for Var class**

Add to `tests/test_lp/test_symbol.py`:

```python
from or_algo.lp.symbol import Var
from unittest.mock import Mock


def test_var_creation():
    """Var should wrap a Parameter."""
    mock_param = Mock()
    mock_param.name = "x_var"
    mock_param.name_cn = "x变量"
    mock_param.id = 42

    var = Var(p=mock_param, sign="x")
    assert var.name == "x_var"
    assert var.name_cn == "x变量"
    assert var.sign == "x"
    assert var.id == 42
    assert var.parameter is mock_param


def test_var_inherits_from_symbol():
    """Var should be a Symbol subclass."""
    mock_param = Mock()
    mock_param.name = "test"
    mock_param.name_cn = "测试"
    mock_param.id = 1

    var = Var(p=mock_param, sign="t")
    assert isinstance(var, Symbol)
    assert str(var) == "t"
    assert repr(var) == "test"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_lp/test_symbol.py::test_var_creation -v`
Expected: FAIL with "NameError: name 'Var' is not defined" or "cannot import 'Var'"

- [ ] **Step 3: Add Var class to symbol.py**

Add to `or_algo/lp/symbol.py`:

```python
"""Symbol hierarchy for LP model elements."""

from typing import Type
from or_register import Parameter  # or-algo dependency


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
        self.vtype = type(None)  # Placeholder, set by subclasses

    @property
    def name(self) -> str:
        return self._name

    @property
    def name_cn(self) -> str:
        return self._name_cn

    @property
    def sign(self) -> str:
        return self._sign

    def __str__(self):
        return self._sign

    def __repr__(self):
        return self._name


class Var(Symbol):
    """Decision variable wrapper around OR-Tools Variable."""

    _parameter: Parameter

    def __init__(self, p: Parameter, sign: str):
        super().__init__(name=p.name, name_cn=p.name_cn, sign=sign)
        self._parameter = p
        # vtype will be set to pywraplp.Variable when OR-Tools is imported

    @property
    def id(self) -> int:
        return self._parameter.id

    @property
    def parameter(self) -> Parameter:
        return self._parameter
```

- [ ] **Step 4: Update lp/__init__.py to export Var**

Modify `or_algo/lp/__init__.py`:

```python
"""or-algo LP module: Linear Programming support using OR-Tools."""

from .symbol import Symbol, Var
from . import exception

__all__ = [
    "Symbol",
    "Var",
    "exception",
]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_lp/test_symbol.py -v`
Expected: PASS (6 tests passed)

- [ ] **Step 6: Commit**

```bash
git add or_algo/lp/symbol.py or_algo/lp/__init__.py tests/test_lp/test_symbol.py
git commit -m "feat: add Var class"
```

---

### Task 5: Create Constr class

**Files:**
- Modify: `or_algo/lp/symbol.py`
- Modify: `or_algo/lp/__init__.py`
- Test: `tests/test_lp/test_symbol.py`

- [ ] **Step 1: Write failing test for Constr class**

Add to `tests/test_lp/test_symbol.py`:

```python
from or_algo.lp.symbol import Constr


def test_constr_creation():
    """Constr should store name, name_cn, and sign."""
    constr = Constr(name="capacity_limit", name_cn="容量限制", sign="cap")
    assert constr.name == "capacity_limit"
    assert constr.name_cn == "容量限制"
    assert constr.sign == "cap"


def test_constr_inherits_from_symbol():
    """Constr should be a Symbol subclass."""
    constr = Constr(name="test", name_cn="测试", sign="t")
    assert isinstance(constr, Symbol)
    assert str(constr) == "t"
    assert repr(constr) == "test"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_lp/test_symbol.py::test_constr_creation -v`
Expected: FAIL with "NameError: name 'Constr' is not defined" or "cannot import 'Constr'"

- [ ] **Step 3: Add Constr class to symbol.py**

Add to `or_algo/lp/symbol.py`:

```python
class Constr(Symbol):
    """Constraint wrapper around OR-Tools Constraint."""

    def __init__(self, name: str, name_cn: str, sign: str):
        super().__init__(name, name_cn, sign)
        # vtype will be set to pywraplp.Constraint when OR-Tools is imported
```

Add after the `Var` class definition.

- [ ] **Step 4: Update lp/__init__.py to export Constr**

Modify `or_algo/lp/__init__.py`:

```python
"""or-algo LP module: Linear Programming support using OR-Tools."""

from .symbol import Symbol, Var, Constr
from . import exception

__all__ = [
    "Symbol",
    "Var",
    "Constr",
    "exception",
]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_lp/test_symbol.py -v`
Expected: PASS (8 tests passed)

- [ ] **Step 6: Commit**

```bash
git add or_algo/lp/symbol.py or_algo/lp/__init__.py tests/test_lp/test_symbol.py
git commit -m "feat: add Constr class"
```

---

### Task 6: Create LpStep base class

**Files:**
- Create: `or_algo/lp/step.py`
- Modify: `or_algo/lp/__init__.py`
- Test: `tests/test_lp/test_step.py`

- [ ] **Step 1: Write failing test for LpStep base class**

Create `tests/test_lp/test_step.py`:

```python
import pytest
from abc import ABC
from or_algo.lp.step import LpStep
from or_algo.lp.symbol import Symbol


def test_lp_step_is_abstract():
    """LpStep should be an abstract base class."""
    assert issubclass(LpStep, ABC)

    # Cannot instantiate LpStep directly
    with pytest.raises(TypeError):
        LpStep(symbol=Symbol(name="test", name_cn="测试", sign="t"))


def test_lp_step_requires_run_method():
    """LpStep subclasses must implement the run method."""

    class InvalidStep(LpStep):
        pass  # Missing run() method

    with pytest.raises(TypeError):
        InvalidStep(symbol=Symbol(name="test", name_cn="测试", sign="t"))


def test_lp_step_concrete_subclass():
    """LpStep subclass with run() method should be instantiable."""

    class ConcreteStep(LpStep):
        def run(self, data, model, var):
            pass

    symbol = Symbol(name="test", name_cn="测试", sign="t")
    step = ConcreteStep(symbol=symbol)
    assert step._symbol is symbol
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_lp/test_step.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'or_algo.lp.step'"

- [ ] **Step 3: Create step.py with LpStep base class**

Create `or_algo/lp/step.py`:

```python
"""LpStep hierarchy for LP model building."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from or_register import Register
    from or_register import Parameter
    from or_algo.lp.symbol import Symbol
    from ortools.linear_solver import pywraplp


class LpStep(ABC):
    """Abstract base class for LP model building steps."""

    def __init__(self, symbol: "Symbol"):
        super().__init__()
        self._symbol = symbol

    @abstractmethod
    def run(
        self,
        data: "Register[Parameter]",
        model: "pywraplp.Solver",
        var: "Register[Symbol]"
    ) -> None:
        """Execute this step to build the LP model.

        Args:
            data: Register containing input parameters
            model: OR-Tools solver instance
            var: Register for storing variables/constraints
        """
        pass
```

- [ ] **Step 4: Update lp/__init__.py to export LpStep**

Modify `or_algo/lp/__init__.py`:

```python
"""or-algo LP module: Linear Programming support using OR-Tools."""

from .symbol import Symbol, Var, Constr
from .step import LpStep
from . import exception

__all__ = [
    "Symbol",
    "Var",
    "Constr",
    "LpStep",
    "exception",
]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_lp/test_step.py -v`
Expected: PASS (3 tests passed)

- [ ] **Step 6: Commit**

```bash
git add or_algo/lp/step.py or_algo/lp/__init__.py tests/test_lp/test_step.py
git commit -m "feat: add LpStep base class"
```

---

### Task 7: Create CreateVar base class

**Files:**
- Modify: `or_algo/lp/step.py`
- Modify: `or_algo/lp/__init__.py`
- Test: `tests/test_lp/test_step.py`

- [ ] **Step 1: Write failing test for CreateVar base class**

Add to `tests/test_lp/test_step.py`:

```python
from or_algo.lp.step import CreateVar
from or_algo.lp.symbol import Var
from or_register import Register
from unittest.mock import Mock


def test_create_var_is_lp_step():
    """CreateVar should be an LpStep subclass."""
    assert issubclass(CreateVar, LpStep)
    assert issubclass(CreateVar, ABC)


def test_create_var_cannot_be_instantiated_directly():
    """CreateVar should be abstract without run() implementation."""
    mock_param = Mock()
    mock_param.name = "x"
    mock_param.name_cn = "x变量"
    mock_param.id = 1
    mock_param.vtype = float

    var_symbol = Var(p=mock_param, sign="x")
    weight = Register()
    lb = Register()
    ub = Register()

    with pytest.raises(TypeError):
        CreateVar(symbol=var_symbol, weight=weight, lb=lb, ub=ub)


def test_create_var_concrete_subclass():
    """CreateVar subclass with run() should be instantiable."""
    from unittest.mock import Mock

    mock_param = Mock()
    mock_param.name = "x"
    mock_param.name_cn = "x变量"
    mock_param.id = 1
    mock_param.vtype = float

    var_symbol = Var(p=mock_param, sign="x")
    weight = Register()
    lb = Register()
    ub = Register()

    class ConcreteCreateVar(CreateVar):
        def run(self, data, model, var):
            pass

    step = ConcreteCreateVar(symbol=var_symbol, weight=weight, lb=lb, ub=ub)
    assert step._symbol is var_symbol
    assert step._weight is weight
    assert step._lb is lb
    assert step._ub is ub


def test_create_var_vtype_mapping():
    """CreateVar.vtype should map Parameter vtype to OR-Tools types."""
    from unittest.mock import Mock

    # Test float -> CONTINUOUS
    mock_param = Mock()
    mock_param.vtype = float
    var_float = Var(p=mock_param, sign="x")

    class ConcreteCreateVar(CreateVar):
        def run(self, data, model, var):
            pass

    step_float = ConcreteCreateVar(
        symbol=var_float,
        weight=Register(),
        lb=Register(),
        ub=Register()
    )
    assert step_float.vtype == 'CONTINUOUS'

    # Test int -> INTEGER
    mock_param.vtype = int
    var_int = Var(p=mock_param, sign="y")

    step_int = ConcreteCreateVar(
        symbol=var_int,
        weight=Register(),
        lb=Register(),
        ub=Register()
    )
    assert step_int.vtype == 'INTEGER'

    # Test bool -> INTEGER
    mock_param.vtype = bool
    var_bool = Var(p=mock_param, sign="z")

    step_bool = ConcreteCreateVar(
        symbol=var_bool,
        weight=Register(),
        lb=Register(),
        ub=Register()
    )
    assert step_bool.vtype == 'INTEGER'
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_lp/test_step.py::test_create_var_is_lp_step -v`
Expected: FAIL with "cannot import 'CreateVar'"

- [ ] **Step 3: Add CreateVar class to step.py**

Add to `or_algo/lp/step.py`:

```python
"""LpStep hierarchy for LP model building."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from or_register import Register
    from or_register import Parameter
    from or_algo.lp.symbol import Symbol, Var
    from ortools.linear_solver import pywraplp


class LpStep(ABC):
    """Abstract base class for LP model building steps."""

    def __init__(self, symbol: "Symbol"):
        super().__init__()
        self._symbol = symbol

    @abstractmethod
    def run(
        self,
        data: "Register[Parameter]",
        model: "pywraplp.Solver",
        var: "Register[Symbol]"
    ) -> None:
        """Execute this step to build the LP model."""
        pass


class CreateVar(LpStep, ABC):
    """Base class for variable creation steps."""

    _weight: "Register[Symbol]"
    _lb: "Register[Symbol]"
    _ub: "Register[Symbol]"

    def __init__(
        self,
        symbol: "Var",
        weight: "Register[Symbol]",
        lb: "Register[Symbol]",
        ub: "Register[Symbol]"
    ):
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
    def run(
        self,
        data: "Register[Parameter]",
        model: "pywraplp.Solver",
        var: "Register[Symbol]"
    ) -> None:
        """Create variables in the model."""
        pass
```

- [ ] **Step 4: Update lp/__init__.py to export CreateVar**

Modify `or_algo/lp/__init__.py`:

```python
"""or-algo LP module: Linear Programming support using OR-Tools."""

from .symbol import Symbol, Var, Constr
from .step import LpStep, CreateVar
from . import exception

__all__ = [
    "Symbol",
    "Var",
    "Constr",
    "LpStep",
    "CreateVar",
    "exception",
]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_lp/test_step.py -v`
Expected: PASS (7 tests passed)

- [ ] **Step 6: Commit**

```bash
git add or_algo/lp/step.py or_algo/lp/__init__.py tests/test_lp/test_step.py
git commit -m "feat: add CreateVar base class"
```

---

### Task 8: Create CreateConstr base class

**Files:**
- Modify: `or_algo/lp/step.py`
- Modify: `or_algo/lp/__init__.py`
- Test: `tests/test_lp/test_step.py`

- [ ] **Step 1: Write failing test for CreateConstr base class**

Add to `tests/test_lp/test_step.py`:

```python
from or_algo.lp.step import CreateConstr
from or_algo.lp.symbol import Constr


def test_create_constr_is_lp_step():
    """CreateConstr should be an LpStep subclass."""
    assert issubclass(CreateConstr, LpStep)
    assert issubclass(CreateConstr, ABC)


def test_create_constr_cannot_be_instantiated_directly():
    """CreateConstr should be abstract without run() implementation."""
    constr_symbol = Constr(name="limit", name_cn="限制", sign="L")

    with pytest.raises(TypeError):
        CreateConstr(symbol=constr_symbol)


def test_create_constr_concrete_subclass():
    """CreateConstr subclass with run() should be instantiable."""
    constr_symbol = Constr(name="limit", name_cn="限制", sign="L")

    class ConcreteCreateConstr(CreateConstr):
        def run(self, data, model, var):
            pass

    step = ConcreteCreateConstr(symbol=constr_symbol)
    assert step._symbol is constr_symbol
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_lp/test_step.py::test_create_constr_is_lp_step -v`
Expected: FAIL with "cannot import 'CreateConstr'"

- [ ] **Step 3: Add CreateConstr class to step.py**

Add to `or_algo/lp/step.py` after `CreateVar`:

```python
class CreateConstr(LpStep, ABC):
    """Base class for constraint creation steps."""

    def __init__(self, symbol: "Constr"):
        super().__init__(symbol)

    @abstractmethod
    def run(
        self,
        data: "Register[Parameter]",
        model: "pywraplp.Solver",
        var: "Register[Symbol]"
    ) -> None:
        """Create constraints in the model."""
        pass
```

- [ ] **Step 4: Update lp/__init__.py to export CreateConstr**

Modify `or_algo/lp/__init__.py`:

```python
"""or-algo LP module: Linear Programming support using OR-Tools."""

from .symbol import Symbol, Var, Constr
from .step import LpStep, CreateVar, CreateConstr
from . import exception

__all__ = [
    "Symbol",
    "Var",
    "Constr",
    "LpStep",
    "CreateVar",
    "CreateConstr",
    "exception",
]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_lp/test_step.py -v`
Expected: PASS (10 tests passed)

- [ ] **Step 6: Commit**

```bash
git add or_algo/lp/step.py or_algo/lp/__init__.py tests/test_lp/test_step.py
git commit -m "feat: add CreateConstr base class"
```

---

### Task 9: Create LpSolver class skeleton

**Files:**
- Create: `or_algo/lp/solver.py`
- Modify: `or_algo/lp/__init__.py`
- Test: `tests/test_lp/test_solver.py`

- [ ] **Step 1: Write failing test for LpSolver initialization**

Create `tests/test_lp/test_solver.py`:

```python
import pytest
from or_algo.lp.solver import LpSolver
from or_algo import Solver


def test_lp_solver_is_solver():
    """LpSolver should inherit from or-algo's Solver."""
    assert issubclass(LpSolver, Solver)


def test_lp_solver_initialization():
    """LpSolver should initialize with required parameters."""
    solver = LpSolver(name="test_solver")
    assert solver._name == "test_solver"
    assert solver.solver_type == 'CBC'
    assert solver._model is not None


def test_lp_solver_custom_solver_type():
    """LpSolver should accept custom solver_type."""
    solver = LpSolver(name="test_solver", solver_type='GLOP')
    assert solver.solver_type == 'GLOP'


def test_lp_solver_invalid_solver_type():
    """LpSolver should handle invalid solver_type gracefully."""
    # OR-Tools returns None for invalid solver types
    with pytest.raises(Exception):  # LpSolverException
        LpSolver(name="test_solver", solver_type='INVALID_SOLVER')


def test_lp_solver_has_weight_lb_ub_defaults():
    """LpSolver should create default Register for weight, lb, ub."""
    from or_register import Register
    from or_algo.lp import Symbol

    solver = LpSolver(name="test_solver")
    assert isinstance(solver._weight, Register)
    assert isinstance(solver._lb, Register)
    assert isinstance(solver._ub, Register)
    assert isinstance(solver._var, Register)


def test_lp_solver_custom_weight_lb_ub():
    """LpSolver should accept custom weight, lb, ub Registers."""
    from or_register import Register

    weight = Register()
    lb = Register()
    ub = Register()

    solver = LpSolver(name="test_solver", weight=weight, lb=lb, ub=ub)
    assert solver._weight is weight
    assert solver._lb is lb
    assert solver._ub is ub
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_lp/test_solver.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'or_algo.lp.solver'"

- [ ] **Step 3: Create solver.py with LpSolver skeleton**

Create `or_algo/lp/solver.py`:

```python
"""LpSolver: Linear Programming solver using OR-Tools."""

from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    from or_register import Register, Parameter
    from or_algo.lp.symbol import Symbol
    from ortools.linear_solver import pywraplp

from ortools.linear_solver import pywraplp
from or_algo.solver import Solver
from . import exception


class LpSolver(Solver):
    """Linear Programming solver using OR-Tools.

    Inherits from or-algo's Solver base class and integrates
    with Register[Parameter] for data flow.
    """

    _name: str
    _weight: "Register[Symbol]"
    _lb: "Register[Symbol]"
    _ub: "Register[Symbol]"
    _var: "Register[Symbol]"
    _build_steps: list[tuple[Type["LpStep"], tuple, dict]]
    _model: pywraplp.Solver
    _solver_type: str

    def __init__(
        self,
        name: str,
        weight: "Register[Symbol]" = None,
        lb: "Register[Symbol]" = None,
        ub: "Register[Symbol]" = None,
        solver_type: str = 'CBC'
    ):
        from or_register import Register

        super().__init__(name)
        self._name = name
        self._weight = Register() if weight is None else weight
        self._lb = Register() if lb is None else lb
        self._ub = Register() if ub is None else ub
        self._var = Register()
        self._build_steps = list()
        self._solver_type = solver_type

        self._model = pywraplp.Solver.CreateSolver(solver_type)
        if not self._model:
            raise exception.LpSolverException(
                f"Failed to create OR-Tools solver with type '{solver_type}'"
            )

    @property
    def solver_type(self) -> str:
        return self._solver_type
```

- [ ] **Step 4: Update lp/__init__.py to export LpSolver**

Modify `or_algo/lp/__init__.py`:

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

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_lp/test_solver.py -v`
Expected: PASS (6 tests passed)

- [ ] **Step 6: Commit**

```bash
git add or_algo/lp/solver.py or_algo/lp/__init__.py tests/test_lp/test_solver.py
git commit -m "feat: add LpSolver class skeleton"
```

---

### Task 10: Implement LpSolver.append() method

**Files:**
- Modify: `or_algo/lp/solver.py`
- Test: `tests/test_lp/test_solver.py`

- [ ] **Step 1: Write failing test for append() method**

Add to `tests/test_lp/test_solver.py`:

```python
from or_algo.lp.step import CreateVar, CreateConstr
from or_algo.lp.symbol import Var, Constr
from or_register import Register
from unittest.mock import Mock


def test_lp_solver_append_create_var():
    """LpSolver.append() should accept CreateVar steps."""
    solver = LpSolver(name="test_solver")

    mock_param = Mock()
    mock_param.name = "x"
    mock_param.name_cn = "x变量"
    mock_param.id = 1
    mock_param.vtype = float
    var_symbol = Var(p=mock_param, sign="x")

    class TestCreateVar(CreateVar):
        def run(self, data, model, var):
            pass

    initial_count = len(solver._build_steps)
    solver.append(TestCreateVar, var_symbol)
    assert len(solver._build_steps) == initial_count + 1


def test_lp_solver_append_create_var_auto_fills_args():
    """LpSolver.append() should auto-fill weight, lb, ub for CreateVar."""
    solver = LpSolver(name="test_solver")

    mock_param = Mock()
    mock_param.name = "x"
    mock_param.name_cn = "x变量"
    mock_param.id = 1
    mock_param.vtype = float
    var_symbol = Var(p=mock_param, sign="x")

    class TestCreateVar(CreateVar):
        def __init__(self, symbol, weight, lb, ub, custom_arg=None):
            super().__init__(symbol, weight, lb, ub)
            self.custom_arg = custom_arg

        def run(self, data, model, var):
            pass

    # Pass only symbol and custom_arg - weight, lb, ub should be auto-filled
    solver.append(TestCreateVar, var_symbol, custom_arg="test")
    step_type, args, kwargs = solver._build_steps[-1]

    assert args[0] is var_symbol  # symbol
    assert args[1] is solver._weight  # weight
    assert args[2] is solver._lb  # lb
    assert args[3] is solver._ub  # ub
    assert kwargs['custom_arg'] == "test"


def test_lp_solver_append_create_constr():
    """LpSolver.append() should accept CreateConstr steps."""
    solver = LpSolver(name="test_solver")

    constr_symbol = Constr(name="limit", name_cn="限制", sign="L")

    class TestCreateConstr(CreateConstr):
        def run(self, data, model, var):
            pass

    initial_count = len(solver._build_steps)
    solver.append(TestCreateConstr, constr_symbol)
    assert len(solver._build_steps) == initial_count + 1


def test_lp_solver_append_invalid_step_type():
    """LpSolver.append() should raise exception for unsupported step types."""
    solver = LpSolver(name="test_solver")

    class InvalidStep:
        pass

    with pytest.raises(Exception):  # LpSolverException
        solver.append(InvalidStep)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_lp/test_solver.py::test_lp_solver_append_create_var -v`
Expected: FAIL with "AttributeError: 'LpSolver' object has no attribute 'append'" or append() not implemented correctly

- [ ] **Step 3: Implement append() method**

Add to `or_algo/lp/solver.py`:

```python
    def append(self, step: Type["LpStep"], *args, **kwargs) -> None:
        """Add a build step to the execution sequence.

        Args:
            step: LpStep subclass (CreateVar or CreateConstr)
            *args, **kwargs: Arguments to pass to step.__init__()

        Raises:
            LpSolverException: If step type is unsupported
        """
        from or_algo.lp.step import CreateVar, CreateConstr

        if issubclass(step, CreateVar):
            # Fill args with (weight, lb, ub) if not provided
            full_args = args + (self._weight, self._lb, self._ub)[len(args):]
            self._build_steps.append((step, full_args, kwargs))
        elif issubclass(step, CreateConstr):
            self._build_steps.append((step, args, kwargs))
        else:
            raise exception.LpSolverException(
                f"Unsupported step type {step} in {type(self).__name__}.append()"
            )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_lp/test_solver.py -v`
Expected: PASS (10 tests passed)

- [ ] **Step 5: Commit**

```bash
git add or_algo/lp/solver.py tests/test_lp/test_solver.py
git commit -m "feat: implement LpSolver.append() method"
```

---

### Task 11: Implement LpSolver.solve() method - build steps

**Files:**
- Modify: `or_algo/lp/solver.py`
- Test: `tests/test_lp/test_solver.py`

- [ ] **Step 1: Write failing test for solve() build step execution**

Add to `tests/test_lp/test_solver.py`:

```python
from or_register import Register, Parameter


def test_lp_solver_solve_executes_build_steps():
    """LpSolver.solve() should execute build steps in order."""
    from unittest.mock import Mock, MagicMock

    solver = LpSolver(name="test_solver")

    # Mock the steps
    executed_steps = []

    class Step1(CreateVar):
        def run(self, data, model, var):
            executed_steps.append('step1')

    class Step2(CreateConstr):
        def run(self, data, model, var):
            executed_steps.append('step2')

    mock_param = Mock()
    mock_param.name = "x"
    mock_param.name_cn = "x变量"
    mock_param.id = 1
    mock_param.vtype = float
    var_symbol = Var(p=mock_param, sign="x")
    constr_symbol = Constr(name="limit", name_cn="限制", sign="L")

    solver.append(Step1, var_symbol)
    solver.append(Step2, constr_symbol)

    # Create mock data var
    data = Register[Parameter]()

    # Mock the model.optimize() to return OPTIMAL
    solver._model.Solve = Mock(return_value=pywraplp.Solver.OPTIMAL)

    # Solve
    result = solver.solve(data)

    assert executed_steps == ['step1', 'step2']
    assert result is data  # Should return the same var


def test_lp_solver_solve_build_step_exception():
    """LpSolver.solve() should wrap build step exceptions."""
    class FailingStep(CreateVar):
        def run(self, data, model, var):
            raise ValueError("Step failed!")

    solver = LpSolver(name="test_solver")

    mock_param = Mock()
    mock_param.name = "x"
    mock_param.name_cn = "x变量"
    mock_param.id = 1
    mock_param.vtype = float
    var_symbol = Var(p=mock_param, sign="x")

    solver.append(FailingStep, var_symbol)

    data = Register[Parameter]()

    # Mock the model.optimize() to return OPTIMAL (won't be reached)
    solver._model.Solve = Mock(return_value=pywraplp.Solver.OPTIMAL)

    # Should raise BuildLpStepException
    with pytest.raises(Exception):  # BuildLpStepException
        solver.solve(data)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_lp/test_solver.py::test_lp_solver_solve_executes_build_steps -v`
Expected: FAIL with "AttributeError: 'LpSolver' object has no attribute 'solve'" or solve() not implemented correctly

- [ ] **Step 3: Implement solve() method with build step execution**

Add to `or_algo/lp/solver.py`:

```python
    def solve(self, data: "Register[Parameter]") -> "Register[Parameter]":
        """Build and solve the LP model.

        Args:
            data: Register containing input parameters

        Returns:
            The same Register (users can extract solutions via their own mechanisms)

        Raises:
            BuildLpStepException: If a build step fails
            LpModelOptimizeException: If optimization fails or no solution is found
        """
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_lp/test_solver.py -v`
Expected: PASS (12 tests passed)

- [ ] **Step 5: Commit**

```bash
git add or_algo/lp/solver.py tests/test_lp/test_solver.py
git commit -m "feat: implement LpSolver.solve() method with build step execution"
```

---

### Task 12: Implement LpSolver.solve() status handling tests

**Files:**
- Test: `tests/test_lp/test_solver.py`

- [ ] **Step 1: Write tests for all OR-Tools status codes**

Add to `tests/test_lp/test_solver.py`:

```python
def test_lp_solver_solve_optimal_status():
    """LpSolver.solve() should handle OPTIMAL status."""
    solver = LpSolver(name="test_solver")
    data = Register[Parameter]()

    solver._model.Solve = Mock(return_value=pywraplp.Solver.OPTIMAL)

    # Should not raise, should return data
    result = solver.solve(data)
    assert result is data


def test_lp_solver_solve_infeasible_status():
    """LpSolver.solve() should raise exception for INFEASIBLE status."""
    solver = LpSolver(name="test_solver")
    data = Register[Parameter]()

    solver._model.Solve = Mock(return_value=pywraplp.Solver.INFEASIBLE)

    with pytest.raises(Exception):  # LpModelOptimizeException
        solver.solve(data)


def test_lp_solver_solve_unbounded_status():
    """LpSolver.solve() should raise exception for UNBOUNDED status."""
    solver = LpSolver(name="test_solver")
    data = Register[Parameter]()

    solver._model.Solve = Mock(return_value=pywraplp.Solver.UNBOUNDED)

    with pytest.raises(Exception):  # LpModelOptimizeException
        solver.solve(data)


def test_lp_solver_solve_not_solved_status():
    """LpSolver.solve() should raise exception for NOT_SOLVED status."""
    solver = LpSolver(name="test_solver")
    data = Register[Parameter]()

    solver._model.Solve = Mock(return_value=pywraplp.Solver.NOT_SOLVED)

    with pytest.raises(Exception):  # LpModelOptimizeException
        solver.solve(data)


def test_lp_solver_solve_abnormal_status():
    """LpSolver.solve() should raise exception for ABNORMAL status."""
    solver = LpSolver(name="test_solver")
    data = Register[Parameter]()

    solver._model.Solve = Mock(return_value=pywraplp.Solver.ABNORMAL)

    with pytest.raises(Exception):  # LpModelOptimizeException
        solver.solve(data)
```

- [ ] **Step 2: Run test to verify it passes**

Run: `pytest tests/test_lp/test_solver.py -v`
Expected: PASS (17 tests passed)

- [ ] **Step 3: Commit**

```bash
git add tests/test_lp/test_solver.py
git commit -m "test: add LpSolver.solve() status handling tests"
```

---

### Task 13: Update main package exports

**Files:**
- Modify: `or_algo/__init__.py`

- [ ] **Step 1: Update or_algo/__init__.py to export lp module and bump version**

Modify `or_algo/__init__.py`:

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

- [ ] **Step 2: Verify lp module is accessible**

Run: `python -c "from or_algo import lp; print(dir(lp))"`
Expected: List containing 'Symbol', 'Var', 'Constr', 'LpStep', 'CreateVar', 'CreateConstr', 'LpSolver', 'exception'

- [ ] **Step 3: Commit**

```bash
git add or_algo/__init__.py
git commit -m "feat: export lp module from main package, bump version to 0.2.0"
```

---

### Task 14: Update dependencies in pyproject.toml

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add ortools dependency to pyproject.toml**

Modify `pyproject.toml`:

```toml
[tool.poetry.dependencies]
python = "^3.11"
register = "0.1.0"
ortools = "^9.0"
```

If `pyscipopt` is present, remove it:
```toml
# pyscipopt = "^X.X.X"  # Remove this line if present
```

- [ ] **Step 2: Install ortools dependency**

Run: `poetry lock` followed by `poetry install`

- [ ] **Step 3: Verify ortools installation**

Run: `python -c "from ortools.linear_solver import pywraplp; print(pywraplp.Solver.CreateSolver('CBC'))"`
Expected: No error, OR-Tools solver created

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml poetry.lock
git commit -m "deps: add ortools ^9.0, remove pyscipopt"
```

---

### Task 15: Run full test suite and verify coverage

**Files:**
- Test: All test files

- [ ] **Step 1: Run full LP module test suite**

Run: `pytest tests/test_lp/ -v`

Expected: All tests pass (17+ tests)

- [ ] **Step 2: Run tests with coverage**

Run: `pytest tests/test_lp/ --cov=or_algo/lp --cov-report=term-missing`

Expected: Coverage report showing >90% coverage

- [ ] **Step 3: Run entire test suite to ensure no regressions**

Run: `pytest tests/ -v`

Expected: All tests pass (both existing or-algo tests and new LP tests)

- [ ] **Step 4: Run type checking**

Run: `mypy or_algo/lp/`

Expected: No type errors (may need to add `mypy.ini` or update existing config)

- [ ] **Step 5: Run linting**

Run: `ruff check or_algo/lp/`

Expected: No linting errors

- [ ] **Step 6: Commit any fixes**

If any issues found:
```bash
git add or_algo/lp/ tests/test_lp/
git commit -m "fix: address test coverage, type checking, or linting issues"
```

---

### Task 16: Create integration example (optional)

**Files:**
- Create: `examples/lp_example.py` (optional, for documentation)

- [ ] **Step 1: Create simple LP example**

Create `examples/lp_example.py`:

```python
"""Example: Simple LP problem using or-algo LP module with OR-Tools.

Maximize: 3*x + 2*y
Subject to:
    x + y <= 10
    x >= 0
    y >= 0
"""

from or_register import Register, Parameter
from or_algo import Algorithm
from or_algo.lp import LpSolver, CreateVar, CreateConstr
from or_algo.lp.symbol import Var, Constr
from ortools.linear_solver import pywraplp


class CreateXVar(CreateVar):
    """Create variable x."""
    def run(self, data, model, var):
        x = model.NumVar(0, model.infinity(), "x")
        var[self._symbol][0,] = x


class CreateYVar(CreateVar):
    """Create variable y."""
    def run(self, data, model, var):
        y = model.NumVar(0, model.infinity(), "y")
        var[self._symbol][0,] = y


class CreateCapacityConstraint(CreateConstr):
    """Create constraint: x + y <= 10."""
    def run(self, data, model, var):
        # This is a simplified example - real usage would access
        # variables from the var var
        pass


# Note: This is a skeletal example showing the API structure.
# Full implementation would require Register integration and
# proper variable/constraint creation logic.

if __name__ == "__main__":
    # Create algorithm
    algo = Algorithm()

    # Add LP solver step
    # (Full example would use concrete CreateVar/CreateConstr implementations)
    pass
```

- [ ] **Step 2: Commit**

```bash
git add examples/lp_example.py
git commit -m "docs: add LP module integration example"
```

---

### Task 17: Update README documentation

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add LP module section to README**

Add to `README.md`:

```markdown
## LP Module (OR-Tools)

The `or_algo.lp` module provides Linear Programming support using Google OR-Tools.

### Basic Usage

```python
from or_algo.lp import LpSolver, CreateVar, CreateConstr
from or_algo.lp.symbol import Var, Constr
from or_register import Register

# Create LP solver (defaults to CBC)
solver = LpSolver(name="my_lp_problem")

# Add variable creation steps
# solver.append(CreateVar, var_symbol, ...)

# Add constraint creation steps
# solver.append(CreateConstr, constr_symbol, ...)

# Solve
data = Register[Parameter]()
solver.solve(data)
```

### Supported Solvers

- **CBC** (default): Mixed Integer Programming
- **GLOP**: Linear Programming (continuous only)

Specify solver type: `LpSolver(name="my_lp", solver_type='GLOP')`

### Components

- **Symbol, Var, Constr**: Type-safe wrappers for model elements
- **LpStep, CreateVar, CreateConstr**: Abstract base classes for model building
- **LpSolver**: Main solver class inheriting from `or_algo.Solver`
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add LP module documentation to README"
```

---

## Completion Checklist

After all tasks are complete:

- [ ] All tests pass: `pytest tests/ -v`
- [ ] Coverage >90%: `pytest tests/ --cov=or_algo --cov-report=term`
- [ ] Type checking passes: `mypy or_algo/`
- [ ] Linting passes: `ruff check or_algo/`
- [ ] Documentation updated: README.md includes LP module
- [ ] Version bumped: or_algo.__version__ == "0.2.0"
- [ ] Dependencies updated: ortools added, pyscipopt removed
