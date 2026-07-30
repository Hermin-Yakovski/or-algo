"""Solver abstract base class for or-algo package."""

from abc import ABC, abstractmethod

from or_register import Register, RegisterKey


class Solver(ABC):
    def __init__(self, name: str | None = None) -> None:
        self._name = type(self).__name__ if name is None else name

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    def solve(self, data: Register[RegisterKey]) -> Register[RegisterKey]:
        pass
