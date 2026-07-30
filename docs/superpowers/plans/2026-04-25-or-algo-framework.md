# or-algo Framework Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a general-purpose algorithm framework for orchestrating solvers that operate on shared Register[Parameter] data

**Architecture:** Two-layer framework with Solver (abstract base class) and Algorithm (orchestrator). Users extend Solver for domain logic and use Algorithm to manage sequential execution. All solvers share the same Register for reading/writing data.

**Tech Stack:** Python 3.11+, Poetry, pytest, ruff, mypy, register package dependency

---

## File Structure

```
or-algo/
├── or_algo/
│   ├── __init__.py       # Package exports
│   ├── exception.py      # OrAlgoException base class
│   ├── solver.py         # Solver abstract base class
│   └── algorithm.py      # Algorithm orchestrator
├── tests/
│   ├── __init__.py       # Test package marker
│   ├── conftest.py       # Shared fixtures
│   ├── test_exception.py # Exception tests
│   ├── test_solver.py    # Solver tests
│   └── test_algorithm.py # Algorithm tests
├── pyproject.toml        # Poetry configuration
├── README.md             # Package documentation
└── .gitignore            # Git ignore patterns
```

---

### Task 1: Create project foundation files

**Files:**
- Create: `.gitignore`
- Create: `pyproject.toml`
- Create: `README.md`

- [ ] **Step 1: Create .gitignore**

```bash
cat > .gitignore << 'EOF'
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
PIPFILE.lock

# PyInstaller
*.manifest
*.spec

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDEs
.idea/
.vscode/
*.swp
*.swo
*~

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# ruff
.ruff_cache/
EOF
```

- [ ] **Step 2: Create pyproject.toml**

```bash
cat > pyproject.toml << 'EOF'
[tool.poetry]
name = "or-algo"
version = "0.1.0"
description = "A general-purpose algorithm framework for orchestrating solvers"
authors = ["yehemin <yehemin@example.com>"]
readme = "README.md"
packages = [{include = "or_algo"}]

[tool.poetry.dependencies]
python = "^3.11"
register = "0.1.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0"
ruff = "^0.8"
mypy = "^1.10"
pytest-cov = "^7.1.0"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_ignores = true

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
EOF
```

- [ ] **Step 3: Create README.md**

```bash
cat > README.md << 'EOF'
# or-algo

A general-purpose algorithm framework for orchestrating solvers that operate on shared data.

## Installation

```bash
pip install or-algo
```

## Quick Start

```python
from or_register import Register, Parameter
from or_algo import Solver, Algorithm

# Define your domain-specific solver
class MySolver(Solver):
    def solve(self, data: Register[Parameter]) -> None:
        # Read from and write to the Register
        pass

# Create an algorithm and add solvers
algo = Algorithm()
algo.append(MySolver)
algo.solve(your_register)
```

## Components

- **Solver**: Abstract base class for implementing solving logic
- **Algorithm**: Orchestrates sequential execution of multiple solvers
- **OrAlgoException**: Base exception for all package errors

## License

MIT
EOF
```

- [ ] **Step 4: Commit**

```bash
git add .gitignore pyproject.toml README.md
git commit -m "chore: add project foundation files"
```

---

### Task 2: Create package structure

**Files:**
- Create: `or_algo/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create or_algo package directory**

```bash
mkdir -p or_algo
```

- [ ] **Step 2: Create or_algo/__init__.py**

```python
"""or-algo: A general-purpose algorithm framework for orchestrating solvers."""

__version__ = "0.1.0"
```

- [ ] **Step 3: Create tests directory and __init__.py**

```bash
mkdir -p tests
cat > tests/__init__.py << 'EOF'
"""Tests for or-algo package."""
EOF
```

- [ ] **Step 4: Verify package structure**

Run: `python -c "import or_algo; print(or_algo.__version__)"`

Expected: `0.1.0`

- [ ] **Step 5: Commit**

```bash
git add or_algo/__init__.py tests/__init__.py
git commit -m "chore: create package structure"
```

---

### Task 3: Implement OrAlgoException (exception.py)

**Files:**
- Create: `or_algo/exception.py`
- Create: `tests/test_exception.py`

- [ ] **Step 1: Write the failing test for OrAlgoException**

Create `tests/test_exception.py`:

```python
"""Tests for or_algo.exception module."""

import pytest
from or_algo.exception import OrAlgoException


