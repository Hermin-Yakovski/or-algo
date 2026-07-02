"""Shared fixtures for or-algo tests."""

import os
import sys

# Add ortools DLL directory to PATH for subprocess compatibility (Windows only)
if sys.platform == "win32":
    try:
        import site
        site_packages = site.getsitepackages()
        for pkg_path in site_packages:
            ortools_dll_path = os.path.join(pkg_path, "ortools", ".libs")
            if os.path.exists(ortools_dll_path):
                # Add to PATH for subprocess
                os.environ["PATH"] = ortools_dll_path + os.pathsep + os.environ.get("PATH", "")
                # Also add to DLL directory for current process
                os.add_dll_directory(ortools_dll_path)
                break
    except Exception:
        # Silently fail if this doesn't work
        pass


import pytest
from register import Register, RegisterKey, Id, Code, Name, Index


@pytest.fixture
def empty_register() -> Register[RegisterKey]:
    """Provide an empty Register for testing."""
    return Register()


@pytest.fixture
def sample_register() -> Register[RegisterKey]:
    """Provide a Register with sample data for testing."""
    reg = Register()
    # Add sample data as needed
    reg[Id][(Index,)][(0,)] = 1
    reg[Code][(Index,)][(0,)] = "test_code"
    reg[Name][(Index,)][(0,)] = "test_name"
    return reg