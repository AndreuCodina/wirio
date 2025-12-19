from typing import TYPE_CHECKING, Final, Self

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aspy_dependency_injection.abstractions.service_provider import ServiceProvider
    from aspy_dependency_injection.service_lifetime import ServiceLifetime


class ServiceDescriptor:
    """Service registration."""

    _service_type: Final[type]
    _lifetime: Final[ServiceLifetime]
    _implementation_type: type | None
    _sync_implementation_factory: Callable[[ServiceProvider], object] | None
    _async_implementation_factory: Callable[[ServiceProvider], Awaitable[object]] | None

    def __init__(self, service_type: type, lifetime: ServiceLifetime) -> None:
        self._service_type = service_type
        self._lifetime = lifetime
        self._implementation_type = None
        self._sync_implementation_factory = None
        self._async_implementation_factory = None

    @property
    def service_type(self) -> type:
        return self._service_type

    @property
    def lifetime(self) -> ServiceLifetime:
        return self._lifetime

    @property
    def implementation_type(self) -> type | None:
        return self._implementation_type

    @property
    def sync_implementation_factory(self) -> Callable[[ServiceProvider], object] | None:
        return self._sync_implementation_factory

    @property
    def async_implementation_factory(
        self,
    ) -> Callable[[ServiceProvider], Awaitable[object]] | None:
        return self._async_implementation_factory

    @classmethod
    def from_implementation_type(
        cls, service_type: type, implementation_type: type, lifetime: ServiceLifetime
    ) -> Self:
        self = cls(service_type=service_type, lifetime=lifetime)
        self._implementation_type = implementation_type
        return self

    @classmethod
    def from_sync_implementation_factory(
        cls,
        service_type: type,
        implementation_factory: Callable[[ServiceProvider], object],
        lifetime: ServiceLifetime,
    ) -> Self:
        self = cls(service_type=service_type, lifetime=lifetime)
        self._sync_implementation_factory = implementation_factory
        return self

    @classmethod
    def from_async_implementation_factory(
        cls,
        service_type: type,
        implementation_factory: Callable[[ServiceProvider], Awaitable[object]],
        lifetime: ServiceLifetime,
    ) -> Self:
        self = cls(service_type=service_type, lifetime=lifetime)
        self._async_implementation_factory = implementation_factory
        return self

    def has_implementation_type(self) -> bool:
        return self._implementation_type is not None
