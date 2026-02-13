from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import cast

from wirio._service_lookup._typed_type import TypedType
from wirio.abstractions.keyed_service import KeyedService
from wirio.abstractions.keyed_service_provider import (
    KeyedServiceProvider,
)
from wirio.abstractions.service_scope_factory import (
    ServiceScopeFactory,
)
from wirio.exceptions import (
    KeyedServiceAnyKeyUsedToResolveServiceError,
    NoKeyedServiceRegisteredError,
    NoServiceRegisteredError,
)


class BaseServiceProvider(KeyedServiceProvider, ServiceScopeFactory, ABC):
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
    ) -> TService | None:
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
    ) -> TService:
        """Get service of type `TService` or raise an error."""
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

    async def get_services[TService](
        self, service_type: type[TService]
    ) -> Sequence[TService]:
        """Get all services of type `TService`."""
        return await self.get_required_service(Sequence[service_type])  # ty: ignore[invalid-type-form]

    async def get_keyed_services[TService](
        self, service_key: object | None, service_type: type[TService]
    ) -> Sequence[TService]:
        """Get all services of type `TService`."""
        return await self.get_required_keyed_service(
            service_key,
            Sequence[service_type],  # ty: ignore[invalid-type-form]
        )
