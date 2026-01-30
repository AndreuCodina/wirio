from typing import ClassVar, final


@final
class WirioUndefined:
    """A type used as a sentinel for undefined values."""

    INSTANCE: ClassVar["WirioUndefined"]


WirioUndefined.INSTANCE = WirioUndefined()
