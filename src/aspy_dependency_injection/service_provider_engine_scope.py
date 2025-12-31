import asyncio
from typing import TYPE_CHECKING, Final, Self, final, override

from aspy_dependency_injection._service_lookup._service_identifier import (
    ServiceIdentifier,
)
from aspy_dependency_injection._service_lookup._supports_async_context_manager import (
    SupportsAsyncContextManager,
)
from aspy_dependency_injection._service_lookup._supports_context_manager import (
    SupportsContextManager,
)
from aspy_dependency_injection.abstractions.base_service_provider import (
    BaseServiceProvider,
)
from aspy_dependency_injection.abstractions.service_scope import ServiceScope
from aspy_dependency_injection.abstractions.service_scope_factory import (
    ServiceScopeFactory,
)
from aspy_dependency_injection.exceptions import ObjectDisposedError

if TYPE_CHECKING:
    from types import TracebackType

    from aspy_dependency_injection._service_lookup._typed_type import TypedType
    from aspy_dependency_injection._service_lookup.service_cache_key import (
        ServiceCacheKey,
    )
    from aspy_dependency_injection.service_provider import (
        ServiceProvider,
    )


@final
class ServiceProviderEngineScope(
    ServiceScope, BaseServiceProvider, ServiceScopeFactory
):
    """Container resolving services with scope."""

    _root_provider: Final[ServiceProvider]
    _is_root_scope: Final[bool]
    _is_disposed: bool
    _disposables: list[object] | None
    _resolved_services: Final[dict[ServiceCacheKey, object | None]]
    _resolved_services_lock: Final[asyncio.Lock]

    def __init__(self, service_provider: ServiceProvider, is_root_scope: bool) -> None:
        self._root_provider = service_provider
        self._is_root_scope = is_root_scope
        self._is_disposed = False
        self._disposables = None
        self._resolved_services = {}
        self._resolved_services_lock = asyncio.Lock()

    @property
    def root_provider(self) -> ServiceProvider:
        return self._root_provider

    @property
    def is_root_scope(self) -> bool:
        return self._is_root_scope

    @property
    def realized_services(self) -> dict[ServiceCacheKey, object | None]:
        return self._resolved_services

    @property
    def resolved_services_lock(self) -> asyncio.Lock:
        """Protect the state on the scope.

        In particular, for the root scope, it protects the list of disposable entries only, since :attr:`resolved_services` are cached on :class:`CallSites`.

        For other scopes, it protects :attr:`resolved_services` and the list of disposables.
        """
        return self._resolved_services_lock

    @property
    @override
    def service_provider(self) -> BaseServiceProvider:
        return self

    @override
    def create_scope(self) -> ServiceScope:
        return self._root_provider.create_scope()

    @override
    async def get_service_object(self, service_type: TypedType) -> object | None:
        if self._is_disposed:
            raise ObjectDisposedError

        return await self._root_provider.get_service_from_service_identifier(
            service_identifier=ServiceIdentifier.from_service_type(service_type),
            service_provider_engine_scope=self,
        )

    async def capture_disposable(self, service: object | None) -> object | None:
        if service is self or not (
            isinstance(service, (SupportsAsyncContextManager, SupportsContextManager))
        ):
            return service

        is_disposed = False

        async with self._resolved_services_lock:
            if self._is_disposed:
                is_disposed = True
            else:
                if self._disposables is None:
                    self._disposables = []

                self._disposables.append(service)

        # Don't run customer code under the lock
        if is_disposed:
            if isinstance(service, SupportsAsyncContextManager):
                await service.__aexit__(None, None, None)
            else:
                service.__exit__(None, None, None)

            raise ObjectDisposedError

        return service

    async def _begin_dispose(self) -> list[object] | None:
        async with self._resolved_services_lock:
            if self._is_disposed:
                return None

            # We've transitioned to the disposed state, so future calls to
            # :meth:`capture_disposable` will immediately dispose the object.
            # No further changes to disposables are allowed.
            self._is_disposed = True

        if self._is_root_scope and not self._root_provider.is_disposed:
            # If this :class:`ServiceProviderEngineScope` instance is a root scope, disposing this instance will need to dispose the :attr:`root_provider` too.
            # Otherwise the :attr:`root_provider` will never get disposed and will leak.
            # Note, if the :attr:`root_provider` gets disposed first, it will automatically dispose all attached :class:`ServiceProviderEngineScope` objects.
            await self._root_provider.__aexit__(None, None, None)

        # :attr:`_resolved_services` is never cleared for singletons because there might be a compilation running in background
        # trying to get a cached singleton service. If it doesn't find it
        # it will try to create a new one which will result in an :class:`ObjectDisposedError`.
        return self._disposables

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
        to_dispose = await self._begin_dispose()

        if to_dispose is None:
            return None

        for i in range(len(to_dispose) - 1, -1, -1):
            service = to_dispose[i]

            if isinstance(service, SupportsAsyncContextManager):
                await service.__aexit__(None, None, None)
            elif isinstance(service, SupportsContextManager):
                service.__exit__(None, None, None)
