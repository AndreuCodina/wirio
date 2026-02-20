from wirio._service_lookup._service_provider_call_site import ServiceProviderCallSite
from wirio._service_lookup._typed_type import TypedType
from wirio.abstractions.base_service_provider import BaseServiceProvider


class TestServiceProviderCallSite:
    def test_return_service_type(self) -> None:
        call_site = ServiceProviderCallSite()

        assert call_site.service_type == TypedType.from_type(BaseServiceProvider)
