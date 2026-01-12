import inspect
import typing
from collections.abc import Awaitable, Callable
from typing import Final, overload

from fastapi import FastAPI

from aspy_dependency_injection._integrations._fastapi_dependency_injection import (
    FastApiDependencyInjection,
)
from aspy_dependency_injection.service_descriptor import ServiceDescriptor
from aspy_dependency_injection.service_lifetime import ServiceLifetime
from aspy_dependency_injection.service_provider import (
    ServiceProvider,
)


class ServiceCollection:
    """Collection of service descriptors provided during configuration."""

    _descriptors: Final[list[ServiceDescriptor]]

    def __init__(self) -> None:
        self._descriptors = []

    @property
    def descriptors(self) -> list[ServiceDescriptor]:
        return self._descriptors

    @overload
    def add_transient[TService](self, service_type: type[TService], /) -> None: ...

    @overload
    def add_transient[TService](
        self,
        service_type: type[TService],
        implementation_factory: Callable[..., Awaitable[TService]],
        /,
    ) -> None: ...

    @overload
    def add_transient[TService](
        self,
        service_type: type[TService],
        implementation_factory: Callable[..., TService],
        /,
    ) -> None: ...

    @overload
    def add_transient[TService](
        self,
        implementation_factory: Callable[..., Awaitable[TService]],
        /,
    ) -> None: ...

    @overload
    def add_transient[TService](
        self,
        implementation_factory: Callable[..., TService],
        /,
    ) -> None: ...

    @overload
    def add_transient[TService](
        self,
        service_type: type[TService],
        implementation_type: type,
        /,
    ) -> None: ...

    def add_transient[TService](
        self,
        service_type_or_implementation_factory: type[TService]
        | Callable[..., Awaitable[TService]]
        | Callable[..., TService],
        implementation_factory_or_implementation_type_or_none: Callable[
            ..., Awaitable[TService]
        ]
        | Callable[..., TService]
        | type
        | None = None,
        /,
    ) -> None:
        self._add_from_overloaded_constructor(
            lifetime=ServiceLifetime.TRANSIENT,
            service_type_or_implementation_factory=service_type_or_implementation_factory,
            implementation_factory_or_implementation_type_or_implementation_instance_none=implementation_factory_or_implementation_type_or_none,
        )

    @overload
    def add_singleton[TService](self, service_type: type[TService], /) -> None: ...

    @overload
    def add_singleton[TService](
        self,
        service_type: type[TService],
        implementation_factory: Callable[..., Awaitable[TService]],
        /,
    ) -> None: ...

    @overload
    def add_singleton[TService](
        self,
        service_type: type[TService],
        implementation_factory: Callable[..., TService],
        /,
    ) -> None: ...

    @overload
    def add_singleton[TService](
        self,
        implementation_factory: Callable[..., Awaitable[TService]],
        /,
    ) -> None: ...

    @overload
    def add_singleton[TService](
        self,
        implementation_factory: Callable[..., TService],
        /,
    ) -> None: ...

    @overload
    def add_singleton[TService](
        self,
        service_type: type[TService],
        implementation_type: type,
        /,
    ) -> None: ...

    @overload
    def add_singleton[TService](
        self,
        service_type: type[TService],
        implementation_instance: object,
        /,
    ) -> None: ...

    def add_singleton[TService](
        self,
        service_type_or_implementation_factory: type[TService]
        | Callable[..., Awaitable[TService]]
        | Callable[..., TService],
        implementation_factory_or_implementation_type_or_implementation_instance_none: Callable[
            ..., Awaitable[TService]
        ]
        | Callable[..., TService]
        | type
        | object
        | None = None,
        /,
    ) -> None:
        self._add_from_overloaded_constructor(
            lifetime=ServiceLifetime.SINGLETON,
            service_type_or_implementation_factory=service_type_or_implementation_factory,
            implementation_factory_or_implementation_type_or_implementation_instance_none=implementation_factory_or_implementation_type_or_implementation_instance_none,
        )

    @overload
    def add_scoped[TService](self, service_type: type[TService], /) -> None: ...

    @overload
    def add_scoped[TService](
        self,
        service_type: type[TService],
        implementation_factory: Callable[..., Awaitable[TService]],
        /,
    ) -> None: ...

    @overload
    def add_scoped[TService](
        self,
        service_type: type[TService],
        implementation_factory: Callable[..., TService],
        /,
    ) -> None: ...

    @overload
    def add_scoped[TService](
        self,
        implementation_factory: Callable[..., Awaitable[TService]],
        /,
    ) -> None: ...

    @overload
    def add_scoped[TService](
        self,
        implementation_factory: Callable[..., TService],
        /,
    ) -> None: ...

    @overload
    def add_scoped[TService](
        self,
        service_type: type[TService],
        implementation_type: type,
        /,
    ) -> None: ...

    def add_scoped[TService](
        self,
        service_type_or_implementation_factory: type[TService]
        | Callable[..., Awaitable[TService]]
        | Callable[..., TService],
        implementation_factory_or_implementation_type_or_none: Callable[
            ..., Awaitable[TService]
        ]
        | Callable[..., TService]
        | type
        | None = None,
        /,
    ) -> None:
        self._add_from_overloaded_constructor(
            lifetime=ServiceLifetime.SCOPED,
            service_type_or_implementation_factory=service_type_or_implementation_factory,
            implementation_factory_or_implementation_type_or_implementation_instance_none=implementation_factory_or_implementation_type_or_none,
        )

    def build_service_provider(self) -> ServiceProvider:
        """Create a :class:`ServiceProvider` containing services from the provided :class:`ServiceCollection`."""
        return ServiceProvider(self)

    def configure_fastapi(self, app: FastAPI) -> None:
        """Configure the FastAPI application to use dependency injection using the services from this service collection."""
        FastApiDependencyInjection.setup(app, self)

    def _add_from_overloaded_constructor[TService](
        self,
        lifetime: ServiceLifetime,
        service_type_or_implementation_factory: type[TService]
        | Callable[..., Awaitable[TService]]
        | Callable[..., TService],
        implementation_factory_or_implementation_type_or_implementation_instance_none: Callable[
            ..., Awaitable[TService]
        ]
        | Callable[..., TService]
        | type
        | object
        | None = None,
    ) -> None:
        service_type_to_add: type[TService] | None = None
        implementation_factory_to_add: (
            Callable[..., Awaitable[TService]] | Callable[..., TService] | None
        ) = None
        implementation_type_to_add: type | None = None
        implementation_instance_to_add: object | None = None

        if isinstance(service_type_or_implementation_factory, type):
            service_type_to_add = service_type_or_implementation_factory

        if isinstance(
            implementation_factory_or_implementation_type_or_implementation_instance_none,
            type,
        ):
            implementation_type_to_add = implementation_factory_or_implementation_type_or_implementation_instance_none
        elif (
            service_type_to_add is not None
            and implementation_factory_or_implementation_type_or_implementation_instance_none
            is not None
        ):
            if callable(
                implementation_factory_or_implementation_type_or_implementation_instance_none,
            ):
                implementation_factory_to_add = implementation_factory_or_implementation_type_or_implementation_instance_none  # pyright: ignore[reportAssignmentType]
            else:
                implementation_instance_to_add = implementation_factory_or_implementation_type_or_implementation_instance_none
        elif (
            service_type_to_add is None
            and implementation_factory_or_implementation_type_or_implementation_instance_none
            is None
        ):
            implementation_factory_to_add = service_type_or_implementation_factory

        self._add(
            lifetime=lifetime,
            service_type=service_type_to_add,
            implementation_factory=implementation_factory_to_add,
            implementation_type=implementation_type_to_add,
            implementation_instance=implementation_instance_to_add,
        )

    def _add[TService](
        self,
        lifetime: ServiceLifetime,
        service_type: type[TService] | None,
        implementation_factory: Callable[..., Awaitable[TService]]
        | Callable[..., TService]
        | None,
        implementation_type: type | None,
        implementation_instance: object | None,
    ) -> None:
        provided_service_type = self._get_provided_service_type(
            service_type, implementation_factory
        )

        if implementation_instance is not None:
            self._add_from_implementation_instance(
                service_type=provided_service_type,
                implementation_instance=implementation_instance,
                lifetime=lifetime,
            )
        elif implementation_factory is None:
            implementation_type_to_add = (
                implementation_type
                if implementation_type is not None
                else provided_service_type
            )
            self._add_from_implementation_type(
                service_type=provided_service_type,
                implementation_type=implementation_type_to_add,
                lifetime=lifetime,
            )
        elif inspect.iscoroutinefunction(implementation_factory):
            self._add_from_async_implementation_factory(
                service_type=provided_service_type,
                implementation_factory=implementation_factory,
                lifetime=lifetime,
            )
        else:
            self._add_from_sync_implementation_factory(
                service_type=provided_service_type,
                implementation_factory=implementation_factory,
                lifetime=lifetime,
            )

    def _get_provided_service_type[TService](
        self,
        service_type: type[TService] | None = None,
        implementation_factory: Callable[..., Awaitable[TService]]
        | Callable[..., TService]
        | None = None,
    ) -> type:
        if service_type is not None:
            return service_type

        assert implementation_factory is not None

        type_hints: dict[str, type] = typing.get_type_hints(implementation_factory)
        return_type = type_hints.get("return")

        if return_type is None:
            error_message = "Missing return type hints from 'implementation_factory'"
            raise ValueError(error_message)

        return return_type

    def _add_from_implementation_type(
        self, service_type: type, implementation_type: type, lifetime: ServiceLifetime
    ) -> None:
        descriptor = ServiceDescriptor.from_implementation_type(
            service_type=service_type,
            implementation_type=implementation_type,
            lifetime=lifetime,
        )
        self._descriptors.append(descriptor)

    def _add_from_implementation_instance(
        self,
        service_type: type,
        implementation_instance: object,
        lifetime: ServiceLifetime,
    ) -> None:
        descriptor = ServiceDescriptor.from_implementation_instance(
            service_type=service_type,
            implementation_instance=implementation_instance,
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
