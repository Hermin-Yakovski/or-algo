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