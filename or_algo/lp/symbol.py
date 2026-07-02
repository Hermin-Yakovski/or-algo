"""Symbol hierarchy for LP model elements."""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from ortools.linear_solver import pywraplp

if TYPE_CHECKING:
    from register import RegisterKey


class Symbol:
    """Base class for LP model elements."""

    _name: str
    _name_cn: str
    _sign: str
    vtype: Any

    def __init__(self, name: str, name_cn: str, sign: str):
        self._name = name
        self._name_cn = name_cn
        self._sign = sign
        self.vtype = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def name_cn(self) -> str:
        return self._name_cn

    @property
    def sign(self) -> str:
        return self._sign

    def __str__(self) -> str:
        return self._sign

    def __repr__(self) -> str:
        return self._name


class Var(Symbol):
    """Decision variable wrapper around OR-Tools Variable."""

    _parameter: RegisterKey

    def __init__(self, p: Any, sign: str):
        super().__init__(name=p.name, name_cn=p.name_cn, sign=sign)
        self._parameter = p
        self.vtype = pywraplp.Variable

    @property
    def id(self) -> int:
        return self._parameter.id

    @property
    def parameter(self) -> Any:
        return self._parameter


class Constr(Symbol):
    """Constraint wrapper around OR-Tools Constraint."""

    def __init__(self, name: str, name_cn: str, sign: str):
        super().__init__(name, name_cn, sign)
        self.vtype = pywraplp.Constraint
