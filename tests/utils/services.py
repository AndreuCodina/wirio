from contextlib import AbstractAsyncContextManager, AbstractContextManager
from typing import TYPE_CHECKING, Self, override

if TYPE_CHECKING:
    from types import TracebackType


class ServiceWithNoDependencies:
    pass


class ServiceWithDependencies:
    def __init__(self, service_with_no_dependencies: ServiceWithNoDependencies) -> None:
        self.service_with_no_dependencies = service_with_no_dependencies


class DisposeViewer:
    def __init__(self) -> None:
        self.is_disposed = False
        self.is_disposed_initialized = False

    def _enter_context(self) -> None:
        self.is_disposed_initialized = True

    def _exit_context(self) -> None:
        if not self.is_disposed_initialized:
            error_message = (
                "__aenter__/__enter__ was not called before __aexit__/__exit__."
            )
            raise RuntimeError(error_message)

        self.is_disposed = True


class ServiceWithAsyncContextManagerAndNoDependencies(
    DisposeViewer,
    AbstractAsyncContextManager["ServiceWithAsyncContextManagerAndNoDependencies"],
):
    @override
    async def __aenter__(self) -> Self:
        self._enter_context()
        return self

    @override
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        self._exit_context()
        return None


class ServiceWithAsyncContextManagerAndDependencies(
    DisposeViewer,
    AbstractAsyncContextManager["ServiceWithAsyncContextManagerAndDependencies"],
):
    def __init__(
        self,
        service_with_async_context_manager_and_no_dependencies: ServiceWithAsyncContextManagerAndNoDependencies,
    ) -> None:
        super().__init__()
        self.service_with_async_context_manager_and_no_dependencies = (
            service_with_async_context_manager_and_no_dependencies
        )

    @override
    async def __aenter__(self) -> Self:
        self._enter_context()
        return self

    @override
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        self._exit_context()
        return None


class ServiceWithSyncContextManagerAndNoDependencies(
    DisposeViewer,
    AbstractContextManager["ServiceWithSyncContextManagerAndNoDependencies"],
):
    def __enter__(
        self,
    ) -> Self:
        self._enter_context()
        return self

    @override
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        self._exit_context()
        return None


class SelfCircularDependencyService:
    def __init__(self, service: SelfCircularDependencyService) -> None:
        self.service = service


class ServiceWithGeneric[T]:
    pass
