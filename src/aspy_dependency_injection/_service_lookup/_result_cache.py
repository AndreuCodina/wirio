from typing import TYPE_CHECKING, Final, final

from aspy_dependency_injection._service_lookup.call_site_result_cache_location import (
    CallSiteResultCacheLocation,
)
from aspy_dependency_injection._service_lookup.service_cache_key import ServiceCacheKey
from aspy_dependency_injection.service_lifetime import ServiceLifetime

if TYPE_CHECKING:
    from aspy_dependency_injection._service_lookup._service_identifier import (
        ServiceIdentifier,
    )


@final
class ResultCache:
    _location: Final[CallSiteResultCacheLocation]
    _key: Final[ServiceCacheKey]

    def __init__(
        self,
        lifetime: ServiceLifetime,
        service_identifier: ServiceIdentifier,
        slot: int,
    ) -> None:
        match lifetime:
            case ServiceLifetime.TRANSIENT:
                self._location = CallSiteResultCacheLocation.DISPOSE
            case _:
                self._location = CallSiteResultCacheLocation.NONE

        self._key = ServiceCacheKey(service_identifier, slot)

    @property
    def location(self) -> CallSiteResultCacheLocation:
        return self._location
