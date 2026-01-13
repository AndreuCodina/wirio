from abc import ABC, abstractmethod
from typing import cast

from aspy_dependency_injection._service_lookup._typed_type import TypedType


class BaseServiceProvider(ABC):
    """Define a mechanism for retrieving a service object; that is, an object that provides custom support to other objects."""

    @abstractmethod
    async def get_service_object(self, service_type: TypedType) -> object | None: ...

    async def get_service[TService](
        self, service_type: type[TService]
    ) -> TService | None:
        """Get service of type `TService`."""
        service = await self.get_service_object(TypedType.from_type(service_type))

        if service is None:
            return None

        return cast("TService", service)

    async def get_required_service[TService](
        self, service_type: type[TService]
    ) -> TService:
        """Get service of type `TService`."""
        service = await self.get_service_object(TypedType.from_type(service_type))
        assert service is not None
        return cast("TService", service)