def test_or_algo_exception_creation():
    """Test that OrAlgoException can be created with a message."""
    exc = OrAlgoException("test error")
    assert str(exc) == "test error"
    assert isinstance(exc, Exception)


def test_or_algo_exception_as_base_class():
    """Test that OrAlgoException can be used as a base class."""
    class CustomError(OrAlgoException):
        pass

    exc = CustomError("custom message")
    assert isinstance(exc, OrAlgoException)
    assert isinstance(exc, Exception)
    assert str(exc) == "custom message"


def test_or_algo_exception_without_message():
    """Test that OrAlgoException can be created without a message."""
    exc = OrAlgoException()
    assert isinstance(exc, Exception)
    assert isinstance(exc, OrAlgoException)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_exception.py -v`

Expected: `ImportError: cannot import name 'OrAlgoException' from 'or_algo.exception'`

- [ ] **Step 3: Implement OrAlgoException**

Create `or_algo/exception.py`:

```python
"""Exception classes for or-algo package."""


class OrAlgoException(Exception):
    """Base exception for all or-algo package errors."""
    pass
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_exception.py -v`

Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add or_algo/exception.py tests/test_exception.py
git commit -m "feat: add OrAlgoException base class"
```

---

### Task 4: Implement Solver abstract class (solver.py)

**Files:**
- Create: `or_algo/solver.py`
- Create: `tests/test_solver.py`

- [ ] **Step 1: Write the failing test for Solver abstract class**

Create `tests/test_solver.py`:

```python
"""Tests for or_algo.solver module."""

import pytest
from or_register import Register, Parameter, Id
from or_algo.solver import Solver


def test_solver_cannot_be_instantiated_directly():
    """Test that Solver cannot be instantiated directly because it's abstract."""
    with pytest.raises(TypeError):
        Solver()


def test_solver_default_name():
    """Test that Solver uses class name as default name."""
    class MockSolver(Solver):
        def solve(self, data: Register[Parameter]) -> None:
            pass

    solver = MockSolver()
    assert solver.name == "MockSolver"


def test_solver_custom_name():
    """Test that Solver accepts custom name."""
    class MockSolver(Solver):
        def solve(self, data: Register[Parameter]) -> None:
            pass

    solver = MockSolver(name="CustomName")
    assert solver.name == "CustomName"


def test_solver_solve_requires_implementation():
    """Test that subclasses must implement solve()."""
    class IncompleteSolver(Solver):
        pass

    solver = IncompleteSolver()
    with pytest.raises(TypeError):
        solver.solve(Register[Parameter]())


def test_solver_solve_can_be_called():
    """Test that a properly implemented Solver can call solve()."""
    class WorkingSolver(Solver):
        def solve(self, data: Register[Parameter]) -> None:
            # Store a marker to verify solve was called
            data[Id][(Id,)] = (0, "solved")

    solver = WorkingSolver()
    register = Register[Parameter]()
    solver.solve(register)

    # Verify solve was executed
    assert (Id,) in register[Id]
    assert register[Id][(Id,)] == (0, "solved")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_solver.py -v`

Expected: `ImportError: cannot import name 'Solver' from 'or_algo.solver'`

- [ ] **Step 3: Implement Solver abstract class**

Create `or_algo/solver.py`:

```python
"""Solver abstract base class for or-algo package."""

from abc import ABC, abstractmethod
from or_register import Register, Parameter


class Solver(ABC):
    """Abstract base class for solvers that operate on a Register.

    Users extend this class to implement their solving logic.
    Each solver reads from and writes to a shared Register[Parameter].
    """

    def __init__(self, name: str | None = None) -> None:
        """Initialize the solver with an optional name.

        Args:
            name: Optional name for the solver. Defaults to the class name.
        """
        self._name = type(self).__name__ if name is None else name

    @property
    def name(self) -> str:
        """Get the solver's name."""
        return self._name

    @abstractmethod
    def solve(self, data: Register[Parameter]) -> None:
        """Solve the problem using data from the Register.

        Args:
            data: Register containing input parameters; solutions
                  are written back to this same Register.
        """
        pass
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_solver.py -v`

Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add or_algo/solver.py tests/test_solver.py
git commit -m "feat: add Solver abstract base class"
```

---

### Task 5: Implement Algorithm orchestrator (algorithm.py)

**Files:**
- Create: `or_algo/algorithm.py`
- Create: `tests/test_algorithm.py`

- [ ] **Step 1: Write the failing test for Algorithm**

Create `tests/test_algorithm.py`:

```python
"""Tests for or_algo.algorithm module."""

