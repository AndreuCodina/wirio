from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from types import TracebackType

    from aspy_dependency_injection.abstractions.service_provider import (
        ServiceProvider,
    )


class ServiceScope(ABC):
    """Defines a disposable service scope.

    The __aexit__ method ends the scope lifetime. Once called, any scoped
    services that have been resolved from ServiceProvider will be disposed.
    """

    @property
    @abstractmethod
    def service_provider(self) -> ServiceProvider:
        """Gets the ServiceProvider used to resolve dependencies from the scope."""

    @abstractmethod
    def get_service(self, service_type: type) -> object | None: ...

    @abstractmethod
    def __aenter__(self) -> Self: ...

    @abstractmethod
    def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
        /,
    ) -> bool | None: ...
