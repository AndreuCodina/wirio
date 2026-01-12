from typing import ClassVar, final


@final
class AspyUndefined:
    """A type used as a sentinel for undefined values."""

    INSTANCE: ClassVar["AspyUndefined"]


AspyUndefined.INSTANCE = AspyUndefined()