import pytest
from or_register import Register, Parameter, Id
from or_algo import Solver, Algorithm, OrAlgoException


class SuccessSolver(Solver):
    """A solver that always succeeds."""

    def __init__(self, marker: str = "default"):
        super().__init__()
        self.marker = marker
        self.called = False

    def solve(self, data: Register[Parameter]) -> None:
        self.called = True
        data[Id][(Id,)] = (0, self.marker)


class FailingSolver(Solver):
    """A solver that always fails."""

    def solve(self, data: Register[Parameter]) -> None:
        raise ValueError("intentional failure")


def test_algorithm_initialization():
    """Test that Algorithm can be initialized."""
    algo = Algorithm()
    assert algo is not None


def test_algorithm_append_returns_one_based_index():
    """Test that append() returns 1-based index."""
    algo = Algorithm()
    idx1 = algo.append(SuccessSolver)
    idx2 = algo.append(SuccessSolver)
    assert idx1 == 1
    assert idx2 == 2


def test_algorithm_solve_executes_solvers_in_order():
    """Test that solve() executes solvers in the order they were appended."""
    execution_order = []

    class OrderSolver(Solver):
        def __init__(self, marker: str):
            super().__init__()
            self.marker = marker

        def solve(self, data: Register[Parameter]) -> None:
            execution_order.append(self.marker)

    algo = Algorithm()
    algo.append(OrderSolver, "first")
    algo.append(OrderSolver, "second")
    algo.append(OrderSolver, "third")

    algo.solve(Register[Parameter]())
    assert execution_order == ["first", "second", "third"]


def test_algorithm_solve_stops_on_first_failure():
    """Test that solve() stops and raises on first solver failure."""
    execution_order = []

    class TrackingSolver(Solver):
        def __init__(self, marker: str):
            super().__init__()
            self.marker = marker

        def solve(self, data: Register[Parameter]) -> None:
            execution_order.append(self.marker)
            if self.marker == "fail":
                raise ValueError("intentional failure")

    algo = Algorithm()
    algo.append(TrackingSolver, "first")
    algo.append(TrackingSolver, "fail")
    algo.append(TrackingSolver, "never_reached")

    with pytest.raises(OrAlgoException) as exc_info:
        algo.solve(Register[Parameter]())

    # Verify execution stopped at failure
    assert execution_order == ["first", "fail"]

    # Verify original exception is chained
    assert isinstance(exc_info.value.__cause__, ValueError)
    assert "intentional failure" in str(exc_info.value.__cause__)


def test_algorithm_solve_with_solver_args():
    """Test that solver positional args are passed correctly."""
    class ConfiguredSolver(Solver):
        def __init__(self, value: int):
            super().__init__()
            self.value = value

        def solve(self, data: Register[Parameter]) -> None:
            data[Id][(Id,)] = (0, f"value={self.value}")

    algo = Algorithm()
    algo.append(ConfiguredSolver, 42)

    register = Register[Parameter]()
    algo.solve(register)

    assert register[Id][(Id,)] == (0, "value=42")


def test_algorithm_solve_with_solver_kwargs():
    """Test that solver keyword args are passed correctly."""
    class ConfiguredSolver(Solver):
        def __init__(self, value: int, flag: bool = False):
            super().__init__()
            self.value = value
            self.flag = flag

        def solve(self, data: Register[Parameter]) -> None:
            data[Id][(Id,)] = (0, f"value={self.value},flag={self.flag}")

    algo = Algorithm()
    algo.append(ConfiguredSolver, 42, flag=True)

    register = Register[Parameter]()
    algo.solve(register)

    assert register[Id][(Id,)] == (0, "value=42,flag=True")


def test_algorithm_solve_with_both_args_and_kwargs():
    """Test that both args and kwargs are passed correctly."""
    class ConfiguredSolver(Solver):
        def __init__(self, a: int, b: str, c: bool = False):
            super().__init__()
            self.a = a
            self.b = b
            self.c = c

        def solve(self, data: Register[Parameter]) -> None:
            data[Id][(Id,)] = (0, f"a={self.a},b={self.b},c={self.c}")

    algo = Algorithm()
    algo.append(ConfiguredSolver, 1, "two", c=True)

    register = Register[Parameter]()
    algo.solve(register)

    assert register[Id][(Id,)] == (0, "a=1,b=two,c=True")


