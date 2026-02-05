from collections.abc import Awaitable, Callable
from functools import partial
from typing import Final, Self, override

from wirio._service_lookup._typed_type import TypedType
from wirio.exceptions import NonKeyedDescriptorMisuseError
from wirio.service_lifetime import ServiceLifetime


class ServiceDescriptor:
    """Service registration."""

    _service_type: Final[TypedType]
    _lifetime: Final[ServiceLifetime]
    _implementation_type: TypedType | None
    _implementation_instance: object | None
    _sync_implementation_factory: Callable[..., object] | None
    _async_implementation_factory: Callable[..., Awaitable[object]] | None
    _service_key: object | None
    _auto_activate: bool

    def __init__(
        self,
        service_type: type,
        service_key: object | None,
        lifetime: ServiceLifetime,
        auto_activate: bool,
    ) -> None:
        self._service_type = TypedType.from_type(service_type)
        self._service_key = service_key
        self._lifetime = lifetime
        self._auto_activate = auto_activate
        self._implementation_type = None
        self._implementation_instance = None
        self._sync_implementation_factory = None
        self._async_implementation_factory = None

    @classmethod
    def from_implementation_type(
        cls,
        service_type: type,
        implementation_type: type,
        service_key: object | None,
        lifetime: ServiceLifetime,
        auto_activate: bool,
    ) -> Self:
        self = cls(
            service_type=service_type,
            service_key=service_key,
            lifetime=lifetime,
            auto_activate=auto_activate,
        )
        self._implementation_type = TypedType.from_type(implementation_type)
        return self

    @classmethod
    def from_implementation_instance(
        cls,
        service_type: type,
        implementation_instance: object,
        service_key: object | None,
        lifetime: ServiceLifetime,
        auto_activate: bool,
    ) -> Self:
        self = cls(
            service_type=service_type,
            service_key=service_key,
            lifetime=lifetime,
            auto_activate=auto_activate,
        )
        self._implementation_instance = implementation_instance
        return self

    @classmethod
    def from_sync_implementation_factory(
        cls,
        service_type: type,
        implementation_factory: Callable[..., object],
        lifetime: ServiceLifetime,
        auto_activate: bool,
    ) -> Self:
        self = cls(
            service_type=service_type,
            service_key=None,
            lifetime=lifetime,
            auto_activate=auto_activate,
        )
        self._sync_implementation_factory = implementation_factory
        return self

    @classmethod
    def from_keyed_sync_implementation_factory(
        cls,
        service_type: type,
        implementation_factory: Callable[..., object],
        service_key: object | None,
        lifetime: ServiceLifetime,
        auto_activate: bool,
    ) -> Self:
        self = cls(
            service_type=service_type,
            service_key=service_key,
            lifetime=lifetime,
            auto_activate=auto_activate,
        )

        if service_key is None:
            none_keyed_implementation_factory = partial(implementation_factory, None)
            self._sync_implementation_factory = none_keyed_implementation_factory
        else:
            self._sync_implementation_factory = implementation_factory

        return self

    @classmethod
    def from_async_implementation_factory(
        cls,
        service_type: type,
        implementation_factory: Callable[..., Awaitable[object]],
        lifetime: ServiceLifetime,
        auto_activate: bool,
    ) -> Self:
        self = cls(
            service_type=service_type,
            service_key=None,
            lifetime=lifetime,
            auto_activate=auto_activate,
        )
        self._async_implementation_factory = implementation_factory
        return self

    @classmethod
    def from_keyed_async_implementation_factory(
        cls,
        service_type: type,
        implementation_factory: Callable[..., Awaitable[object]],
        service_key: object | None,
        lifetime: ServiceLifetime,
        auto_activate: bool,
    ) -> Self:
        self = cls(
            service_type=service_type,
            service_key=service_key,
            lifetime=lifetime,
            auto_activate=auto_activate,
        )

        if service_key is None:
            none_keyed_implementation_factory = partial(implementation_factory, None)
            self._async_implementation_factory = none_keyed_implementation_factory
        else:
            self._async_implementation_factory = implementation_factory

        return self

    @property
    def service_type(self) -> TypedType:
        return self._service_type

    @property
    def service_key(self) -> object | None:
        return self._service_key

    @property
    def lifetime(self) -> ServiceLifetime:
        return self._lifetime

    @property
    def auto_activate(self) -> bool:
        return self._auto_activate

    @auto_activate.setter
    def auto_activate(self, value: bool) -> None:
        self._auto_activate = value

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
        if self.is_keyed_service:
            return None

        return self._sync_implementation_factory

    @property
    def async_implementation_factory(
        self,
    ) -> Callable[..., Awaitable[object]] | None:
        if self.is_keyed_service:
            return None

        return self._async_implementation_factory

    @property
    def keyed_sync_implementation_factory(
        self,
    ) -> Callable[..., object] | None:
        """Get the factory used for creating keyed synchronous service instances, or raise :class:`NonKeyedDescriptorMisuseError` if :attr:`is_keyed_service` is `False`."""
        if not self.is_keyed_service:
            raise NonKeyedDescriptorMisuseError

        return self._sync_implementation_factory

    @property
    def keyed_async_implementation_factory(
        self,
    ) -> Callable[..., Awaitable[object]] | None:
        """Get the factory used for creating keyed asynchronous service instances, or raise :class:`NonKeyedDescriptorMisuseError` if :attr:`is_keyed_service` is `False`."""
        if not self.is_keyed_service:
            raise NonKeyedDescriptorMisuseError

        return self._async_implementation_factory

    @property
    def is_keyed_service(self) -> bool:
        return self._service_key is not None

    @property
    def keyed_implementation_type(self) -> TypedType | None:
        """Get the type that implements the service, or raise :class:`NonKeyedDescriptorMisuseError` if :attr:`is_keyed_service` is `False`."""
        if not self.is_keyed_service:
            raise NonKeyedDescriptorMisuseError

        return self._implementation_type

    @property
    def keyed_implementation_instance(self) -> object | None:
        """Get the instance that implements the service, or raise :class:`NonKeyedDescriptorMisuseError` if :attr:`is_keyed_service` is `False`."""
        if not self.is_keyed_service:
            raise NonKeyedDescriptorMisuseError

        return self._implementation_instance

    def has_implementation_type(self) -> bool:
        return self.get_implementation_type() is not None

    def get_implementation_type(self) -> TypedType | None:
        if self.is_keyed_service:
            return self.keyed_implementation_type

        return self._implementation_type

    def has_implementation_instance(self) -> bool:
        return self.get_implementation_instance() is not None

    def get_implementation_instance(self) -> object | None:
        if self.is_keyed_service:
            return self.keyed_implementation_instance

        return self._implementation_instance

    @override
    def __str__(self) -> str:  # noqa: PLR0911
        lifetime = f"service_type: {self.service_type}, lifetime: {self.lifetime}, "

        if self.is_keyed_service:
            lifetime += f"service_key: {self.service_key}, "

            if self.keyed_implementation_type is not None:
                return (
                    lifetime
                    + f"keyed_implementation_type: {self.keyed_implementation_type}"
                )

            if self.keyed_async_implementation_factory is not None:
                return (
                    lifetime
                    + f"keyed_async_implementation_factory: {self.keyed_async_implementation_factory}"
                )

            if self.keyed_sync_implementation_factory is not None:
                return (
                    lifetime
                    + f"keyed_sync_implementation_factory: {self.keyed_sync_implementation_factory}"
                )

            return (
                lifetime
                + f"keyed_implementation_instance: {self.keyed_implementation_instance}"
            )

        if self.implementation_type is not None:
            return lifetime + f"implementation_type: {self.implementation_type}"

        if self.async_implementation_factory is not None:
            return (
                lifetime
                + f"async_implementation_factory: {self.async_implementation_factory}"
            )

        if self.sync_implementation_factory is not None:
            return (
                lifetime
                + f"sync_implementation_factory: {self.sync_implementation_factory}"
            )

        return lifetime + (f"implementation_instance: {self.implementation_instance}")
