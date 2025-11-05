from typing import TYPE_CHECKING, ClassVar, final, override

from aspy_dependency_injection._service_lookup._call_site_runtime_resolver import (
    CallSiteRuntimeResolver,
)
from aspy_dependency_injection._service_lookup._service_provider_engine import (
    ServiceProviderEngine,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from aspy_dependency_injection._service_lookup._service_call_site import (
        ServiceCallSite,
    )
    from aspy_dependency_injection.service_provider_engine_scope import (
        ServiceProviderEngineScope,
    )


@final
class RuntimeServiceProviderEngine(ServiceProviderEngine):
    INSTANCE: ClassVar[RuntimeServiceProviderEngine]

    @override
    def realize_service(
        self, call_site: ServiceCallSite
    ) -> Callable[[ServiceProviderEngineScope], object | None]:
        return lambda scope: CallSiteRuntimeResolver.INSTANCE.resolve(call_site, scope)


RuntimeServiceProviderEngine.INSTANCE = RuntimeServiceProviderEngine()
