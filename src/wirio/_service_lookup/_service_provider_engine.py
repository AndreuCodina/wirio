from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable

from wirio._service_lookup._service_call_site import (
    ServiceCallSite,
)
from wirio.service_provider_engine_scope import (
    ServiceProviderEngineScope,
)


class ServiceProviderEngine(ABC):
    @abstractmethod
    def realize_service(
        self, call_site: ServiceCallSite
    ) -> Callable[[ServiceProviderEngineScope], Awaitable[object | None]]: ...
