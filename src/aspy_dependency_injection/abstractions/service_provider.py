from abc import ABC, abstractmethod


class ServiceProvider(ABC):
    @abstractmethod
    def get_service(self, service_type: type) -> object | None: ...
