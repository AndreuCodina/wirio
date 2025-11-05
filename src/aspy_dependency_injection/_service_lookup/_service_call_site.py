from abc import ABC, abstractmethod


class ServiceCallSite(ABC):
    @property
    @abstractmethod
    def service_type(self) -> type: ...
