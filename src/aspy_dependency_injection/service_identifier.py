from collections.abc import Hashable
from typing import TYPE_CHECKING, Final, final, override

if TYPE_CHECKING:
    from aspy_dependency_injection.service_descriptor import ServiceDescriptor


@final
class ServiceIdentifier(Hashable):
    """Internal registered service during resolution."""

    service_type: Final[type]

    def __init__(self, service_type: type) -> None:
        self.service_type = service_type

    @classmethod
    def from_service_type(cls, service_type: type) -> ServiceIdentifier:
        return cls(service_type)

    @classmethod
    def from_descriptor(
        cls, service_descriptor: ServiceDescriptor
    ) -> ServiceIdentifier:
        return cls(service_descriptor.service_type)

    @override
    def __hash__(self) -> int:
        return hash(self.service_type)

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, ServiceIdentifier):
            return NotImplemented

        return self.service_type == value.service_type
