from wirio.abstractions.keyed_service import KeyedService


class TestKeyedService:
    def test_stringify_any_key(self) -> None:
        any_key = KeyedService.ANY_KEY

        assert str(any_key) == "*"
