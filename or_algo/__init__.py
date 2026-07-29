"""or-algo: A general-purpose algorithm framework for orchestrating solvers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .algorithm import Algorithm
from .exception import OrAlgoException
from .solver import Solver
from .task import SolverTask

if TYPE_CHECKING:
    from types import ModuleType

__version__ = "0.2.0"

__all__ = [
    "Algorithm",
    "OrAlgoException",
    "Solver",
    "SolverTask",
    "lp",
]


def __getattr__(name: str) -> ModuleType:
    """Lazy import lp module to avoid ortools import issues in multiprocessing."""
    if name == "lp":
        from . import lp

        return lp
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
