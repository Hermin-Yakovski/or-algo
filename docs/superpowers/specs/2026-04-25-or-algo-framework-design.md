# or-algo Framework Design

**Date:** 2026-04-25
**Status:** Approved
**Version:** 0.1.0

## Overview

A general-purpose algorithm framework for orchestrating solvers that operate on shared `Register[Parameter]` data. Users implement domain-specific `Solver` subclasses and organize them in `Algorithm` instances; the framework manages sequential execution.

## Architecture

Two-layer architecture:

1. **Solver Layer** - Abstract base class extended by users to implement solving logic
2. **Algorithm Layer** - Orchestrator that manages and executes solvers in sequence
3. **Exception Layer** - Base exception for all package errors

```
┌─────────────────────────────────────┐
│           Algorithm                 │
│  (orchestrates solver execution)    │
└─────────────────┬───────────────────┘
                  │
      ┌───────────┴───────────┐
      │                       │
      ▼                       ▼
┌──────────┐            ┌──────────┐
│ Solver A │    ...     │ Solver B │
│(user impl)│            │(user impl)│
└──────────┘            └──────────┘
      │                       │
      └───────────┬───────────┘
                  ▼
         ┌────────────────┐
         │  Register[P]   │
         │  (shared data) │
         └────────────────┘
```

## Core Components

### OrAlgoException (exception.py)
Base exception for all or-algo package errors.

```python
class OrAlgoException(Exception):
    """Base exception for all or-algo package errors."""
    pass
```

### Solver (solver.py)
Abstract base class for solvers that operate on a Register.

```python
from abc import ABC, abstractmethod
from register import Register, Parameter

class Solver(ABC):
    """Abstract base class for solvers that operate on a Register."""

    def __init__(self, name: str | None = None):
        self._name = type(self).__name__ if name is None else name

    @property
    def name(self) -> str:
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

### Algorithm (algorithm.py)
Orchestrates sequential execution of multiple Solvers.

```python
from typing import Type
from register import Register, Parameter

class Algorithm:
    """Orchestrates sequential execution of multiple Solvers."""

    def __init__(self, *args, **kwargs) -> None:
        self._solvers: list[tuple[Type[Solver], tuple, dict]] = []

    def append(self, solver_type: Type[Solver], *args, **kwargs) -> int:
        """Add a solver to the execution sequence.

        Returns:
            The 1-based index of the solver in the sequence.
        """
        self._solvers.append((solver_type, args, kwargs))
        return len(self._solvers)

    def solve(self, data: Register[Parameter]) -> None:
        """Execute all solvers in sequence.

        Raises:
            OrAlgoException: If any solver fails.
        """
        for solver, args, kwargs in self._solvers:
            try:
                solver(*args, **kwargs).solve(data)
            except Exception as e:
                raise OrAlgoException(
                    f"Failed {solver.__name__}.solve()! args={args}, kwargs={kwargs}"
                ) from e
```

## Project Structure

```
or-algo/
├── or_algo/
│   ├── __init__.py
│   ├── solver.py
│   ├── algorithm.py
│   └── exception.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_solver.py
│   ├── test_algorithm.py
│   └── test_exception.py
├── pyproject.toml
├── README.md
└── .gitignore
```

## Configuration

### pyproject.toml
```toml
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
```

## Testing

Comprehensive testing with 100% line coverage goal.

### Coverage Areas
- **test_exception.py**: Exception creation and inheritance
- **test_solver.py**: Abstract class enforcement, naming, instantiation
- **test_algorithm.py**: Sequential execution, error handling, args/kwargs passing

### Key Test Cases
- Solver cannot be instantiated directly (abstract)
- Solver default name vs custom name
- Algorithm returns 1-based indices
- Algorithm executes solvers in order
- Algorithm stops on first failure and wraps exception

## Package Exports

```python
# or_algo/__init__.py
from .solver import Solver
from .algorithm import Algorithm
from .exception import OrAlgoException

__all__ = [
    "Solver",
    "Algorithm",
    "OrAlgoException",
]
```

## Scope

### v0.1.0 (Initial Release)
- Basic sequential solver execution
- Simple exception handling
- Comprehensive test coverage

### Future Enhancements (Out of Scope)
- Communication between solvers (shared context/state)
- Multiprocessing support
- Parallel solver execution
- Advanced error recovery

## Dependencies

- **register** (0.1.0): Multi-dimensional data registry with `Register[Parameter]` type
- **Python**: ^3.11

## Documentation Level

Minimal: docstrings in code + simple README with usage example.
