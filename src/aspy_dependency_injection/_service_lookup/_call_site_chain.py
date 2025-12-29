from typing import TYPE_CHECKING, Final, final

if TYPE_CHECKING:
    from aspy_dependency_injection._service_lookup._service_identifier import (
        ServiceIdentifier,
    )
    from tests._service_lookup.test_typed_type import TypedType


@final
class CallSiteChain:
    _call_site_chain: Final[dict[ServiceIdentifier, _ChainItemInformation]]

    def __init__(self) -> None:
        self._call_site_chain = {}

    def add(
        self,
        service_identifier: ServiceIdentifier,
        implementation_type: TypedType | None = None,
    ) -> None:
        self._call_site_chain[service_identifier] = _ChainItemInformation(
            order=len(self._call_site_chain), implementation_type=implementation_type
        )

    def remove(self, service_identifier: ServiceIdentifier) -> None:
        del self._call_site_chain[service_identifier]

    def check_circular_dependency(self, service_identifier: ServiceIdentifier) -> None:
        if service_identifier in self._call_site_chain:
            error_message = f"A circular dependency was detected for the service of type '{service_identifier.service_type}'"
            raise RuntimeError(error_message)


@final
class _ChainItemInformation:
    _order: Final[int]
    _implementation_type: Final[TypedType | None]

    def __init__(self, order: int, implementation_type: TypedType | None) -> None:
        self._order = order
        self._implementation_type = implementation_type
