from abc import ABC, abstractmethod


class ServiceContainerIsService(ABC):
    """Provide methods to determine if the specified service type is available from the :class:`BaseServiceContainer`."""

    @abstractmethod
    def is_service(self, service_type: type) -> bool:
        """Determine if the specified service type is available from the :class:`BaseServiceContainer`."""
        ...
