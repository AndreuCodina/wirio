from typing import TYPE_CHECKING, Final, Self

if TYPE_CHECKING:
    from aspy_dependency_injection.service_lifetime import ServiceLifetime


class ServiceDescriptor:
    """Service registration."""

    service_type: Final[type]
    lifetime: Final[ServiceLifetime]
    implementation_type: type | None

    def __init__(self, service_type: type, lifetime: ServiceLifetime) -> None:
        self.service_type = service_type
        self.lifetime = lifetime
        self.implementation_type = None

    @classmethod
    def from_implementation_type(
        cls, service_type: type, implementation_type: type, lifetime: ServiceLifetime
    ) -> Self:
        """Initialize a new instance of ServiceDescriptor with the specified implementation_type."""
        self = cls(service_type=service_type, lifetime=lifetime)
        self.implementation_type = implementation_type
        return self
