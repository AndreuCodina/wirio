from contextlib import AbstractAsyncContextManager
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from types import TracebackType


class ServiceWithNoDependencies:
    pass


class ServiceWithDependencies:
    def __init__(self, service_with_no_dependencies: ServiceWithNoDependencies) -> None:
        self.service_with_no_dependencies = service_with_no_dependencies


class ServiceWithAsyncContextManagerAndNoDependencies(
    AbstractAsyncContextManager["ServiceWithAsyncContextManagerAndNoDependencies"]
):
    @override
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        return None
