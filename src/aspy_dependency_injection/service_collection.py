from typing import TypeVar

from aspy_dependency_injection.default_service_provider import (
    DefaultServiceProvider,
    ServiceProvider,
)
from aspy_dependency_injection.service_descriptor import ServiceDescriptor
from aspy_dependency_injection.service_lifetime import ServiceLifetime

TService = TypeVar("TService", bound=object)


class ServiceCollection:  # extends  : IList<ServiceDescriptor>
    """Collection of service descriptors provided during configuration."""

    # private readonly List<ServiceDescriptor> _descriptors = new List<ServiceDescriptor>();

    descriptors: list[ServiceDescriptor]

    def __init__(self) -> None:
        self.descriptors = []

    def add_transient(self, service_type: type) -> None:
        self._add(service_type, ServiceLifetime.TRANSIENT)

    def _add(self, service: type, lifetime: ServiceLifetime) -> None:
        descriptor = ServiceDescriptor(service, lifetime)
        self.descriptors.append(descriptor)

    def add_singleton(self, service: type) -> None:
        pass

    def add_scoped(self, service: type) -> None:
        pass

    def build_service_provider(self) -> ServiceProvider:
        return DefaultServiceProvider(self)

    @classmethod
    async def uninitialize(cls) -> None:
        pass
