from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from aspy_dependency_injection._service_lookup._constructor_call_site import (
    ConstructorCallSite,
)
from aspy_dependency_injection._service_lookup.call_site_result_cache_location import (
    CallSiteResultCacheLocation,
)

if TYPE_CHECKING:
    from aspy_dependency_injection._service_lookup._service_call_site import (
        ServiceCallSite,
    )


class CallSiteVisitor[TArgument, TResult](ABC):
    async def _visit_call_site(
        self, call_site: ServiceCallSite, argument: TArgument
    ) -> TResult:
        match call_site.cache.location:
            case CallSiteResultCacheLocation.DISPOSE:
                return await self._visit_dispose_cache(call_site, argument)
            case CallSiteResultCacheLocation.NONE:
                return await self._visit_no_cache(call_site, argument)
            case _:
                raise NotImplementedError

    async def _visit_no_cache(
        self, call_site: ServiceCallSite, argument: TArgument
    ) -> TResult:
        return await self._visit_call_site_main(call_site, argument)

    async def _visit_dispose_cache(
        self, call_site: ServiceCallSite, argument: TArgument
    ) -> TResult:
        return await self._visit_call_site_main(call_site, argument)

    async def _visit_call_site_main(
        self, call_site: ServiceCallSite, argument: TArgument
    ) -> TResult:
        if not isinstance(call_site, ConstructorCallSite):
            error_message = f"Expected {ConstructorCallSite.__name__}, got {type(call_site).__name__}"
            raise TypeError(error_message)

        return await self._visit_constructor(call_site, argument)

    @abstractmethod
    async def _visit_constructor(
        self, constructor_call_site: ConstructorCallSite, argument: TArgument
    ) -> TResult: ...
