from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from aspy_dependency_injection.service_identifier import ServiceIdentifier


class CallSiteChain:
    _call_site_chain: Final[dict[ServiceIdentifier, _ChainItemInfo]]

    def __init__(self) -> None:
        self._call_site_chain = {}


class _ChainItemInfo:
    order: Final[int]
    implementation_type: Final[type | None]

    def __init__(self, order: int, implementation_type: type | None) -> None:
        self.order = order
        self.implementation_type = implementation_type
