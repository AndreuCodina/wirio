from collections.abc import Hashable
from typing import TYPE_CHECKING, Final, final, override

if TYPE_CHECKING:
    from aspy_dependency_injection._service_lookup._service_identifier import (
        ServiceIdentifier,
    )


@final
class ServiceCacheKey(Hashable):
    _service_identifier: Final[ServiceIdentifier]
    _slot: Final[int]

    def __init__(self, service_identifier: ServiceIdentifier, slot: int) -> None:
        self._service_identifier = service_identifier
        self._slot = slot

    @property
    def service_identifier(self) -> ServiceIdentifier:
        return self._service_identifier

    @property
    def slot(self) -> int:
        return self._slot

    @override
    def __hash__(self) -> int:
        return (hash(self._service_identifier) * 397) ^ self._slot

    @override
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, ServiceCacheKey):
            return NotImplemented

        return (
            self._service_identifier == value.service_identifier
            and self._slot == value.slot
        )
