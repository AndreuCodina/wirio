from abc import ABC, abstractmethod

from wirio.abstractions.service_provider_is_service import (
    ServiceProviderIsService,
)


class ServiceProviderIsKeyedService(ServiceProviderIsService, ABC):
    """Provide methods to determine if the specified service type with the specified service key is available from the :class:`BaseServiceProvider`."""

    @abstractmethod
    def is_keyed_service(self, service_key: object | None, service_type: type) -> bool:
        """Determine if the specified service type with the specified service key is available from the :class:`BaseServiceProvider`."""
        ...
