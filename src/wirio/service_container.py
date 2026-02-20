import typing
from collections.abc import Awaitable, Callable, Generator, Sequence
from contextlib import AbstractAsyncContextManager, contextmanager
from types import TracebackType
from typing import TYPE_CHECKING, Self, final

from wirio.abstractions.service_scope import ServiceScope
from wirio.exceptions import ServiceContainerNotBuiltError
from wirio.service_collection import ServiceCollection
from wirio.service_lifetime import ServiceLifetime
from wirio.service_provider import ServiceProvider

if TYPE_CHECKING:
    from fastapi import FastAPI
else:
    FastAPI = None


@final
class ServiceContainer(
    ServiceCollection, AbstractAsyncContextManager["ServiceContainer"]
):
    """Collection of resolvable services."""

    _service_provider: ServiceProvider | None

    def __init__(self) -> None:
        super().__init__()
        self._service_provider = None

    @typing.override
    def build_service_provider(
        self, validate_scopes: bool = False, validate_on_build: bool = True
    ) -> ServiceProvider:
        """Create a :class:`ServiceProvider` containing services from the this :class:`ServiceContainer`."""
        if self._service_provider is not None:
            return self._service_provider

        return super().build_service_provider(validate_scopes, validate_on_build)

    @property
    def service_provider(self) -> ServiceProvider | None:
        return self._service_provider

    async def get[TService](self, service_type: type[TService]) -> TService:
        """Get service of type `TService` or raise :class:`NoServiceRegisteredError`."""
        service_provider = await self._get_service_provider()
        return await service_provider.get_required_service(service_type)

    async def try_get[TService](self, service_type: type[TService]) -> TService | None:
        """Get service of type `TService` or return `None`."""
        service_provider = await self._get_service_provider()
        return await service_provider.get_service(service_type)

    async def get_keyed[TService](
        self, service_key: object | None, service_type: type[TService]
    ) -> TService:
        """Get service of type `TService` or raise an error."""
        service_provider = await self._get_service_provider()
        return await service_provider.get_required_keyed_service(
            service_key=service_key, service_type=service_type
        )

    async def try_get_keyed[TService](
        self, service_key: object | None, service_type: type[TService]
    ) -> TService | None:
        """Get service of type `TService` or return `None`."""
        service_provider = await self._get_service_provider()
        return await service_provider.get_keyed_service(
            service_key=service_key, service_type=service_type
        )

    async def get_all[TService](
        self, service_type: type[TService]
    ) -> Sequence[TService]:
        """Get all services of type `TService`."""
        service_provider = await self._get_service_provider()
        return await service_provider.get_services(service_type)

    async def get_all_keyed[TService](
        self, service_key: object | None, service_type: type[TService]
    ) -> Sequence[TService]:
        """Get all services of type `TService`."""
        service_provider = await self._get_service_provider()
        return await service_provider.get_keyed_services(
            service_key=service_key, service_type=service_type
        )

    def create_scope(self) -> ServiceScope:
        """Create a new :class:`ServiceScope` that can be used to resolve scoped services."""
        if self._service_provider is None:
            self._service_provider = self.build_service_provider()

        return self._service_provider.create_scope()

    async def aclose(self) -> None:
        if self._service_provider is not None:
            await self._service_provider.__aexit__(None, None, None)

        self._service_provider = None

    @contextmanager
    def override(
        self, service_type: type, implementation_instance: object | None
    ) -> Generator[None]:
        """Override a service registration within the context manager scope.

        It can be used to temporarily replace a service for testing specific scenarios. Don't use it in production.
        """
        self._ensure_service_container_is_built()
        assert self._service_provider is not None

        with self._service_provider.override_service(
            service_type=service_type,
            implementation_instance=implementation_instance,
        ):
            yield

    @contextmanager
    def override_keyed(
        self,
        service_key: object | None,
        service_type: type,
        implementation_instance: object | None,
    ) -> Generator[None]:
        """Override a keyed service registration within the context manager scope.

        It can be used to temporarily replace a service for testing specific scenarios. Don't use it in production.
        """
        self._ensure_service_container_is_built()
        assert self._service_provider is not None

        with self._service_provider.override_keyed_service(
            service_key=service_key,
            service_type=service_type,
            implementation_instance=implementation_instance,
        ):
            yield

    @typing.override
    def configure_fastapi(self, app: FastAPI) -> None:
        """Configure the FastAPI application to use dependency injection using the services from this service container."""
        super().configure_fastapi(app)

    @typing.override
    def _add[TService](
        self,
        lifetime: ServiceLifetime,
        service_type: type[TService] | None,
        implementation_factory: Callable[..., Awaitable[TService]]
        | Callable[..., TService]
        | None,
        implementation_type: type | None,
        implementation_instance: object | None,
        service_key: object | None,
        auto_activate: bool,
    ) -> None:
        super()._add(
            lifetime=lifetime,
            service_type=service_type,
            implementation_factory=implementation_factory,
            implementation_type=implementation_type,
            implementation_instance=implementation_instance,
            service_key=service_key,
            auto_activate=auto_activate,
        )

        if self._service_provider is not None:
            added_descriptor = self._descriptors[-1]
            self._service_provider.add_descriptor(added_descriptor)

    async def _get_service_provider(self) -> ServiceProvider:
        if self._service_provider is None:
            self._service_provider = self.build_service_provider()
            await self._service_provider.__aenter__()

        return self._service_provider

    def _ensure_service_container_is_built(self) -> None:
        if self._service_provider is None:
            raise ServiceContainerNotBuiltError

    @typing.override
    async def __aenter__(self) -> Self:
        service_provider = await self._get_service_provider()
        await service_provider.fully_initialize_if_not_fully_initialized()
        return self

    @typing.override
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        assert self._service_provider is not None
        await self._service_provider.__aexit__(exc_type, exc_val, exc_tb)
        self._service_provider = None
