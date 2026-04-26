# or-algo

A general-purpose algorithm framework for orchestrating solvers that operate on shared data.

## Installation

```bash
pip install or-algo
```

## Quick Start

```python
from register import Register, Parameter
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

## LP Module (OR-Tools)

The `or_algo.lp` module provides Linear Programming support using Google OR-Tools.

### Basic Usage

```python
from or_algo.lp import LpSolver, CreateVar, CreateConstr
from or_algo.lp.symbol import Var, Constr
from register import Register

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

## Components

- **Solver**: Abstract base class for implementing solving logic
- **Algorithm**: Orchestrates sequential execution of multiple solvers
- **OrAlgoException**: Base exception for all package errors

## License

MIT