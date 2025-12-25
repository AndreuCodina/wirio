from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aspy_dependency_injection.abstractions.service_scope import ServiceScope


class ServiceScopeFactory(ABC):
    @abstractmethod
    def create_scope(self) -> ServiceScope: ...