def test_algorithm_exception_message():
    """Test that OrAlgoException includes useful information."""
    algo = Algorithm()
    algo.append(FailingSolver)

    with pytest.raises(OrAlgoException) as exc_info:
        algo.solve(Register[Parameter]())

    assert "FailingSolver" in str(exc_info.value)
    assert "solve()" in str(exc_info.value)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_algorithm.py -v`

Expected: `ImportError: cannot import name 'Algorithm' from 'or_algo.algorithm'`

- [ ] **Step 3: Implement Algorithm class**

Create `or_algo/algorithm.py`:

```python
"""Algorithm orchestrator class for or-algo package."""

from typing import Type
from or_register import Register, Parameter

from .solver import Solver
from .exception import OrAlgoException


class Algorithm:
    """Orchestrates sequential execution of multiple Solvers.

    Solvers are executed in the order they are appended. If any solver
    fails, execution stops and an OrAlgoException is raised.
    """

    def __init__(self, *args, **kwargs) -> None:
        """Initialize an empty Algorithm."""
        self._solvers: list[tuple[Type[Solver], tuple, dict]] = []

    def append(self, solver_type: Type[Solver], *args, **kwargs) -> int:
        """Add a solver to the execution sequence.

        Args:
            solver_type: The Solver class to instantiate and execute.
            *args: Positional arguments to pass to the solver constructor.
            **kwargs: Keyword arguments to pass to the solver constructor.

        Returns:
            The 1-based index of the solver in the sequence.
        """
        self._solvers.append((solver_type, args, kwargs))
        return len(self._solvers)

    def solve(self, data: Register[Parameter]) -> None:
        """Execute all solvers in sequence.

        Args:
            data: Register containing input parameters; solutions are
                  written back to this same Register.

        Raises:
            OrAlgoException: If any solver fails. The original exception
                            is chained as the cause.
        """
        for solver, args, kwargs in self._solvers:
            try:
                solver(*args, **kwargs).solve(data)
            except Exception as e:
                raise OrAlgoException(
                    f"Failed {solver.__name__}.solve()! args={args}, kwargs={kwargs}"
                ) from e
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_algorithm.py -v`

Expected: All 9 tests PASS

- [ ] **Step 5: Commit**

```bash
git add or_algo/algorithm.py tests/test_algorithm.py
git commit -m "feat: add Algorithm orchestrator class"
```

---

### Task 6: Create shared test fixtures (conftest.py)

**Files:**
- Create: `tests/conftest.py`

- [ ] **Step 1: Create conftest.py with shared fixtures**

```python
"""Shared fixtures for or-algo tests."""

import pytest
from or_register import Register, Parameter, Id, Code, Name


@pytest.fixture
def empty_register() -> Register[Parameter]:
    """Provide an empty Register for testing."""
    return Register[Parameter]()


@pytest.fixture
def sample_register() -> Register[Parameter]:
    """Provide a Register with sample data for testing."""
    reg = Register[Parameter]()
    # Add sample data as needed
    reg[Id][(Id,)] = (0, 1)
    reg[Code][(Code,)] = (0, "test_code")
    reg[Name][(Name,)] = (0, "test_name")
    return reg
```

- [ ] **Step 2: Verify fixtures work**

Run: `pytest tests/conftest.py -v`

Expected: No errors

- [ ] **Step 3: Update test_solver.py to use fixtures**

Edit `tests/test_solver.py`, update the last test:

```python
def test_solver_solve_can_be_called(empty_register):
    """Test that a properly implemented Solver can call solve()."""
    class WorkingSolver(Solver):
        def solve(self, data: Register[Parameter]) -> None:
            # Store a marker to verify solve was called
            data[Id][(Id,)] = (0, "solved")

    solver = WorkingSolver()
    solver.solve(empty_register)

    # Verify solve was executed
    assert (Id,) in empty_register[Id]
    assert empty_register[Id][(Id,)] == (0, "solved")
