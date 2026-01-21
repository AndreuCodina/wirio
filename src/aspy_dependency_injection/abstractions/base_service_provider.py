from abc import ABC, abstractmethod
from typing import cast

from aspy_dependency_injection._service_lookup._typed_type import TypedType
from aspy_dependency_injection.abstractions.keyed_service import KeyedService
from aspy_dependency_injection.abstractions.keyed_service_provider import (
    KeyedServiceProvider,
)
from aspy_dependency_injection.exceptions import (
    KeyedServiceAnyKeyUsedToResolveServiceError,
    NoKeyedServiceRegisteredError,
    NoServiceRegisteredError,
)


class BaseServiceProvider(KeyedServiceProvider, ABC):
    """Define a mechanism for retrieving a service object; that is, an object that provides custom support to other objects."""

    @abstractmethod
    async def get_service_object(self, service_type: TypedType) -> object | None: ...

    @abstractmethod
    async def get_keyed_service_object(
        self, service_key: object | None, service_type: TypedType
    ) -> object | None: ...

    async def get_service[TService](
        self, service_type: type[TService]
    ) -> TService | None:
        """Get service of type `TService` or return `None`."""
        service = await self.get_service_object(TypedType.from_type(service_type))

        if service is None:
            return None

        return cast("TService", service)

    async def get_required_service[TService](
        self, service_type: type[TService]
    ) -> TService:
        """Get service of type `TService` or raise :class:`NoServiceRegisteredError`."""
        service = await self.get_service(service_type)

        if service is None:
            raise NoServiceRegisteredError(TypedType.from_type(service_type))

        return service

    async def get_keyed_service[TService](
        self, service_key: object | None, service_type: type[TService]
    ) -> object | None:
        """Get service of type `TService` or return `None`."""
        if service_key is KeyedService.ANY_KEY:
            raise KeyedServiceAnyKeyUsedToResolveServiceError

        service = await self.get_keyed_service_object(
            service_key, TypedType.from_type(service_type)
        )

        if service is None:
            return None

        return cast("TService", service)

    async def get_required_keyed_service[TService](
        self, service_key: object | None, service_type: type[TService]
    ) -> object:
        """Get service of type `TService` or raise ``."""
        if service_key is KeyedService.ANY_KEY:
            raise KeyedServiceAnyKeyUsedToResolveServiceError

        service = await self.get_keyed_service(service_key, service_type)

        if service is None:
            if service_key is None:
                raise NoServiceRegisteredError(TypedType.from_type(service_type))

            raise NoKeyedServiceRegisteredError(
                service_type=TypedType.from_type(service_type),
                service_key_type=type(service_key),
            )

        return service
