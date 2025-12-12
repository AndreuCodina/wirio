from typing import TYPE_CHECKING, Final, Self

if TYPE_CHECKING:
    from aspy_dependency_injection.service_lifetime import ServiceLifetime


class ServiceDescriptor:
    """Service registration."""

    _service_type: Final[type]
    _lifetime: Final[ServiceLifetime]
    _implementation_type: type | None

    def __init__(self, service_type: type, lifetime: ServiceLifetime) -> None:
        self._service_type = service_type
        self._lifetime = lifetime
        self._implementation_type = None

    @property
    def service_type(self) -> type:
        return self._service_type

    @property
    def lifetime(self) -> ServiceLifetime:
        return self._lifetime

    @property
    def implementation_type(self) -> type | None:
        return self._implementation_type

    @classmethod
    def from_implementation_type(
        cls, service_type: type, implementation_type: type, lifetime: ServiceLifetime
    ) -> Self:
        """Initialize a new instance of ServiceDescriptor with the specified implementation_type."""
        self = cls(service_type=service_type, lifetime=lifetime)
        self._implementation_type = implementation_type
        return self

    def has_implementation_type(self) -> bool:
        return self._implementation_type is not None
