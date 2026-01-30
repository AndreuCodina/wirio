from abc import ABC, abstractmethod

from wirio._service_lookup._typed_type import (
    TypedType,
)


class KeyedServiceProvider(ABC):
    """Retrieve services using a key and a type."""

    @abstractmethod
    async def get_keyed_service_object(
        self, service_key: object | None, service_type: TypedType
    ) -> object | None: ...

    @abstractmethod
    async def get_keyed_service[TService](
        self, service_key: object | None, service_type: type[TService]
    ) -> TService | None:
        """Get service of type `TService` or return `None`."""
        ...

    @abstractmethod
    async def get_required_keyed_service[TService](
        self, service_key: object | None, service_type: type[TService]
    ) -> TService:
        """Get service of type `TService` or raise an error."""
        ...
