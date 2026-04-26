import pytest
from or_algo.lp import exception
from or_algo import OrAlgoException


def test_lp_solver_exception_is_or_algo_exception():
    """LpSolverException should inherit from OrAlgoException."""
    exc = exception.LpSolverException("test")
    assert isinstance(exc, OrAlgoException)
    assert str(exc) == "test"


def test_build_lp_step_exception_is_lp_solver_exception():
    """BuildLpStepException should inherit from LpSolverException."""
    exc = exception.BuildLpStepException("build failed")
    assert isinstance(exc, exception.LpSolverException)
    assert isinstance(exc, OrAlgoException)
    assert str(exc) == "build failed"


def test_lp_model_optimize_exception_is_lp_solver_exception():
    """LpModelOptimizeException should inherit from LpSolverException."""
    exc = exception.LpModelOptimizeException("no solution")
    assert isinstance(exc, exception.LpSolverException)
    assert isinstance(exc, OrAlgoException)
    assert str(exc) == "no solution"


def test_exception_can_be_raised_and_caught():
    """Exceptions should work with normal exception handling."""
    with pytest.raises(exception.LpSolverException):
        raise exception.LpSolverException("test")

    with pytest.raises(exception.BuildLpStepException):
        raise exception.BuildLpStepException("build failed")

    with pytest.raises(exception.LpModelOptimizeException):
        raise exception.LpModelOptimizeException("no solution")
