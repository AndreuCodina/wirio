import asyncio
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from typing import TYPE_CHECKING, Final, Never, Self, final, override

from aspy_dependency_injection._service_lookup._service_identifier import (
    ServiceIdentifier,
)
from aspy_dependency_injection.abstractions.service_provider import (
    ServiceProvider,
)
from aspy_dependency_injection.abstractions.service_scope import ServiceScope
from aspy_dependency_injection.abstractions.service_scope_factory import (
    ServiceScopeFactory,
)
from aspy_dependency_injection.exceptions import ObjectDisposedError

if TYPE_CHECKING:
    from types import TracebackType

    from aspy_dependency_injection.default_service_provider import (
        DefaultServiceProvider,
    )


@final
class ServiceProviderEngineScope(ServiceScope, ServiceScopeFactory):
    """Container resolving services with scope."""

    _root_provider: Final[DefaultServiceProvider]
    _is_root_scope: Final[bool]
    _is_disposed: bool

    # This lock protects state on the scope, in particular, for the root scope, it protects
    # the list of disposable entries only, since ResolvedServices are cached on CallSites
    # For other scopes, it protects ResolvedServices and the list of disposables
    _resolved_services_lock: asyncio.Lock

    _disposables: list[object] | None

    def __init__(
        self,
        service_provider: DefaultServiceProvider,
        is_root_scope: bool,  # noqa: FBT001
    ) -> None:
        self._root_provider = service_provider
        self._is_root_scope = is_root_scope
        self._is_disposed = False
        self._resolved_services_lock = asyncio.Lock()
        self._disposables = None

    @property
    @override
    def service_provider(self) -> ServiceProvider:
        return self._root_provider

    @override
    def create_scope(self) -> ServiceScope:
        return self._root_provider.create_scope()

    @override
    async def get_service(self, service_type: type) -> object | None:
        return await self._root_provider.get_service_from_service_identifier(
            service_identifier=ServiceIdentifier.from_service_type(service_type),
            service_provider_engine_scope=self,
        )

    async def capture_disposable(self, service: object | None) -> object | None:
        if service is self or not (
            hasattr(service, AbstractAsyncContextManager[Never].__aexit__.__name__)
            or hasattr(service, AbstractContextManager[Never].__exit__.__name__)
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
            if service is not None:
                if hasattr(
                    service, AbstractAsyncContextManager[Never].__aexit__.__name__
                ):
                    await service.__aexit__(None, None, None)  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
                elif hasattr(service, AbstractContextManager[Never].__exit__.__name__):
                    service.__exit__(None, None, None)  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]

            raise ObjectDisposedError(ServiceProvider.__name__)

        return service

    async def _begin_dispose(self) -> list[object] | None:
        async with self._resolved_services_lock:
            if self._is_disposed:
                return None

            # We've transitioned to the disposed state, so future calls to
            # capture_disposable will immediately dispose the object.
            # No further changes to _state.Disposables, are allowed.
            self._is_disposed = True

        if self._is_root_scope and not self._root_provider.is_disposed:
            # If this ServiceProviderEngineScope instance is a root scope, disposing this instance will need to dispose the RootProvider too.
            # Otherwise the RootProvider will never get disposed and will leak.
            # Note, if the RootProvider gets disposed first, it will automatically dispose all attached ServiceProviderEngineScope objects.
            await self._root_provider.__aexit__(None, None, None)

        # _resolved_services is never cleared for singletons because there might be a compilation running in background
        # trying to get a cached singleton service. If it doesn't find it
        # it will try to create a new one which will result in an ObjectDisposedException.
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
            if hasattr(
                to_dispose[i], AbstractAsyncContextManager[Never].__aexit__.__name__
            ):
                await to_dispose[i].__aexit__(None, None, None)  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
            elif hasattr(
                to_dispose[i], AbstractContextManager[Never].__exit__.__name__
            ):
                to_dispose[i].__exit__(None, None, None)  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
