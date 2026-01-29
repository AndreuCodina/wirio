import asyncio
from collections.abc import Awaitable, Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass
from types import TracebackType
from typing import TYPE_CHECKING, Final, Self, final, override

from aspy_dependency_injection._async_concurrent_dictionary import (
    AsyncConcurrentDictionary,
)
from aspy_dependency_injection._service_lookup._call_site_chain import CallSiteChain
from aspy_dependency_injection._service_lookup._call_site_factory import CallSiteFactory
from aspy_dependency_injection._service_lookup._constant_call_site import (
    ConstantCallSite,
)
from aspy_dependency_injection._service_lookup._runtime_service_provider_engine import (
    RuntimeServiceProviderEngine,
)
from aspy_dependency_injection._service_lookup._service_call_site import (
    ServiceCallSite,
)
from aspy_dependency_injection._service_lookup._service_identifier import (
    ServiceIdentifier,
)
from aspy_dependency_injection._service_lookup._service_provider_call_site import (
    ServiceProviderCallSite,
)
from aspy_dependency_injection._service_lookup._service_provider_engine import (
    ServiceProviderEngine,
)
from aspy_dependency_injection._service_lookup._typed_type import TypedType
from aspy_dependency_injection.abstractions.base_service_provider import (
    BaseServiceProvider,
)
from aspy_dependency_injection.abstractions.service_provider_is_keyed_service import (
    ServiceProviderIsKeyedService,
)
from aspy_dependency_injection.abstractions.service_provider_is_service import (
    ServiceProviderIsService,
)
from aspy_dependency_injection.abstractions.service_scope import (
    AbstractAsyncContextManager,
    ServiceScope,
)
from aspy_dependency_injection.abstractions.service_scope_factory import (
    ServiceScopeFactory,
)
from aspy_dependency_injection.exceptions import ObjectDisposedError
from aspy_dependency_injection.service_provider_engine_scope import (
    ServiceProviderEngineScope,
)

if TYPE_CHECKING:
    from aspy_dependency_injection.service_collection import ServiceCollection


@dataclass(frozen=True)
class _ServiceAccessor:
    call_site: ServiceCallSite | None
    realized_service: Callable[[ServiceProviderEngineScope], Awaitable[object | None]]


