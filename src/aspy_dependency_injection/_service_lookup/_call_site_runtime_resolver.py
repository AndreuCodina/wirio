from contextlib import AbstractAsyncContextManager, AbstractContextManager
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Never, final, override

from aspy_dependency_injection._service_lookup._call_site_visitor import CallSiteVisitor

if TYPE_CHECKING:
    from aspy_dependency_injection._service_lookup._constructor_call_site import (
        ConstructorCallSite,
    )
    from aspy_dependency_injection._service_lookup._service_call_site import (
        ServiceCallSite,
    )
    from aspy_dependency_injection.service_provider_engine_scope import (
        ServiceProviderEngineScope,
    )


@dataclass
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
            if hasattr(service, AbstractAsyncContextManager[Never].__aexit__.__name__):
                await service.__aexit__(None, None, None)  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
            elif hasattr(service, AbstractContextManager[Never].__exit__.__name__):
                await service.__exit__(None, None, None)  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]

        return service

    @override
    async def _visit_dispose_cache(
        self, call_site: ServiceCallSite, argument: RuntimeResolverContext
    ) -> object | None:
        service = await self._visit_call_site_main(call_site, argument)
        return await argument.scope.capture_disposable(service)


CallSiteRuntimeResolver.INSTANCE = CallSiteRuntimeResolver()
