from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, final, override

from aspy_dependency_injection._service_lookup._call_site_visitor import CallSiteVisitor
from aspy_dependency_injection._service_lookup._supports_async_context_manager import (
    SupportsAsyncContextManager,
)
from aspy_dependency_injection._service_lookup._supports_context_manager import (
    SupportsContextManager,
)

if TYPE_CHECKING:
    from aspy_dependency_injection._service_lookup._async_factory_call_site import (
        AsyncFactoryCallSite,
    )
    from aspy_dependency_injection._service_lookup._constructor_call_site import (
        ConstructorCallSite,
    )
    from aspy_dependency_injection._service_lookup._service_call_site import (
        ServiceCallSite,
    )
    from aspy_dependency_injection._service_lookup._sync_factory_call_site import (
        SyncFactoryCallSite,
    )
    from aspy_dependency_injection.service_provider_engine_scope import (
        ServiceProviderEngineScope,
    )


@dataclass(frozen=True)
class RuntimeResolverContext:
    scope: ServiceProviderEngineScope


@final
class CallSiteRuntimeResolver(CallSiteVisitor[RuntimeResolverContext, object | None]):
    INSTANCE: ClassVar[CallSiteRuntimeResolver]

    async def resolve(
        self, call_site: ServiceCallSite, scope: ServiceProviderEngineScope
    ) -> object | None:
        return await self._visit_call_site(
            call_site, RuntimeResolverContext(scope=scope)
        )

    @override
    async def _visit_constructor(
        self,
        constructor_call_site: ConstructorCallSite,
        argument: RuntimeResolverContext,
    ) -> object:
        parameter_values: list[object | None] = [
            await self._visit_call_site(parameter_call_site, argument)
            for parameter_call_site in constructor_call_site.parameter_call_sites
        ]
        service = constructor_call_site.constructor_information.invoke(parameter_values)

        if service is not self:
            if isinstance(service, SupportsAsyncContextManager):
                await service.__aenter__()
            elif isinstance(service, SupportsContextManager):
                service.__enter__()

        return service

    @override
    async def _visit_dispose_cache(
        self, call_site: ServiceCallSite, argument: RuntimeResolverContext
    ) -> object | None:
        service = await self._visit_call_site_main(call_site, argument)
        return await argument.scope.capture_disposable(service)

    @override
    def _visit_sync_factory(
        self,
        sync_factory_call_site: SyncFactoryCallSite,
        argument: RuntimeResolverContext,
    ) -> object | None:
        return sync_factory_call_site.implementation_factory(argument.scope)

    @override
    async def _visit_async_factory(
        self,
        async_factory_call_site: AsyncFactoryCallSite,
        argument: RuntimeResolverContext,
    ) -> object | None:
        return await async_factory_call_site.implementation_factory(argument.scope)


CallSiteRuntimeResolver.INSTANCE = CallSiteRuntimeResolver()
