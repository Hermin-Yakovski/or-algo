"""Tests for or_algo package imports."""

from or_algo import Solver, Algorithm, OrAlgoException


def test_solver_is_exported():
    """Test that Solver is exported from package."""
    assert Solver is not None
    assert Solver.__name__ == "Solver"


def test_algorithm_is_exported():
    """Test that Algorithm is exported from package."""
    assert Algorithm is not None
    assert Algorithm.__name__ == "Algorithm"


def test_or_algo_exception_is_exported():
    """Test that OrAlgoException is exported from package."""
    assert OrAlgoException is not None
    assert OrAlgoException.__name__ == "OrAlgoException"


def test_version_is_defined():
    """Test that package version is defined."""
    from or_algo import __version__
    assert __version__ == "0.3.0"