"""Symbol hierarchy for LP model elements."""

from typing import Type, Any


class Symbol:
    """Base class for LP model elements."""

    _name: str
    _name_cn: str
    _sign: str
    vtype: Type[Any]

    def __init__(self, name: str, name_cn: str, sign: str):
        self._name = name
        self._name_cn = name_cn
        self._sign = sign
        self.vtype = type(None)  # Placeholder, set by subclasses

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
