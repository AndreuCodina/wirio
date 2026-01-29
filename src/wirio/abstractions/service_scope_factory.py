from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wirio.abstractions.service_scope import ServiceScope


class ServiceScopeFactory(ABC):
    """Create instances of :class:`ServiceScope`, which is used to create services within a scope."""

    @abstractmethod
    def create_scope(self) -> "ServiceScope":
        """Create a :class:`ServiceScope` that contains a :class:`ServiceContainer` used to resolve dependencies from a newly created scope."""
        ...
