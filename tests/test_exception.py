"""Tests for or_algo.exception module."""

from or_algo.exception import OrAlgoException


def test_or_algo_exception_creation():
    """Test that OrAlgoException can be created with a message."""
    exc = OrAlgoException("test error")
    assert str(exc) == "test error"
    assert isinstance(exc, Exception)


def test_or_algo_exception_as_base_class():
    """Test that OrAlgoException can be used as a base class."""
    class CustomError(OrAlgoException):
        pass

    exc = CustomError("custom message")
    assert isinstance(exc, OrAlgoException)
    assert isinstance(exc, Exception)
    assert str(exc) == "custom message"


def test_or_algo_exception_without_message():
    """Test that OrAlgoException can be created without a message."""
    exc = OrAlgoException()
    assert isinstance(exc, Exception)
    assert isinstance(exc, OrAlgoException)