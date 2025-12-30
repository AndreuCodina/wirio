from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, cast

from aspy_dependency_injection._service_lookup._call_site_kind import CallSiteKind
from aspy_dependency_injection._service_lookup.call_site_result_cache_location import (
    CallSiteResultCacheLocation,
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
    from aspy_dependency_injection._service_lookup._service_provider_call_site import (
        ServiceProviderCallSite,
    )
    from aspy_dependency_injection._service_lookup._sync_factory_call_site import (
        SyncFactoryCallSite,
    )


class CallSiteVisitor[TArgument, TResult](ABC):
    async def _visit_call_site(
        self, call_site: ServiceCallSite, argument: TArgument
    ) -> TResult:
        match call_site.cache.location:
            case CallSiteResultCacheLocation.ROOT:
                return await self._visit_root_cache(call_site, argument)
            case CallSiteResultCacheLocation.SCOPE:
                return await self._visit_scope_cache(call_site, argument)
            case CallSiteResultCacheLocation.DISPOSE:
                return await self._visit_dispose_cache(call_site, argument)
            case CallSiteResultCacheLocation.NONE:
                return await self._visit_no_cache(call_site, argument)

    async def _visit_root_cache(
        self, call_site: ServiceCallSite, argument: TArgument
    ) -> TResult:
        return await self._visit_call_site_main(call_site, argument)

    async def _visit_scope_cache(
        self, call_site: ServiceCallSite, argument: TArgument
    ) -> TResult:
        return await self._visit_call_site_main(call_site, argument)

    async def _visit_dispose_cache(
        self, call_site: ServiceCallSite, argument: TArgument
    ) -> TResult:
        return await self._visit_call_site_main(call_site, argument)

    async def _visit_no_cache(
        self, call_site: ServiceCallSite, argument: TArgument
    ) -> TResult:
        return await self._visit_call_site_main(call_site, argument)

    async def _visit_call_site_main(
        self, call_site: ServiceCallSite, argument: TArgument
    ) -> TResult:
        match call_site.kind:
            case CallSiteKind.SYNC_FACTORY:
                return await self._visit_sync_factory(
                    sync_factory_call_site=cast("SyncFactoryCallSite", call_site),
                    argument=argument,
                )
            case CallSiteKind.ASYNC_FACTORY:
                return await self._visit_async_factory(
                    async_factory_call_site=cast("AsyncFactoryCallSite", call_site),
                    argument=argument,
                )
            case CallSiteKind.CONSTRUCTOR:
                return await self._visit_constructor(
                    constructor_call_site=cast("ConstructorCallSite", call_site),
                    argument=argument,
                )
            case CallSiteKind.SERVICE_PROVIDER:
                return self._visit_service_provider(
                    service_provider_call_site=cast(
                        "ServiceProviderCallSite", call_site
                    ),
                    argument=argument,
                )

    @abstractmethod
    async def _visit_constructor(
        self, constructor_call_site: ConstructorCallSite, argument: TArgument
    ) -> TResult: ...

    @abstractmethod
    async def _visit_sync_factory(
        self, sync_factory_call_site: SyncFactoryCallSite, argument: TArgument
    ) -> TResult: ...

    @abstractmethod
    async def _visit_async_factory(
        self, async_factory_call_site: AsyncFactoryCallSite, argument: TArgument
    ) -> TResult: ...

    @abstractmethod
    def _visit_service_provider(
        self, service_provider_call_site: ServiceProviderCallSite, argument: TArgument
    ) -> TResult: ...
