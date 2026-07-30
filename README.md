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

## Parallel Execution (Beta)

The `Algorithm.parallel_solve()` method enables parallel execution of independent solvers using DAG-based dependency resolution.

### Basic Usage

```python
from concurrent.futures import ProcessPoolExecutor
from or_register import Register, Parameter
from or_algo import Algorithm

# Build dependency graph
algo = Algorithm()
id1 = algo.append(MySolver, "arg1")
id2 = algo.append(MySolver, "arg2")  # Independent
id3 = algo.append(MySolver, "arg3", after=[id1])  # Depends on id1

# Create register with type annotation
reg = Register[Parameter]()
reg["input"] = "value"

# Execute in parallel (modifies data in place)
with ProcessPoolExecutor(max_workers=4) as executor:
    algo.parallel_solve(reg, executor)

# Access results from the modified register
result = reg["output"]
```

### Dependencies

Specify solver dependencies using the `after` parameter:

```python
id_a = algo.append(SolverA)
id_b = algo.append(SolverB, after=[id_a])  # B waits for A
id_c = algo.append(SolverC, after=[id_a, id_b])  # C waits for A and B
```

### Notes

- **Beta API**: The parallel execution feature is in beta and may change.
- **Cycle Detection**: Raises `OrAlgoException` if dependency graph contains cycles.
- **Error Handling**: If any solver fails, pending tasks are cancelled and the exception is propagated.

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

## Components

- **Solver**: Abstract base class for implementing solving logic
- **Algorithm**: Orchestrates sequential execution of multiple solvers
- **OrAlgoException**: Base exception for all package errors

## License

MIT