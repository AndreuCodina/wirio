from typing import Final, final

from wirio._service_lookup._service_identifier import (
    ServiceIdentifier,
)
from wirio._service_lookup._typed_type import TypedType
from wirio._service_lookup.call_site_result_cache_location import (
    CallSiteResultCacheLocation,
)
from wirio._service_lookup.service_cache_key import ServiceCacheKey
from wirio.service_lifetime import ServiceLifetime


@final
class ResultCache:
    """Track cached service."""

    _location: Final[CallSiteResultCacheLocation]
    _key: Final[ServiceCacheKey]

    def __init__(
        self, location: CallSiteResultCacheLocation, key: ServiceCacheKey
    ) -> None:
        self._location = location
        self._key = key

    @classmethod
    def from_lifetime(
        cls,
        lifetime: ServiceLifetime,
        service_identifier: ServiceIdentifier,
        slot: int,
    ) -> "ResultCache":
        match lifetime:
            case ServiceLifetime.SINGLETON:
                location = CallSiteResultCacheLocation.ROOT
            case ServiceLifetime.SCOPED:
                location = CallSiteResultCacheLocation.SCOPE
            case ServiceLifetime.TRANSIENT:
                location = CallSiteResultCacheLocation.DISPOSE

        key = ServiceCacheKey(service_identifier, slot)
        return cls(location, key)

    @classmethod
    def none(cls, service_type: TypedType) -> "ResultCache":
        cache_key = ServiceCacheKey(
            service_identifier=ServiceIdentifier.from_service_type(service_type), slot=0
        )
        return cls(CallSiteResultCacheLocation.NONE, cache_key)

    @property
    def location(self) -> CallSiteResultCacheLocation:
        return self._location

    @property
    def key(self) -> ServiceCacheKey:
        return self._key
