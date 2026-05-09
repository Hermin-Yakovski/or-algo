"""Tests for or_algo.shared_register module."""

import pytest
from multiprocessing import Manager
from or_algo.shared_register import SharedRegister
from register import Register, Parameter


def test_shared_register_initialization():
    """Test that SharedRegister can be initialized."""
    reg = SharedRegister[Parameter]()
    assert reg._data is not None


def test_shared_register_with_manager():
    """Test that SharedRegister can be created with a Manager."""
    manager = Manager()
    reg = SharedRegister[Parameter].create(manager)
    assert reg._data is not None
    # Verify it's actually a Manager.dict
    assert hasattr(reg._data, '__getstate__')  # Manager.dict has this


def test_shared_register_get_set():
    """Test that SharedRegister supports getting and setting values."""
    reg = SharedRegister[Parameter]()
    reg._data["key1"] = "value1"
    reg._data["key2"] = 42
    assert reg._data["key1"] == "value1"
    assert reg._data["key2"] == 42


def test_shared_register_with_manager_get_set():
    """Test that SharedRegister with Manager supports getting and setting values."""
    manager = Manager()
    reg = SharedRegister[Parameter].create(manager)
    reg._data["key1"] = "value1"
    reg._data["key2"] = 42
    assert reg._data["key1"] == "value1"
    assert reg._data["key2"] == 42
