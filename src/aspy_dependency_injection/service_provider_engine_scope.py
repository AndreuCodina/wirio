from typing import TYPE_CHECKING, Final, Self

from aspy_dependency_injection.abstractions.service_scope import ServiceScope
from aspy_dependency_injection.service_identifier import ServiceIdentifier

if TYPE_CHECKING:
    from types import TracebackType

    from aspy_dependency_injection.abstractions.service_provider import (
        ServiceProvider,
    )
    from aspy_dependency_injection.default_service_provider import (
        DefaultServiceProvider,
    )


class ServiceProviderEngineScope(ServiceScope):
    """Container resolving services with scope."""

    _root_provider: Final[DefaultServiceProvider]

    def __init__(self, service_provider: DefaultServiceProvider) -> None:
        self._root_provider = service_provider

    @property
    def service_provider(self) -> ServiceProvider:
        return self._root_provider

    def __aenter__(self) -> Self:
        return self

    def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
        /,
    ) -> bool | None:
        pass

    def create_scope(self) -> ServiceScope:
        return ServiceProviderEngineScope(self._root_provider)

    def get_service(self, service_type: type) -> object | None:
        return self._root_provider.get_service_from_service_identifier(
            ServiceIdentifier.from_service_type(service_type)
        )
