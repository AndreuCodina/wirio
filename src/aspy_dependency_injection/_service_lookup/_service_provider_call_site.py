from typing import Final, final, override

from aspy_dependency_injection._service_lookup._call_site_kind import CallSiteKind
from aspy_dependency_injection._service_lookup._result_cache import ResultCache
from aspy_dependency_injection._service_lookup._service_call_site import ServiceCallSite
from aspy_dependency_injection._service_lookup._typed_type import TypedType
from aspy_dependency_injection.abstractions.base_service_provider import (
    BaseServiceProvider,
)


@final
class ServiceProviderCallSite(ServiceCallSite):
    _service_type: Final[TypedType]

    def __init__(self) -> None:
        self._service_type = TypedType.from_type(BaseServiceProvider)
        result_cache = ResultCache.none(service_type=self._service_type)
        super().__init__(result_cache)

    @property
    @override
    def service_type(self) -> TypedType:
        return self._service_type

    @property
    @override
    def kind(self) -> CallSiteKind:
        return CallSiteKind.SERVICE_PROVIDER
