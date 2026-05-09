"""or-algo: A general-purpose algorithm framework for orchestrating solvers."""

from .solver import Solver
from .algorithm import Algorithm
from .exception import OrAlgoException
from .task import SolverTask
from .shared_register import SharedRegister

__version__ = "0.2.0"

__all__ = [
    "Solver",
    "Algorithm",
    "OrAlgoException",
    "lp",
    "SolverTask",
    "SharedRegister",
]


def __getattr__(name: str):
    """Lazy import lp module to avoid ortools import issues in multiprocessing."""
    if name == "lp":
        from . import lp
        return lp
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
