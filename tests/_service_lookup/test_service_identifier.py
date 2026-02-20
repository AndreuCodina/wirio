from wirio._service_lookup._service_identifier import (
    ServiceIdentifier,
)
from wirio._service_lookup._typed_type import TypedType


class TestServiceIdentifier:
    def test_equality_with_same_type_and_no_key(self) -> None:
        service_identifier_1 = ServiceIdentifier(
            service_key=None, service_type=TypedType.from_type(int)
        )
        service_identifier_2 = ServiceIdentifier(
            service_key=None, service_type=TypedType.from_type(int)
        )

        assert service_identifier_1 == service_identifier_2

    def test_inequality_with_different_types_and_no_key(
        self,
    ) -> None:
        service_identifier_1 = ServiceIdentifier(
            service_key=None, service_type=TypedType.from_type(int)
        )
        service_identifier_2 = ServiceIdentifier(
            service_key=None, service_type=TypedType.from_type(str)
        )

        assert service_identifier_1 != service_identifier_2

    def test_equality_with_same_type_and_same_key(self) -> None:
        service_identifier_1 = ServiceIdentifier(
            service_key="key", service_type=TypedType.from_type(int)
        )
        service_identifier_2 = ServiceIdentifier(
            service_key="key", service_type=TypedType.from_type(int)
        )

        assert service_identifier_1 == service_identifier_2

    def test_inequality_with_same_type_and_different_keys(
        self,
    ) -> None:
        service_identifier_1 = ServiceIdentifier(
            service_key="key_a", service_type=TypedType.from_type(int)
        )
        service_identifier_2 = ServiceIdentifier(
            service_key="key_b", service_type=TypedType.from_type(int)
        )

        assert service_identifier_1 != service_identifier_2

    def test_inequality_with_different_types_and_different_keys(
        self,
    ) -> None:
        service_identifier_1 = ServiceIdentifier(
            service_key="key_a", service_type=TypedType.from_type(int)
        )
        service_identifier_2 = ServiceIdentifier(
            service_key="key_b", service_type=TypedType.from_type(str)
        )

        assert service_identifier_1 != service_identifier_2

    def test_inequality_when_only_one_has_key(self) -> None:
        service_identifier_1 = ServiceIdentifier(
            service_key=None, service_type=TypedType.from_type(int)
        )
        service_identifier_2 = ServiceIdentifier(
            service_key="key", service_type=TypedType.from_type(int)
        )

        assert service_identifier_1 != service_identifier_2

    def test_inequality_with_non_service_identifier(
        self,
    ) -> None:
        service_identifier = ServiceIdentifier(
            service_key=None, service_type=TypedType.from_type(int)
        )
        non_service_identifier = "another_type"

        assert service_identifier != non_service_identifier

    def test_stringify_non_keyed_service_identifier(self) -> None:
        service_type = TypedType.from_type(int)

        service_identifier = ServiceIdentifier(
            service_key=None, service_type=TypedType.from_type(int)
        )

        assert str(service_identifier) == repr(service_type)

    def test_stringify_keyed_service_identifier(self) -> None:
        service_key = "key"
        service_type = TypedType.from_type(int)

        service_identifier = ServiceIdentifier(
            service_key=service_key, service_type=service_type
        )

        assert str(service_identifier) == f"({service_key}, {service_type!r})"
