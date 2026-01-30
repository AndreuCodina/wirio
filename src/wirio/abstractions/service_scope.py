from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager

from wirio.base_service_provider import (
    BaseServiceProvider,
)


class ServiceScope(AbstractAsyncContextManager["ServiceScope"], ABC):
    """Defines a disposable service scope.

    The __aexit__ method ends the scope lifetime. Once called, any scoped
    services that have been resolved from ServiceProvider will be disposed.
    """

    @property
    @abstractmethod
    def service_provider(self) -> BaseServiceProvider:
        """Gets the :class:`BaseServiceProvider` used to resolve dependencies from the scope."""

    @abstractmethod
    async def get_service[TService](
        self, service_type: type[TService]
    ) -> TService | None:
        """Get service of type `TService` or return `None`."""
        ...

    @abstractmethod
    async def get_required_service[TService](
        self, service_type: type[TService]
    ) -> TService:
        """Get service of type `TService` or raise :class:`NoServiceRegisteredError`."""
        ...

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
