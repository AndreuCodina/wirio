from typing import Final, final, override

from wirio._service_lookup._call_site_kind import CallSiteKind
from wirio._service_lookup._constructor_information import (
    ConstructorInformation,
)
from wirio._service_lookup._parameter_information import (
    ParameterInformation,
)
from wirio._service_lookup._result_cache import ResultCache
from wirio._service_lookup._service_call_site import ServiceCallSite
from wirio._service_lookup._typed_type import TypedType


@final
class ConstructorCallSite(ServiceCallSite):
    _service_type: Final[TypedType]
    _constructor_information: Final[ConstructorInformation]
    _parameters: Final[list[ParameterInformation]]
    _parameter_call_sites: Final[list[ServiceCallSite | None]]

    def __init__(  # noqa: PLR0913
        self,
        cache: ResultCache,
        service_type: TypedType,
        constructor_information: ConstructorInformation,
        parameters: list[ParameterInformation],
        parameter_call_sites: list[ServiceCallSite | None],
        service_key: object | None = None,
    ) -> None:
        super().__init__(cache=cache, key=service_key)
        self._service_type = service_type
        self._constructor_information = constructor_information
        self._parameters = parameters
        self._parameter_call_sites = parameter_call_sites

    @property
    @override
    def service_type(self) -> TypedType:
        return self._service_type

    @property
    @override
    def kind(self) -> CallSiteKind:
        return CallSiteKind.CONSTRUCTOR

    @property
    def constructor_information(self) -> ConstructorInformation:
        return self._constructor_information

    @property
    def parameters(self) -> list[ParameterInformation]:
        return self._parameters

    @property
    def parameter_call_sites(self) -> list[ServiceCallSite | None]:
        return self._parameter_call_sites
