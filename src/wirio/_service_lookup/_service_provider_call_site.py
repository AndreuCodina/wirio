from typing import Final, final, override

from wirio._service_lookup._call_site_kind import CallSiteKind
from wirio._service_lookup._result_cache import ResultCache
from wirio._service_lookup._service_call_site import ServiceCallSite
from wirio._service_lookup._typed_type import TypedType
from wirio.base_service_container import BaseServiceContainer


@final
class ServiceProviderCallSite(ServiceCallSite):
    _service_type: Final[TypedType]

    def __init__(self) -> None:
        service_type = TypedType.from_type(BaseServiceContainer)
        result_cache = ResultCache.none(service_type=service_type)
        self._service_type = service_type
        super().__init__(cache=result_cache, key=None)

    @property
    @override
    def service_type(self) -> TypedType:
        return self._service_type

    @property
    @override
    def kind(self) -> CallSiteKind:
        return CallSiteKind.SERVICE_PROVIDER