```

- [ ] **Step 4: Run tests to verify they still pass**

Run: `pytest tests/test_solver.py::test_solver_solve_can_be_called -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/conftest.py
git commit -m "test: add shared fixtures"
```

---

### Task 7: Update package exports (or_algo/__init__.py)

**Files:**
- Modify: `or_algo/__init__.py`
- Create: `tests/test_init.py`

- [ ] **Step 1: Write failing test for package exports**

Create `tests/test_init.py`:

```python
"""Tests for or_algo package imports."""

from or_algo import Solver, Algorithm, OrAlgoException


def test_solver_is_exported():
    """Test that Solver is exported from package."""
    assert Solver is not None
    assert Solver.__name__ == "Solver"


def test_algorithm_is_exported():
    """Test that Algorithm is exported from package."""
    assert Algorithm is not None
    assert Algorithm.__name__ == "Algorithm"


def test_or_algo_exception_is_exported():
    """Test that OrAlgoException is exported from package."""
    assert OrAlgoException is not None
    assert OrAlgoException.__name__ == "OrAlgoException"


def test_version_is_defined():
    """Test that package version is defined."""
    from or_algo import __version__
    assert __version__ == "0.1.0"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_init.py -v`

Expected: Some imports fail (Solver, Algorithm, OrAlgoException not yet exported)

- [ ] **Step 3: Update or_algo/__init__.py with exports**

```python
"""or-algo: A general-purpose algorithm framework for orchestrating solvers."""

from .solver import Solver
from .algorithm import Algorithm
from .exception import OrAlgoException

__version__ = "0.1.0"

__all__ = [
    "Solver",
    "Algorithm",
    "OrAlgoException",
]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_init.py -v`

Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add or_algo/__init__.py tests/test_init.py
git commit -m "feat: add package exports and version"
```

---

### Task 8: Run full test suite with coverage

**Files:**
- No file changes

- [ ] **Step 1: Install the register dependency wheel**

Run: `pip install D:/github/register/dist/register-0.1.0-py3-none-any.whl`

Expected: Package installed successfully

- [ ] **Step 2: Install poetry dependencies**

Run: `cd D:/github/or-algo && poetry install --with dev`

Expected: All dependencies installed

- [ ] **Step 3: Run full test suite**

Run: `poetry run pytest tests/ -v`

Expected: All tests PASS (17+ tests total)

- [ ] **Step 4: Run tests with coverage**

Run: `poetry run pytest tests/ --cov=or_algo --cov-report=term-missing`

Expected: 100% coverage for or_algo module

- [ ] **Step 5: Run ruff linting**

Run: `poetry run ruff check or_algo/ tests/`

Expected: No errors

- [ ] **Step 6: Run mypy type checking**

Run: `poetry run mypy or_algo/`

Expected: No errors (may need to add register stubs or ignore)

- [ ] **Step 7: Fix any mypy issues if needed**

If mypy fails with register import issues, add to pyproject.toml:

```toml
[[tool.mypy.overrides]]
module = "register"
ignore_missing_imports = true
```

Then re-run: `poetry run mypy or_algo/`

---

### Task 9: Build and verify package

**Files:**
- No file changes

- [ ] **Step 1: Build the package**

Run: `poetry build`

Expected: Creates `dist/or-algo-0.1.0.tar.gz` and `dist/or-algo-0.1.0-py3-none-any.whl`

- [ ] **Step 2: Verify wheel contents**

Run: `poetry run python -m zipfile -l dist/or-algo-0.1.0-py3-none-any.whl`

Expected: Shows all or_algo files and metadata

- [ ] **Step 3: Test install from wheel**

Run: `pip uninstall -y or-algo && pip install dist/or-algo-0.1.0-py3-none-any.whl`

Expected: Package installs successfully

- [ ] **Step 4: Verify installation works**

Run: `python -c "from or_algo import Solver, Algorithm, OrAlgoException; print('OK')"`

Expected: Prints "OK"

---

### Task 10: Final verification and cleanup

**Files:**
- No file changes

- [ ] **Step 1: Run full test suite one more time**

Run: `poetry run pytest tests/ -v --cov=or_algo`

Expected: All tests PASS, 100% coverage

- [ ] **Step 2: Verify git status**

Run: `git status`

Expected: No uncommitted changes

- [ ] **Step 3: Review all commits**

Run: `git log --oneline`

Expected: 9 commits showing incremental progress

- [ ] **Step 4: Create git tag for release**

Run: `git tag v0.1.0`

- [ ] **Step 5: Verification complete**

The or-algo package v0.1.0 is complete and ready for publication.
