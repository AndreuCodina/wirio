from typing import TypeVar

from aspy_dependency_injection.default_service_provider import (
    DefaultServiceProvider,
)
from aspy_dependency_injection.service_descriptor import ServiceDescriptor
from aspy_dependency_injection.service_lifetime import ServiceLifetime

TService = TypeVar("TService")


class ServiceCollection:
    """Collection of service descriptors provided during configuration."""

    descriptors: list[ServiceDescriptor]

    def __init__(self) -> None:
        self.descriptors = []

    def add_transient(self, service_type: type) -> None:
        self._add(service_type, ServiceLifetime.TRANSIENT)

    def add_singleton(self, service: type) -> None:
        pass

    def add_scoped(self, service: type) -> None:
        pass

    def build_service_provider(self) -> DefaultServiceProvider:
        """Create a DefaultServiceProvider containing services from the provided ServiceCollection."""
        return DefaultServiceProvider(self)

    @classmethod
    async def uninitialize(cls) -> None:
        pass

    def _add(self, service: type, lifetime: ServiceLifetime) -> None:
        descriptor = ServiceDescriptor(service, lifetime)
        self.descriptors.append(descriptor)
