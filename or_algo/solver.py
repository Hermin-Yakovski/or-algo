"""Solver abstract base class for or-algo package."""

from abc import ABC, abstractmethod
from register import Register, Parameter


class Solver(ABC):
    """Abstract base class for solvers that operate on a Register.

    Users extend this class to implement their solving logic.
    Each solver reads from and writes to a shared Register[Parameter].
    """

    def __init__(self, name: str | None = None) -> None:
        """Initialize the solver with an optional name.

        Args:
            name: Optional name for the solver. Defaults to the class name.
        """
        self._name = type(self).__name__ if name is None else name

    @property
    def name(self) -> str:
        """Get the solver's name."""
        return self._name

    @abstractmethod
    def solve(self, data: Register[Parameter]) -> None:
        """Solve the problem using data from the Register.

        Args:
            data: Register containing input parameters; solutions
                  are written back to this same Register.
        """
        pass