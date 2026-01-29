from collections.abc import Hashable
from typing import (
    Final,
    final,
    override,
)

from wirio._service_lookup._typed_type import TypedType
from wirio.service_descriptor import ServiceDescriptor


@final
class ServiceIdentifier(Hashable):
    """Internal registered service during resolution."""

    _service_key: Final[object | None]
    _service_type: Final[TypedType]

    def __init__(self, service_key: object | None, service_type: TypedType) -> None:
        self._service_key = service_key
        self._service_type = service_type

    @property
    def service_key(self) -> object | None:
        return self._service_key

    @property
    def service_type(self) -> TypedType:
        return self._service_type

    @classmethod
    def from_service_type(
        cls, service_type: TypedType, service_key: object | None = None
    ) -> "ServiceIdentifier":
        return cls(service_key=service_key, service_type=service_type)

    @classmethod
    def from_descriptor(
        cls, service_descriptor: ServiceDescriptor
    ) -> "ServiceIdentifier":
        return cls(
            service_key=service_descriptor.service_key,
            service_type=service_descriptor.service_type,
        )

    @override
    def __hash__(self) -> int:
        if self.service_key is None:
            return hash(self._service_type)

        return (hash(self._service_type) * 397) ^ hash(self._service_key)

    @override
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, ServiceIdentifier):
            return NotImplemented

        if self.service_key is None and value.service_key is None:
            return self.service_type == value.service_type

        if self.service_key is not None and value.service_key is not None:
            return (
                self.service_type == value.service_type
                and self.service_key == value.service_key
            )

        return False
