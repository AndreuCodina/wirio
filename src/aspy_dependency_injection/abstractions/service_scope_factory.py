from abc import ABC, abstractmethod

from aspy_dependency_injection.abstractions.service_scope import ServiceScope


class ServiceScopeFactory(ABC):
    @abstractmethod
    def create_scope(self) -> ServiceScope: ...
