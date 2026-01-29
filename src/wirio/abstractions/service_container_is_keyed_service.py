from abc import ABC, abstractmethod

from wirio.abstractions.service_container_is_service import (
    ServiceContainerIsService,
)


class ServiceContainerIsKeyedService(ServiceContainerIsService, ABC):
    """Provide methods to determine if the specified service type with the specified service key is available from the :class:`BaseServiceContainer`."""

    @abstractmethod
    def is_keyed_service(self, service_key: object | None, service_type: type) -> bool:
        """Determine if the specified service type with the specified service key is available from the :class:`BaseServiceContainer`."""
        ...
