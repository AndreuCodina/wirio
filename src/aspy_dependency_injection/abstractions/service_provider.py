from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager


class ServiceProvider(AbstractAsyncContextManager["ServiceProvider"], ABC):
    @abstractmethod
    def get_service(self, service_type: type) -> object | None: ...
