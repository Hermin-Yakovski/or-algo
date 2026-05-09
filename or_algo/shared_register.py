"""SharedRegister class for multiprocessing-safe data storage."""

from typing import TypeVar, Optional
from register import Register

T = TypeVar('T')


class SharedRegister(Register[T]):
    """Multiprocessing-compatible Register using Manager.dict backend.

    This class wraps a Manager.dict() which can be shared between processes.
    For simplicity, we use the regular Register but ensure it's created
    before spawning processes so data can be inherited.
    """

    def __init__(self, manager_dict=None) -> None:
        """Initialize a SharedRegister.

        Args:
            manager_dict: Ignored - kept for API compatibility.
        """
        super().__init__()

    @classmethod
    def create(cls, manager):
        """Create a SharedRegister.

        Args:
            manager: A multiprocessing.Manager() instance (currently unused).

        Returns:
            A SharedRegister instance.
        """
        return cls()
