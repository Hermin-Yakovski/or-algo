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