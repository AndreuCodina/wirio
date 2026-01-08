from collections.abc import Hashable
from typing import (
    TYPE_CHECKING,
    Final,
    final,
    override,
)

if TYPE_CHECKING:
    from aspy_dependency_injection._service_lookup._typed_type import TypedType
    from aspy_dependency_injection.service_descriptor import ServiceDescriptor


@final
class ServiceIdentifier(Hashable):
    """Internal registered service during resolution."""

    _service_type: Final[TypedType]

    def __init__(self, service_type: TypedType) -> None:
        self._service_type = service_type

    @property
    def service_type(self) -> TypedType:
        return self._service_type

    @classmethod
    def from_service_type(cls, service_type: TypedType) -> ServiceIdentifier:
        return cls(service_type)

    @classmethod
    def from_descriptor(
        cls, service_descriptor: ServiceDescriptor
    ) -> ServiceIdentifier:
        return cls(service_descriptor.service_type)

    @override
    def __hash__(self) -> int:
        return hash(self._service_type)

    @override
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, ServiceIdentifier):
            return NotImplemented

        return self._service_type == value._service_type
