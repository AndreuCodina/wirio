from collections.abc import Sequence

from tests.utils.services import ServiceWithNoDependencies
from wirio._service_lookup._result_cache import ResultCache
from wirio._service_lookup._sequence_call_site import SequenceCallSite
from wirio._service_lookup._service_identifier import ServiceIdentifier
from wirio._service_lookup._typed_type import TypedType
from wirio._service_lookup.call_site_result_cache_location import (
    CallSiteResultCacheLocation,
)
from wirio._service_lookup.service_cache_key import ServiceCacheKey


class TestSequenceCallSite:
    def test_get_service_type(self) -> None:
        expected_type = TypedType.from_type(Sequence[ServiceWithNoDependencies])
        type_ = TypedType.from_type(ServiceWithNoDependencies)
        result_cache = ResultCache(
            CallSiteResultCacheLocation.NONE,
            ServiceCacheKey(
                ServiceIdentifier(
                    service_key=None,
                    service_type=type_,
                ),
                slot=0,
            ),
        )

        service_call_site = SequenceCallSite(
            result_cache=result_cache,
            item_type=type_,
            service_call_sites=[],
            service_key=None,
        )

        assert service_call_site.service_type == expected_type
