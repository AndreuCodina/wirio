from collections.abc import Awaitable, Callable
from typing import ClassVar, final, override

from wirio._service_lookup._call_site_runtime_resolver import (
    CallSiteRuntimeResolver,
)
from wirio._service_lookup._service_call_site import (
    ServiceCallSite,
)
from wirio._service_lookup._service_provider_engine import (
    ServiceProviderEngine,
)
from wirio.service_provider_engine_scope import (
    ServiceProviderEngineScope,
)


@final
class RuntimeServiceProviderEngine(ServiceProviderEngine):
    INSTANCE: ClassVar["RuntimeServiceProviderEngine"]

    @override
    def realize_service(
        self, call_site: ServiceCallSite
    ) -> Callable[[ServiceProviderEngineScope], Awaitable[object | None]]:
        def _create_realize_service(
            scope: ServiceProviderEngineScope,
        ) -> Awaitable[object | None]:
            return CallSiteRuntimeResolver.INSTANCE.resolve(call_site, scope)

        return _create_realize_service


RuntimeServiceProviderEngine.INSTANCE = RuntimeServiceProviderEngine()
