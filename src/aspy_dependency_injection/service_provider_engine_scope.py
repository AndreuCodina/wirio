from typing import TYPE_CHECKING, Final, Self, final, override

from aspy_dependency_injection.abstractions.service_scope import ServiceScope
from aspy_dependency_injection.abstractions.service_scope_factory import (
    ServiceScopeFactory,
)
from aspy_dependency_injection.service_identifier import ServiceIdentifier

if TYPE_CHECKING:
    from types import TracebackType

    from aspy_dependency_injection.abstractions.service_provider import (
        ServiceProvider,
    )
    from aspy_dependency_injection.default_service_provider import (
        DefaultServiceProvider,
    )


@final
class ServiceProviderEngineScope(ServiceScope, ServiceScopeFactory):
    """Container resolving services with scope."""

    _root_provider: Final[DefaultServiceProvider]
    _is_root_scope: Final[bool]

    def __init__(
        self,
        service_provider: DefaultServiceProvider,
        is_root_scope: bool,  # noqa: FBT001
    ) -> None:
        self._root_provider = service_provider
        self._is_root_scope = is_root_scope

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
        pass
