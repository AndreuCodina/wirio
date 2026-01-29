from abc import ABC, abstractmethod

from wirio._service_lookup._typed_type import (
    TypedType,
)


class KeyedServiceContainer(ABC):
    """Retrieve services using a key and a type."""

    @abstractmethod
    async def get_keyed_object(
        self, service_key: object | None, service_type: TypedType
    ) -> object | None: ...

    @abstractmethod
    async def try_get_keyed[TService](
        self, service_key: object | None, service_type: type[TService]
    ) -> TService | None:
        """Get service of type `TService` or return `None`."""
        ...

    @abstractmethod
    async def get_keyed[TService](
        self, service_key: object | None, service_type: type[TService]
    ) -> TService:
        """Get service of type `TService` or raise an error."""
        ...
