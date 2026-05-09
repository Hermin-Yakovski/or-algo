"""SharedRegister class for multiprocessing-safe data storage."""

from typing import TypeVar
from register import Register
from multiprocessing import Manager

T = TypeVar('T')


class SharedRegister(Register[T]):
    """Multiprocessing-compatible Register using Manager backend."""

    def __init__(self) -> None:
        """Initialize a SharedRegister with a Manager.dict() backing store."""
        super().__init__()
        self._manager = Manager()
        self._data = self._manager.dict()

    def shutdown(self) -> None:
        """Cleanup manager resources."""
        self._manager.shutdown()
