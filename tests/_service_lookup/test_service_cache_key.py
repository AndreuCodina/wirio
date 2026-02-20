from wirio._service_lookup._service_identifier import ServiceIdentifier
from wirio._service_lookup._typed_type import TypedType
from wirio._service_lookup.service_cache_key import ServiceCacheKey


class TestServiceCacheKey:
    def test_equality_and_hash_with_same_service_identifier_and_slot(
        self,
    ) -> None:
        service_identifier = ServiceIdentifier(
            service_key=None, service_type=TypedType.from_type(int)
        )
        service_cache_key_1 = ServiceCacheKey(
            service_identifier=service_identifier, slot=0
        )
        service_cache_key_2 = ServiceCacheKey(
            service_identifier=service_identifier, slot=0
        )

        assert service_cache_key_1 == service_cache_key_2
        assert hash(service_cache_key_1) == hash(service_cache_key_2)

    def test_inequality_and_hash_with_different_service_identifier_and_same_slot(
        self,
    ) -> None:
        service_cache_key_1 = ServiceCacheKey(
            service_identifier=ServiceIdentifier(
                service_key=None, service_type=TypedType.from_type(int)
            ),
            slot=0,
        )
        service_cache_key_2 = ServiceCacheKey(
            service_identifier=ServiceIdentifier(
                service_key=None, service_type=TypedType.from_type(str)
            ),
            slot=0,
        )

        assert service_cache_key_1 != service_cache_key_2
        assert hash(service_cache_key_1) != hash(service_cache_key_2)

    def test_inequality_and_hash_with_same_service_identifier_and_different_slot(
        self,
    ) -> None:
        service_identifier = ServiceIdentifier(
            service_key=None, service_type=TypedType.from_type(int)
        )
        service_cache_key_1 = ServiceCacheKey(
            service_identifier=service_identifier, slot=0
        )
        service_cache_key_2 = ServiceCacheKey(
            service_identifier=service_identifier, slot=1
        )

        assert service_cache_key_1 != service_cache_key_2
        assert hash(service_cache_key_1) != hash(service_cache_key_2)

    def test_inequality_with_non_service_cache_key(self) -> None:
        service_cache_key = ServiceCacheKey(
            service_identifier=ServiceIdentifier(
                service_key=None, service_type=TypedType.from_type(int)
            ),
            slot=0,
        )

        assert service_cache_key != "other"
