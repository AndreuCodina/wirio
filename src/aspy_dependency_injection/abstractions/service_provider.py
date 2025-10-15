from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aspy_dependency_injection.abstractions.service_scope import ServiceScope


class ServiceProvider(ABC):
    @abstractmethod
    def get_service(self, service_type: type) -> object | None: ...

    @abstractmethod
    def create_scope(self) -> ServiceScope: ...
