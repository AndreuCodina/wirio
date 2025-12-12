import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, Self, final, override

from aspy_dependency_injection._async_concurrent_dictionary import (
    AsyncConcurrentDictionary,
)
from aspy_dependency_injection._service_lookup._call_site_chain import CallSiteChain
from aspy_dependency_injection._service_lookup._call_site_factory import CallSiteFactory
from aspy_dependency_injection._service_lookup._runtime_service_provider_engine import (
    RuntimeServiceProviderEngine,
)
from aspy_dependency_injection._service_lookup._service_identifier import (
    ServiceIdentifier,
)
from aspy_dependency_injection.abstractions.service_provider import ServiceProvider
from aspy_dependency_injection.service_provider_engine_scope import (
    ServiceProviderEngineScope,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from types import TracebackType

    from aspy_dependency_injection._service_lookup._service_call_site import (
        ServiceCallSite,
    )
    from aspy_dependency_injection._service_lookup._service_provider_engine import (
        ServiceProviderEngine,
    )
    from aspy_dependency_injection.abstractions.service_scope import ServiceScope
    from aspy_dependency_injection.service_collection import ServiceCollection


@dataclass(frozen=True)
class ServiceAccessor:
    call_site: ServiceCallSite | None
    realized_service: Callable[[ServiceProviderEngineScope], Awaitable[object | None]]


@final
class DefaultServiceProvider(ServiceProvider):
    """Provider that resolves services."""

    _services: Final[ServiceCollection]
    _root: Final[ServiceProviderEngineScope]
    _engine: Final[ServiceProviderEngine]
    _service_accessors: Final[
        AsyncConcurrentDictionary[ServiceIdentifier, ServiceAccessor]
    ]
    _is_disposed: bool

    def __init__(self, services: ServiceCollection) -> None:
        self._services = services
        self._root = ServiceProviderEngineScope(
            service_provider=self, is_root_scope=True
        )
        self._engine = self._get_engine()
        self._service_accessors = AsyncConcurrentDictionary()
        self._call_site_factory = CallSiteFactory(services)
        self._is_disposed = False

    @property
    def is_disposed(self) -> bool:
        return self._is_disposed

    @override
    async def get_service(self, service_type: type) -> object | None:
        return await self.get_service_from_service_identifier(
            service_identifier=ServiceIdentifier.from_service_type(service_type),
            service_provider_engine_scope=self._root,
        )

    def create_scope(self) -> ServiceScope:
        """Create a new ServiceScope that can be used to resolve scoped services."""
        return ServiceProviderEngineScope(service_provider=self, is_root_scope=False)

    async def get_service_from_service_identifier(
        self,
        service_identifier: ServiceIdentifier,
        service_provider_engine_scope: ServiceProviderEngineScope,
    ) -> object | None:
        service_accessor = await self._service_accessors.get_or_add(
            key=service_identifier, value_factory=self._create_service_accessor
        )
        return await service_accessor.realized_service(service_provider_engine_scope)

    async def _create_service_accessor(
        self, service_identifier: ServiceIdentifier
    ) -> ServiceAccessor:
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
            return ServiceAccessor(
                call_site=call_site, realized_service=realized_service
            )

        return ServiceAccessor(
            call_site=call_site, realized_service=realized_service_returning_none
        )

    def _get_engine(self) -> ServiceProviderEngine:
        return RuntimeServiceProviderEngine.INSTANCE

    @override
    async def __aenter__(self) -> Self:
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
