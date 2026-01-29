from types import TracebackType
from typing import Protocol, Self, runtime_checkable


@runtime_checkable
class SupportsAsyncContextManager(Protocol):
    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None: ...
