"""Shared fixtures for or-algo tests."""

import pytest
from register import Register, Parameter, Id, Code, Name, Index


@pytest.fixture
def empty_register() -> Register[Parameter]:
    """Provide an empty Register for testing."""
    return Register[Parameter]()


@pytest.fixture
def sample_register() -> Register[Parameter]:
    """Provide a Register with sample data for testing."""
    reg = Register[Parameter]()
    # Add sample data as needed
    reg[Id][(Index,)][(0,)] = 1
    reg[Code][(Index,)][(0,)] = "test_code"
    reg[Name][(Index,)][(0,)] = "test_name"
    return reg