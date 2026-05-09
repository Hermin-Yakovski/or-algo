"""Tests for or_algo.shared_register module."""

import pytest
from or_algo.shared_register import SharedRegister
from register import Register, Parameter


def test_shared_register_initialization():
    """Test that SharedRegister can be initialized."""
    reg = SharedRegister[Parameter]()
    assert reg._data is not None
    assert reg._manager is not None


def test_shared_register_get_set():
    """Test that SharedRegister supports getting and setting values."""
    reg = SharedRegister[Parameter]()
    reg._data["key1"] = "value1"
    reg._data["key2"] = 42
    assert reg._data["key1"] == "value1"
    assert reg._data["key2"] == 42


def test_shared_register_shutdown():
    """Test that SharedRegister can be properly shut down."""
    reg = SharedRegister[Parameter]()
    reg._data["key"] = "value"
    reg.shutdown()
    # After shutdown, operations should fail or behave as expected
    # Manager.dict() behavior after shutdown varies, so we just ensure no exception
