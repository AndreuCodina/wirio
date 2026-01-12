from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable

from aspy_dependency_injection._service_lookup._service_call_site import (
    ServiceCallSite,
)
from aspy_dependency_injection.service_provider_engine_scope import (
    ServiceProviderEngineScope,
)


class ServiceProviderEngine(ABC):
    @abstractmethod
    def realize_service(
        self, call_site: ServiceCallSite
    ) -> Callable[[ServiceProviderEngineScope], Awaitable[object | None]]: ...
