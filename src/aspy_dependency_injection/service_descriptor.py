from typing import TYPE_CHECKING, Final, Self

from aspy_dependency_injection._service_lookup._typed_type import TypedType

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aspy_dependency_injection.service_lifetime import ServiceLifetime


class ServiceDescriptor:
    """Service registration."""

    _service_type: Final[TypedType]
    _lifetime: Final[ServiceLifetime]
    _implementation_type: TypedType | None
    _implementation_instance: object | None
    _sync_implementation_factory: Callable[..., object] | None
    _async_implementation_factory: Callable[..., Awaitable[object]] | None

    def __init__(self, service_type: type, lifetime: ServiceLifetime) -> None:
        self._service_type = TypedType.from_type(service_type)
        self._lifetime = lifetime
        self._implementation_type = None
        self._implementation_instance = None
        self._sync_implementation_factory = None
        self._async_implementation_factory = None

    @property
    def service_type(self) -> TypedType:
        return self._service_type

    @property
    def lifetime(self) -> ServiceLifetime:
        return self._lifetime

    @property
    def implementation_type(self) -> TypedType | None:
        return self._implementation_type

    @property
    def implementation_instance(self) -> object | None:
        return self._implementation_instance

    @property
    def sync_implementation_factory(
        self,
    ) -> Callable[..., object] | None:
        return self._sync_implementation_factory

    @property
    def async_implementation_factory(
        self,
    ) -> Callable[..., Awaitable[object]] | None:
        return self._async_implementation_factory

    @classmethod
    def from_implementation_type(
        cls, service_type: type, implementation_type: type, lifetime: ServiceLifetime
    ) -> Self:
        self = cls(service_type=service_type, lifetime=lifetime)
        self._implementation_type = TypedType.from_type(implementation_type)
        return self

    @classmethod
    def from_implementation_instance(
        cls,
        service_type: type,
        implementation_instance: object,
        lifetime: ServiceLifetime,
    ) -> Self:
        self = cls(service_type=service_type, lifetime=lifetime)
        self._implementation_instance = implementation_instance
        return self

    @classmethod
    def from_sync_implementation_factory(
        cls,
        service_type: type,
        implementation_factory: Callable[..., object],
        lifetime: ServiceLifetime,
    ) -> Self:
        self = cls(service_type=service_type, lifetime=lifetime)
        self._sync_implementation_factory = implementation_factory
        return self

    @classmethod
    def from_async_implementation_factory(
        cls,
        service_type: type,
        implementation_factory: Callable[..., Awaitable[object]],
        lifetime: ServiceLifetime,
    ) -> Self:
        self = cls(service_type=service_type, lifetime=lifetime)
        self._async_implementation_factory = implementation_factory
        return self

    def has_implementation_type(self) -> bool:
        return self._implementation_type is not None
