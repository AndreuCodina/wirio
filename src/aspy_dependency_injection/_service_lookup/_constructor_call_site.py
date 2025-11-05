from typing import TYPE_CHECKING, Final, final, override

from aspy_dependency_injection._service_lookup._service_call_site import ServiceCallSite

if TYPE_CHECKING:
    from aspy_dependency_injection._service_lookup._constructor_information import (
        ConstructorInformation,
    )


@final
class ConstructorCallSite(ServiceCallSite):
    _service_type: Final[type]
    _constructor_information: Final[ConstructorInformation]
    _parameter_call_sites: Final[list[ServiceCallSite]]

    def __init__(
        self,
        service_type: type,
        constructor_information: ConstructorInformation,
        parameter_call_sites: list[ServiceCallSite],
    ) -> None:
        self._service_type = service_type
        self._constructor_information = constructor_information
        self._parameter_call_sites = parameter_call_sites

    @property
    @override
    def service_type(self) -> type:
        return self._service_type

    @property
    def constructor_information(self) -> ConstructorInformation:
        return self._constructor_information

    @property
    def parameter_call_sites(self) -> list[ServiceCallSite]:
        return self._parameter_call_sites
