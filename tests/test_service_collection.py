from contextlib import AbstractAsyncContextManager, AbstractContextManager
from typing import TYPE_CHECKING, Self, override

import pytest

from aspy_dependency_injection.abstractions.base_service_provider import (
    BaseServiceProvider,
)
from aspy_dependency_injection.service_collection import ServiceCollection
from aspy_dependency_injection.service_lifetime import ServiceLifetime
from tests.utils.services import (
    DisposeViewer,
    SelfCircularDependencyService,
    ServiceWithAsyncContextManagerAndDependencies,
    ServiceWithAsyncContextManagerAndNoDependencies,
    ServiceWithDependencies,
    ServiceWithNoDependencies,
    ServiceWithSyncContextManagerAndNoDependencies,
)

if TYPE_CHECKING:
    from types import TracebackType


class TestServiceCollection:
    @pytest.mark.parametrize(
        argnames=("service_lifetime"),
        argvalues=[
            ServiceLifetime.SINGLETON,
            ServiceLifetime.SCOPED,
            ServiceLifetime.TRANSIENT,
        ],
        ids=["singleton", "scoped", "transient"],
    )
    async def test_resolve_service_with_no_dependencies(
        self, service_lifetime: ServiceLifetime
    ) -> None:
        services = ServiceCollection()

        match service_lifetime:
            case ServiceLifetime.SINGLETON:
                services.add_singleton(ServiceWithNoDependencies)
            case ServiceLifetime.SCOPED:
                services.add_scoped(ServiceWithNoDependencies)
            case ServiceLifetime.TRANSIENT:
                services.add_transient(ServiceWithNoDependencies)

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_service(
                ServiceWithNoDependencies
            )

            assert isinstance(resolved_service, ServiceWithNoDependencies)

    @pytest.mark.parametrize(
        argnames=("service_lifetime"),
        argvalues=[
            ServiceLifetime.SINGLETON,
            ServiceLifetime.SCOPED,
            ServiceLifetime.TRANSIENT,
        ],
        ids=["singleton", "scoped", "transient"],
    )
    async def test_resolve_service_using_scope(
        self, service_lifetime: ServiceLifetime
    ) -> None:
        services = ServiceCollection()

        match service_lifetime:
            case ServiceLifetime.SINGLETON:
                services.add_singleton(ServiceWithNoDependencies)
            case ServiceLifetime.SCOPED:
                services.add_scoped(ServiceWithNoDependencies)
            case ServiceLifetime.TRANSIENT:
                services.add_transient(ServiceWithNoDependencies)

        async with (
            services.build_service_provider() as service_provider,
            service_provider.create_scope() as service_scope,
        ):
            resolved_service = (
                await service_scope.service_provider.get_required_service(
                    ServiceWithNoDependencies
                )
            )

            assert isinstance(resolved_service, ServiceWithNoDependencies)

    @pytest.mark.parametrize(
        argnames=("is_async_implementation_factory"),
        argvalues=[
            True,
            False,
        ],
        ids=[
            "async_implementation_factory",
            "sync_implementation_factory",
        ],
    )
    async def test_resolve_transient_service_with_implementation_factory_and_no_dependencies(
        self,
        is_async_implementation_factory: bool,
    ) -> None:
        async def async_implementation_factory(
            _: BaseServiceProvider,
        ) -> ServiceWithNoDependencies:
            return ServiceWithNoDependencies()

        def sync_implementation_factory(
            _: BaseServiceProvider,
        ) -> ServiceWithNoDependencies:
            return ServiceWithNoDependencies()

        services = ServiceCollection()

        implementation_factory = (
            async_implementation_factory
            if is_async_implementation_factory
            else sync_implementation_factory
        )
        services.add_transient(ServiceWithNoDependencies, implementation_factory)

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_service(
                ServiceWithNoDependencies
            )

            assert isinstance(resolved_service, ServiceWithNoDependencies)

    async def test_resolve_transient_service_with_dependencies(self) -> None:
        services = ServiceCollection()
        services.add_transient(ServiceWithNoDependencies)
        services.add_transient(ServiceWithDependencies)

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_service(
                ServiceWithDependencies
            )

            assert isinstance(resolved_service, ServiceWithDependencies)
            assert isinstance(
                resolved_service.service_with_no_dependencies, ServiceWithNoDependencies
            )

    @pytest.mark.parametrize(
        argnames=("service_type"),
        argvalues=[
            ServiceWithAsyncContextManagerAndNoDependencies,
            ServiceWithSyncContextManagerAndNoDependencies,
        ],
        ids=[
            "async_context_manager",
            "sync_context_manager",
        ],
    )
    async def test_resolve_and_dispose_transient_service_with_context_manager_and_no_dependencies(
        self, service_type: type[DisposeViewer]
    ) -> None:
        services = ServiceCollection()
        services.add_transient(service_type)

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_service(service_type)

            assert isinstance(resolved_service, service_type)
            assert resolved_service.is_disposed_initialized

        assert resolved_service.is_disposed

    async def test_resolve_and_dispose_transient_service_with_context_manager_and_dependencies(
        self,
    ) -> None:
        services = ServiceCollection()
        services.add_transient(ServiceWithAsyncContextManagerAndNoDependencies)
        services.add_transient(ServiceWithAsyncContextManagerAndDependencies)

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_service(
                ServiceWithAsyncContextManagerAndDependencies
            )

            assert isinstance(
                resolved_service, ServiceWithAsyncContextManagerAndDependencies
            )
            assert not resolved_service.is_disposed
            assert isinstance(
                resolved_service.service_with_async_context_manager_and_no_dependencies,
                ServiceWithAsyncContextManagerAndNoDependencies,
            )
            assert not resolved_service.service_with_async_context_manager_and_no_dependencies.is_disposed

        assert resolved_service.is_disposed
        assert resolved_service.service_with_async_context_manager_and_no_dependencies.is_disposed

    async def test_fail_when_resolve_circular_dependency(self) -> None:
        expected_error_message = "A circular dependency was detected for the service of type 'tests.utils.services.SelfCircularDependencyService'"
        services = ServiceCollection()
        services.add_transient(SelfCircularDependencyService)

        async with services.build_service_provider() as service_provider:
            with pytest.raises(RuntimeError, match=expected_error_message):
                await service_provider.get_required_service(
                    SelfCircularDependencyService
                )

    async def test_resolve_same_transient_service_several_times(self) -> None:
        services = ServiceCollection()
        services.add_transient(ServiceWithNoDependencies)

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_service(
                ServiceWithNoDependencies
            )
            assert isinstance(resolved_service, ServiceWithNoDependencies)

            await service_provider.get_required_service(ServiceWithNoDependencies)
            assert isinstance(resolved_service, ServiceWithNoDependencies)

    async def test_get_service_returns_none_when_the_required_service_is_not_provided(
        self,
    ) -> None:
        services = ServiceCollection()

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_service(
                ServiceWithNoDependencies
            )

            assert resolved_service is None

    async def test_get_service_provider(self) -> None:
        services = ServiceCollection()

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_service(
                BaseServiceProvider
            )

            assert isinstance(resolved_service, BaseServiceProvider)

    async def test_resolve_implementation_factory_with_service_injected(self) -> None:
        class Service1:
            pass

        class Service2:
            pass

        def implementation_factory(
            service_1: Service1,
        ) -> Service2:
            assert isinstance(service_1, Service1)
            return Service2()

        services = ServiceCollection()
        services.add_transient(Service2, implementation_factory)
        services.add_transient(Service1)

        async with services.build_service_provider() as service_provider:
            resolved_service_1 = await service_provider.get_required_service(Service1)
            assert isinstance(resolved_service_1, Service1)

            resolved_service_2 = await service_provider.get_required_service(Service2)
            assert isinstance(resolved_service_2, Service2)

    @pytest.mark.parametrize(
        argnames=("is_async_implementation_factory", "is_async_context_manager"),
        argvalues=[
            (True, True),
            (True, False),
            (False, True),
            (False, False),
        ],
    )
    async def test_context_manager_is_called_with_implementation_factory(  # noqa: C901
        self, is_async_implementation_factory: bool, is_async_context_manager: bool
    ) -> None:
        class AsyncService1(
            DisposeViewer, AbstractAsyncContextManager["AsyncService1"]
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

        class AsyncService2(
            DisposeViewer, AbstractAsyncContextManager["AsyncService2"]
        ):
            def __init__(self, service_1: AsyncService1) -> None:
                super().__init__()
                self.service_1 = service_1

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

        async def async_inject_async_service_2(
            service_1: AsyncService1,
        ) -> AsyncService2:
            assert isinstance(
                service_1,
                AsyncService1,
            )
            assert service_1.is_disposed_initialized
            return AsyncService2(service_1)

        def sync_inject_async_service_2(
            service_1: AsyncService1,
        ) -> AsyncService2:
            assert isinstance(
                service_1,
                AsyncService1,
            )
            assert service_1.is_disposed_initialized
            return AsyncService2(service_1)

        class SyncService1(DisposeViewer, AbstractContextManager["SyncService1"]):
            @override
            def __enter__(self) -> Self:
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

        class SyncService2(DisposeViewer, AbstractContextManager["SyncService2"]):
            def __init__(self, service_1: SyncService1) -> None:
                super().__init__()
                self.service_1 = service_1

            @override
            def __enter__(self) -> Self:
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

        async def async_inject_sync_service_2(
            service_1: SyncService1,
        ) -> SyncService2:
            assert isinstance(
                service_1,
                SyncService1,
            )
            assert service_1.is_disposed_initialized
            return SyncService2(service_1)

        def sync_inject_sync_service_2(
            service_1: SyncService1,
        ) -> SyncService2:
            assert isinstance(
                service_1,
                SyncService1,
            )
            assert service_1.is_disposed_initialized
            return SyncService2(service_1)

        services = ServiceCollection()
        services.add_transient(
            AsyncService1 if is_async_context_manager else SyncService1
        )

        if is_async_implementation_factory:
            if is_async_context_manager:
                services.add_transient(AsyncService2, async_inject_async_service_2)
            else:
                services.add_transient(SyncService2, async_inject_sync_service_2)
        elif is_async_context_manager:
            services.add_transient(AsyncService2, sync_inject_async_service_2)
        else:
            services.add_transient(SyncService2, sync_inject_sync_service_2)

        async with services.build_service_provider() as service_provider:
            resolved_service_2 = await service_provider.get_required_service(
                AsyncService2 if is_async_context_manager else SyncService2
            )

            assert isinstance(
                resolved_service_2,
                AsyncService2 if is_async_context_manager else SyncService2,
            )
            assert isinstance(
                resolved_service_2.service_1,
                AsyncService1 if is_async_context_manager else SyncService1,
            )
            assert resolved_service_2.service_1.is_disposed_initialized
            assert resolved_service_2.is_disposed_initialized

        assert resolved_service_2.service_1.is_disposed
        assert resolved_service_2.is_disposed
