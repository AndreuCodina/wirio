from typing import Final, final, override

from aspy_dependency_injection._service_lookup._call_site_kind import CallSiteKind
from aspy_dependency_injection._service_lookup._result_cache import ResultCache
from aspy_dependency_injection._service_lookup._service_call_site import ServiceCallSite
from aspy_dependency_injection._service_lookup._typed_type import TypedType


@final
class ConstantCallSite(ServiceCallSite):
    _service_type: Final[TypedType]

    def __init__(self, service_type: TypedType, default_value: object) -> None:
        result_cache = ResultCache.none(service_type=service_type)
        self._service_type = service_type

        if not isinstance(default_value, service_type.to_type()):
            error_message = f"Constant value of type '{type(default_value)}' can't be converted to service type '{service_type.to_type()}'"
            raise TypeError(error_message)

        super().__init__(result_cache, default_value)

    @property
    @override
    def service_type(self) -> TypedType:
        return self._service_type

    @property
    @override
    def kind(self) -> CallSiteKind:
        return CallSiteKind.CONSTANT

    @property
    def default_value(self) -> object:
        return self._value
