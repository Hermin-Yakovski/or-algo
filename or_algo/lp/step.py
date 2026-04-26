"""LpStep hierarchy for LP model building."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from register import Register
    from register import Parameter
    from or_algo.lp.symbol import Symbol
    from ortools.linear_solver import pywraplp


class LpStep(ABC):
    """Abstract base class for LP model building steps."""

    def __init__(self, symbol: "Symbol"):
        super().__init__()
        self._symbol = symbol

    @abstractmethod
    def run(
        self,
        data: "Register[Parameter]",
        model: "pywraplp.Solver",
        var: "Register[Symbol]"
    ) -> None:
        """Execute this step to build the LP model.

        Args:
            data: Register containing input parameters
            model: OR-Tools solver instance
            var: Register for storing variables/constraints
        """
        pass