@final
class ServiceProvider(
    BaseServiceProvider, AbstractAsyncContextManager["ServiceProvider"]
):
    """Provider that resolves services."""

    _services: Final["ServiceCollection"]
    _root: Final[ServiceProviderEngineScope]
    _engine: Final[ServiceProviderEngine]
    _service_accessors: Final[
        AsyncConcurrentDictionary[ServiceIdentifier, _ServiceAccessor]
    ]
    _is_disposed: bool
    _call_site_factory: Final[CallSiteFactory]

    def __init__(self, services: "ServiceCollection") -> None:
        self._services = services
        self._root = ServiceProviderEngineScope(
            service_provider=self, is_root_scope=True
        )
        self._engine = self._get_engine()
        self._service_accessors = AsyncConcurrentDictionary()
        self._is_disposed = False
        self._call_site_factory = CallSiteFactory(services)

    @property
    def root(self) -> ServiceProviderEngineScope:
        return self._root

    @property
    def is_disposed(self) -> bool:
        return self._is_disposed

    @override
    async def get_service_object(self, service_type: TypedType) -> object | None:
        if self._is_disposed:
            raise ObjectDisposedError

        return await self.get_service_from_service_identifier(
            service_identifier=ServiceIdentifier.from_service_type(service_type),
            service_provider_engine_scope=self._root,
        )

    @override
    async def get_keyed_service_object(
        self, service_key: object | None, service_type: TypedType
    ) -> object | None:
        if self._is_disposed:
            raise ObjectDisposedError

        return await self.get_service_from_service_identifier(
            service_identifier=ServiceIdentifier.from_service_type(
                service_type=service_type, service_key=service_key
            ),
            service_provider_engine_scope=self._root,
        )

    # Check against public static IServiceScope CreateScope(this IServiceProvider provider)      ... return provider.GetRequiredService<IServiceScopeFactory>().CreateScope();
    def create_scope(self) -> ServiceScope:
        """Create a new :class:`ServiceScope` that can be used to resolve scoped services."""
        if self._is_disposed:
            raise ObjectDisposedError

        return ServiceProviderEngineScope(service_provider=self, is_root_scope=False)

    async def get_service_from_service_identifier(
        self,
        service_identifier: ServiceIdentifier,
        service_provider_engine_scope: ServiceProviderEngineScope,
    ) -> object | None:
        override_call_site = self._call_site_factory.get_overridden_call_site(
            service_identifier
        )

        if override_call_site is not None:
            realized_override = self._engine.realize_service(override_call_site)
            return await realized_override(service_provider_engine_scope)

        service_accessor = await self._service_accessors.get_or_add(
            key=service_identifier, value_factory=self._create_service_accessor
        )
        return await service_accessor.realized_service(service_provider_engine_scope)

    @contextmanager
    def override_service(
        self, service_type: type, implementation_instance: object | None
    ) -> Generator[None]:
        """Override a service registration within the context manager scope.

        It can be used to temporarily replace a service for testing specific scenarios. Don't use it in production.
        """
        service_identifier = ServiceIdentifier.from_service_type(
            TypedType.from_type(service_type)
        )

        with self._call_site_factory.override_service(
            service_identifier=service_identifier,
            implementation_instance=implementation_instance,
        ):
            yield

    @contextmanager
    def override_keyed_service(
        self,
        service_key: object | None,
        service_type: type,
        implementation_instance: object | None,
    ) -> Generator[None]:
        """Override a keyed service registration within the context manager scope.

        It can be used to temporarily replace a service for testing specific scenarios. Don't use it in production.
        """
        service_identifier = ServiceIdentifier.from_service_type(
            service_type=TypedType.from_type(service_type),
            service_key=service_key,
        )

        with self._call_site_factory.override_service(
            service_identifier=service_identifier,
            implementation_instance=implementation_instance,
        ):
            yield

    async def _create_service_accessor(
        self, service_identifier: ServiceIdentifier
    ) -> _ServiceAccessor:
        def realized_service_returning_none(
            _: ServiceProviderEngineScope,
        ) -> Awaitable[object | None]:
            future = asyncio.Future[None]()
            future.set_result(None)
            return future

        call_site = await self._call_site_factory.get_call_site(
            service_identifier, CallSiteChain()
        )

        if call_site is not None:
            realized_service = self._engine.realize_service(call_site)
            return _ServiceAccessor(
                call_site=call_site, realized_service=realized_service
            )

        return _ServiceAccessor(
            call_site=call_site, realized_service=realized_service_returning_none
        )

    def _get_engine(self) -> ServiceProviderEngine:
        return RuntimeServiceProviderEngine.INSTANCE

    async def _add_built_in_services(self) -> None:
        """Add built-in services that aren't part of the list of service descriptors."""
        await self._call_site_factory.add(
            ServiceIdentifier.from_service_type(
                TypedType.from_type(BaseServiceProvider)
            ),
            ServiceProviderCallSite(),
        )
        await self._call_site_factory.add(
            ServiceIdentifier.from_service_type(
                TypedType.from_type(ServiceScopeFactory)
            ),
            ConstantCallSite(
                TypedType.from_type(ServiceScopeFactory),
                self._root,
            ),
        )
        await self._call_site_factory.add(
            ServiceIdentifier.from_service_type(
                TypedType.from_type(ServiceProviderIsService)
            ),
            ConstantCallSite(
                TypedType.from_type(ServiceProviderIsService), self._call_site_factory
            ),
        )
        await self._call_site_factory.add(
            ServiceIdentifier.from_service_type(
                TypedType.from_type(ServiceProviderIsKeyedService)
            ),
            ConstantCallSite(
                TypedType.from_type(ServiceProviderIsKeyedService),
                self._call_site_factory,
            ),
        )

    async def _activate_auto_activated_singletons(self) -> None:
        """Activate all singletons registered with auto_activate=True."""
        for service_descriptor in self._services.descriptors:
            if not service_descriptor.auto_activate:
                continue

            await self.get_service_from_service_identifier(
                service_identifier=ServiceIdentifier.from_descriptor(
                    service_descriptor
                ),
                service_provider_engine_scope=self._root,
            )

    @override
    async def __aenter__(self) -> Self:
        await self._add_built_in_services()
        await self._activate_auto_activated_singletons()
        return self

    @override
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        self._is_disposed = True
        await self._root.__aexit__(exc_type, exc_val, exc_tb)
