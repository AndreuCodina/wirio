from types import TracebackType
from typing import Protocol, Self, runtime_checkable


@runtime_checkable
class SupportsSyncContextManager(Protocol):
    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None: ...
