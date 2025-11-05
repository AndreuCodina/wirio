from typing import TYPE_CHECKING, Final, final

if TYPE_CHECKING:
    from aspy_dependency_injection.service_identifier import ServiceIdentifier


@final
class CallSiteChain:
    _call_site_chain: Final[dict[ServiceIdentifier, ChainItemInfo]]

    def __init__(self) -> None:
        self._call_site_chain = {}


class ChainItemInfo:
    _order: Final[int]
    _implementation_type: Final[type | None]

    def __init__(self, order: int, implementation_type: type | None) -> None:
        self._order = order
        self._implementation_type = implementation_type
