"""LpStep hierarchy for LP model building."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from or_register import Register, RegisterKey

from . import exception

if TYPE_CHECKING:
    from or_register import Dimension, Selected
    from ortools.linear_solver import pywraplp

    from .symbol import ConstrKey, VarKey


class LpStep(ABC):
    """Abstract base class for LP model building steps."""

    def __init__(self, symbol: RegisterKey):
        super().__init__()
        self._symbol = symbol

    @abstractmethod
    def run(
        self,
        data: Register[RegisterKey],
        model: pywraplp.Solver,
        var: Register[VarKey],
    ) -> None:
        """Execute this step to build the LP model."""


class CreateVar(LpStep, ABC):
    """Base class for variable creation steps."""

    _symbol: VarKey

    def __init__(self, symbol: VarKey):
        super().__init__(symbol)

    def _create(
        self,
        selected: Selected,
        model: pywraplp.Solver,
        var: Register[VarKey],
        dimension: tuple[Dimension, ...],
    ) -> None:
        dim_signs = ",".join(d.sign for d in dimension)
        for index in selected:
            idx_str = ",".join(str(i) for i in index)
            name = f"{self._symbol.sign}({dim_signs},)({idx_str},)"
            if self.vtype == "BINARY":
                v = model.IntVar(0, 1, name)
            elif self.vtype == "INTEGER":
                v = model.IntVar(0, model.infinity(), name)
            else:  # CONTINUOUS
                v = model.NumVar(0, model.infinity(), name)
            var[self._symbol][dimension][index] = v

    @property
    def vtype(self) -> str:
        """Map NumKey vtype to OR-Tools variable type."""
        vtype_mapping = {
            int: "INTEGER",
            float: "CONTINUOUS",
            bool: "BINARY",
        }
        vtype = self._symbol.vtype
        if vtype not in vtype_mapping:
            raise ValueError(
                f"Unsupported NumKey vtype: {vtype}. Supported types: {list(vtype_mapping.keys())}"
            )
        return vtype_mapping[vtype]

    @abstractmethod
    def run(
        self,
        data: Register[RegisterKey],
        model: pywraplp.Solver,
        var: Register[VarKey],
    ) -> None:
        """Create variables in the model."""


class CreateConstr(LpStep, ABC):
    """Base class for constraint creation steps."""

    def __init__(self, symbol: ConstrKey):
        super().__init__(symbol)

    @abstractmethod
    def run(
        self,
        data: Register[RegisterKey],
        model: pywraplp.Solver,
        var: Register[VarKey],
    ) -> None:
        """Create constraints in the model."""


class Publish(LpStep):
    _symbol: VarKey
    _zeros: bool
    _dimension: tuple[Dimension, ...]
    _threshold: float
    _target: tuple[slice, ...] | None

    def __init__(
        self,
        symbol: VarKey,
        dimension: tuple[Dimension, ...],
        target: tuple[slice, ...] | None = None,
        zeros: bool = False,
        threshold: float = 1e-6,
    ):
        super().__init__(symbol)
        self._dimension = dimension
        self._zeros = zeros
        self._threshold = threshold
        self._target = target

    def run(
        self, data: Register[RegisterKey], model: pywraplp.Solver, register: Register[VarKey]
    ) -> None:
        space = register[self._symbol][self._dimension]
        sel = space.all if self._target is None else space[self._target]
        for index in sel:
            quantity = register[self._symbol][self._dimension][index].solution_value()
            if self._symbol.vtype is int:
                quantity = int(round(quantity, 0))
            elif self._symbol.vtype is bool:
                quantity = bool(round(quantity, 0))
            elif self._symbol.vtype is float:
                pass
            else:
                raise exception.BuildLpStepException(
                    f"Unsupported vtype {self._symbol.vtype} while publishing variable {self._symbol.name}"
                )

            if self._zeros or (quantity > self._threshold):
                data[self._symbol.parameter][self._dimension][index] = quantity
