"""LP-specific exceptions for or-algo."""

from .. import exception as base_exception


class LpSolverException(base_exception.OrAlgoException):
    """Base exception for LP solver errors."""


class BuildLpStepException(LpSolverException):
    """Raised when an LpStep fails during model building."""


class LpModelOptimizeException(LpSolverException):
    """Raised when model optimization fails or no solution is found."""
