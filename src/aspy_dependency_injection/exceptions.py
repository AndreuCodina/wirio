from aspy_dependency_injection.abstractions.base_service_provider import (
    BaseServiceProvider,
)


class ObjectDisposedError(Exception):
    """The exception that is thrown when an operation is performed on a disposed object."""

    def __init__(self) -> None:
        super().__init__(BaseServiceProvider.__name__)
