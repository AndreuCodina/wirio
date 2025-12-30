import inspect
from typing import TYPE_CHECKING, Final, overload

from aspy_dependency_injection._integrations._fastapi_dependency_injection import (
    FastApiDependencyInjection,
)
from aspy_dependency_injection.service_descriptor import ServiceDescriptor
from aspy_dependency_injection.service_lifetime import ServiceLifetime
from aspy_dependency_injection.service_provider import (
    ServiceProvider,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from fastapi import FastAPI


class ServiceCollection:
    """Collection of service descriptors provided during configuration."""

    _descriptors: Final[list[ServiceDescriptor]]

    def __init__(self) -> None:
        self._descriptors = []

    @property
    def descriptors(self) -> list[ServiceDescriptor]:
        return self._descriptors

    @overload
    def add_transient[TService](self, service_type: type[TService]) -> None: ...

    @overload
    def add_transient[TService](
        self,
        service_type: type[TService],
        implementation_factory: Callable[..., Awaitable[TService]],
    ) -> None: ...

    @overload
    def add_transient[TService](
        self,
        service_type: type[TService],
        implementation_factory: Callable[..., TService],
    ) -> None: ...

    def add_transient[TService](
        self,
        service_type: type[TService],
        implementation_factory: Callable[..., Awaitable[TService]]
        | Callable[..., TService]
        | None = None,
    ) -> None:
        if implementation_factory is None:
            self._add_from_implementation_type(
                service_type=service_type,
                implementation_type=service_type,
                lifetime=ServiceLifetime.TRANSIENT,
            )
        elif inspect.iscoroutinefunction(implementation_factory):
            self._add_from_async_implementation_factory(
                service_type=service_type,
                implementation_factory=implementation_factory,
                lifetime=ServiceLifetime.TRANSIENT,
            )
        else:
            self._add_from_sync_implementation_factory(
                service_type=service_type,
                implementation_factory=implementation_factory,
                lifetime=ServiceLifetime.TRANSIENT,
            )

    @overload
    def add_singleton[TService](self, service_type: type[TService]) -> None: ...

    @overload
    def add_singleton[TService](
        self,
        service_type: type[TService],
        implementation_factory: Callable[..., Awaitable[TService]],
    ) -> None: ...

    @overload
    def add_singleton[TService](
        self,
        service_type: type[TService],
        implementation_factory: Callable[..., TService],
    ) -> None: ...

    def add_singleton[TService](
        self,
        service_type: type[TService],
        implementation_factory: Callable[..., Awaitable[TService]]
        | Callable[..., TService]
        | None = None,
    ) -> None:
        if implementation_factory is None:
            self._add_from_implementation_type(
                service_type=service_type,
                implementation_type=service_type,
                lifetime=ServiceLifetime.SINGLETON,
            )
        elif inspect.iscoroutinefunction(implementation_factory):
            self._add_from_async_implementation_factory(
                service_type=service_type,
                implementation_factory=implementation_factory,
                lifetime=ServiceLifetime.SINGLETON,
            )
        else:
            self._add_from_sync_implementation_factory(
                service_type=service_type,
                implementation_factory=implementation_factory,
                lifetime=ServiceLifetime.SINGLETON,
            )

    @overload
    def add_scoped[TService](self, service_type: type[TService]) -> None: ...

    @overload
    def add_scoped[TService](
        self,
        service_type: type[TService],
        implementation_factory: Callable[..., Awaitable[TService]],
    ) -> None: ...

    @overload
    def add_scoped[TService](
        self,
        service_type: type[TService],
        implementation_factory: Callable[..., TService],
    ) -> None: ...

    def add_scoped[TService](
        self,
        service_type: type[TService],
        implementation_factory: Callable[..., Awaitable[TService]]
        | Callable[..., TService]
        | None = None,
    ) -> None:
        if implementation_factory is None:
            self._add_from_implementation_type(
                service_type=service_type,
                implementation_type=service_type,
                lifetime=ServiceLifetime.SCOPED,
            )
        elif inspect.iscoroutinefunction(implementation_factory):
            self._add_from_async_implementation_factory(
                service_type=service_type,
                implementation_factory=implementation_factory,
                lifetime=ServiceLifetime.SCOPED,
            )
        else:
            self._add_from_sync_implementation_factory(
                service_type=service_type,
                implementation_factory=implementation_factory,
                lifetime=ServiceLifetime.SCOPED,
            )

    def build_service_provider(self) -> ServiceProvider:
        """Create a :class:`ServiceProvider` containing services from the provided :class:`ServiceCollection`."""
        return ServiceProvider(self)

    def configure_fastapi(self, app: FastAPI) -> None:
        FastApiDependencyInjection.setup(app, self)

    def _add_from_implementation_type(
        self, service_type: type, implementation_type: type, lifetime: ServiceLifetime
    ) -> None:
        descriptor = ServiceDescriptor.from_implementation_type(
            service_type=service_type,
            implementation_type=implementation_type,
            lifetime=lifetime,
        )
        self._descriptors.append(descriptor)

    def _add_from_sync_implementation_factory(
        self,
        service_type: type,
        implementation_factory: Callable[..., object],
        lifetime: ServiceLifetime,
    ) -> None:
        descriptor = ServiceDescriptor.from_sync_implementation_factory(
            service_type=service_type,
            implementation_factory=implementation_factory,
            lifetime=lifetime,
        )
        self._descriptors.append(descriptor)

    def _add_from_async_implementation_factory(
        self,
        service_type: type,
        implementation_factory: Callable[..., Awaitable[object]],
        lifetime: ServiceLifetime,
    ) -> None:
        descriptor = ServiceDescriptor.from_async_implementation_factory(
            service_type=service_type,
            implementation_factory=implementation_factory,
            lifetime=lifetime,
        )
        self._descriptors.append(descriptor)
