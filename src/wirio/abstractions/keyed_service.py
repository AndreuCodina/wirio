from typing import ClassVar, final


@final
class KeyedService:
    """Provide static APIs for use with `KeyedServiceProvider`."""

    @final
    class AnyKeyObj:
        def __str__(self) -> str:
            return "*"

    ANY_KEY: ClassVar[object] = AnyKeyObj()
