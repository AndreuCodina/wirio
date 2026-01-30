from abc import ABC, abstractmethod


class ServiceProviderIsService(ABC):
    """Provide methods to determine if the specified service type is available from the :class:`BaseServiceProvider`."""

    @abstractmethod
    def is_service(self, service_type: type) -> bool:
        """Determine if the specified service type is available from the :class:`BaseServiceProvider`."""
        ...
