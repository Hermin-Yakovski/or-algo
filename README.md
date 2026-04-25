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

## Components

- **Solver**: Abstract base class for implementing solving logic
- **Algorithm**: Orchestrates sequential execution of multiple solvers
- **OrAlgoException**: Base exception for all package errors

## License

MIT