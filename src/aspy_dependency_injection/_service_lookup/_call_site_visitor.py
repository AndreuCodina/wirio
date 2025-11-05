from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from aspy_dependency_injection._service_lookup._constructor_call_site import (
    ConstructorCallSite,
)

if TYPE_CHECKING:
    from aspy_dependency_injection._service_lookup._service_call_site import (
        ServiceCallSite,
    )


class CallSiteVisitor[TArgument, TResult](ABC):
    def _visit_call_site(
        self, call_site: ServiceCallSite, argument: TArgument
    ) -> TResult:
        return self._visit_no_cache(call_site, argument)

    def _visit_no_cache(
        self, call_site: ServiceCallSite, argument: TArgument
    ) -> TResult:
        return self._visit_call_site_main(call_site, argument)

    def _visit_call_site_main(
        self, call_site: ServiceCallSite, argument: TArgument
    ) -> TResult:
        if not isinstance(call_site, ConstructorCallSite):
            error_message = (
                f"Expected ConstructorCallSite, got {type(call_site).__name__}"
            )
            raise TypeError(error_message)

        return self._visit_constructor(call_site, argument)

    @abstractmethod
    def _visit_constructor(
        self, constructor_call_site: ConstructorCallSite, argument: TArgument
    ) -> TResult: ...
