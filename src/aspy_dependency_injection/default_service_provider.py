from dataclasses import dataclass
from typing import TYPE_CHECKING, Self, final, override

from aspy_dependency_injection._async_concurrent_dictionary import (
    AsyncConcurrentDictionary,
)
from aspy_dependency_injection.abstractions.service_provider import ServiceProvider
from aspy_dependency_injection.service_identifier import ServiceIdentifier
from aspy_dependency_injection.service_lookup.call_site_chain import CallSiteChain
from aspy_dependency_injection.service_lookup.call_site_factory import CallSiteFactory
from aspy_dependency_injection.service_lookup.runtime_service_provider_engine import (
    RuntimeServiceProviderEngine,
)
from aspy_dependency_injection.service_provider_engine_scope import (
    ServiceProviderEngineScope,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import TracebackType

    from aspy_dependency_injection.abstractions.service_scope import ServiceScope
    from aspy_dependency_injection.service_collection import ServiceCollection
    from aspy_dependency_injection.service_lookup.service_call_site import (
        ServiceCallSite,
    )
    from aspy_dependency_injection.service_lookup.service_provider_engine import (
        ServiceProviderEngine,
    )


@dataclass(frozen=True)
class _ServiceAccessor:
    call_site: ServiceCallSite | None
    realized_service: Callable[[ServiceProviderEngineScope], object | None]


@final
class DefaultServiceProvider(ServiceProvider):
    """Provider that resolves services."""

    _services: ServiceCollection
    _root: ServiceProviderEngineScope
    _engine: ServiceProviderEngine
    _service_accessors: AsyncConcurrentDictionary[ServiceIdentifier, _ServiceAccessor]

    def __init__(self, services: ServiceCollection) -> None:
        self._services = services
        self._root = ServiceProviderEngineScope(
            service_provider=self, is_root_scope=True
        )
        self._engine = self._get_engine()
        self._service_accessors = AsyncConcurrentDictionary()
        self._call_site_factory = CallSiteFactory(services)

    @override
    async def get_service(self, service_type: type) -> object | None:
        return await self.get_service_from_service_identifier(
            service_identifier=ServiceIdentifier.from_service_type(service_type),
            service_provider_engine_scope=self._root,
        )

    # @asynccontextmanager
    def create_scope(self) -> ServiceScope:  # AsyncGenerator[ServiceScope]:
        """Create a new ServiceScope that can be used to resolve scoped services."""
        # async with DefaultServiceScope(service_provider=self) as service_scope:
        #     yield service_scope
        return ServiceProviderEngineScope(service_provider=self, is_root_scope=False)

    async def get_service_from_service_identifier(
        self,
        service_identifier: ServiceIdentifier,
        service_provider_engine_scope: ServiceProviderEngineScope,
    ) -> object | None:
        service_accessor = await self._service_accessors.get_or_add(
            key=service_identifier, value_factory=self._create_service_accessor
        )
        return service_accessor.realized_service(service_provider_engine_scope)

    async def _create_service_accessor(
        self, service_identifier: ServiceIdentifier
    ) -> _ServiceAccessor:
        call_site = await self._call_site_factory.get_call_site(
            service_identifier, CallSiteChain()
        )

        if call_site is not None:
            realized_service = self._engine.realize_service(call_site)
            return _ServiceAccessor(
                call_site=call_site, realized_service=realized_service
            )

        return _ServiceAccessor(call_site=call_site, realized_service=lambda _: None)

    def _get_engine(self) -> ServiceProviderEngine:
        return RuntimeServiceProviderEngine.INSTANCE

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        await self._root.__aexit__(exc_type, exc_val, exc_tb)
