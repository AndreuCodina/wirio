from abc import ABC
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from typing import TYPE_CHECKING, Self, override

import pytest

from aspy_dependency_injection._service_lookup._typed_type import TypedType
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
    ServiceWithGeneric,
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
        argnames=("service_lifetime", "is_async_implementation_factory"),
        argvalues=[
            (ServiceLifetime.SINGLETON, True),
            (ServiceLifetime.SINGLETON, False),
            (ServiceLifetime.SCOPED, True),
            (ServiceLifetime.SCOPED, False),
            (ServiceLifetime.TRANSIENT, True),
            (ServiceLifetime.TRANSIENT, False),
        ],
    )
    async def test_resolve_service_with_implementation_factory(
        self, service_lifetime: ServiceLifetime, is_async_implementation_factory: bool
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

        match service_lifetime:
            case ServiceLifetime.SINGLETON:
                services.add_singleton(
                    ServiceWithNoDependencies, implementation_factory
                )
            case ServiceLifetime.SCOPED:
                services.add_scoped(ServiceWithNoDependencies, implementation_factory)
            case ServiceLifetime.TRANSIENT:
                services.add_transient(
                    ServiceWithNoDependencies, implementation_factory
                )

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
    )
    async def test_resolve_service_with_dependencies(
        self, service_lifetime: ServiceLifetime
    ) -> None:
        services = ServiceCollection()

        match service_lifetime:
            case ServiceLifetime.SINGLETON:
                services.add_singleton(ServiceWithNoDependencies)
                services.add_singleton(ServiceWithDependencies)
            case ServiceLifetime.SCOPED:
                services.add_scoped(ServiceWithNoDependencies)
                services.add_scoped(ServiceWithDependencies)
            case ServiceLifetime.TRANSIENT:
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
        argnames=("service_lifetime", "service_type"),
        argvalues=[
            (
                ServiceLifetime.SINGLETON,
                ServiceWithAsyncContextManagerAndNoDependencies,
            ),
            (ServiceLifetime.SINGLETON, ServiceWithSyncContextManagerAndNoDependencies),
            (
                ServiceLifetime.SCOPED,
                ServiceWithAsyncContextManagerAndNoDependencies,
            ),
            (ServiceLifetime.SCOPED, ServiceWithSyncContextManagerAndNoDependencies),
            (
                ServiceLifetime.TRANSIENT,
                ServiceWithAsyncContextManagerAndNoDependencies,
            ),
            (ServiceLifetime.TRANSIENT, ServiceWithSyncContextManagerAndNoDependencies),
        ],
    )
    async def test_resolve_and_dispose_service_with_context_manager_and_no_dependencies(
        self, service_lifetime: ServiceLifetime, service_type: type[DisposeViewer]
    ) -> None:
        services = ServiceCollection()

        match service_lifetime:
            case ServiceLifetime.SINGLETON:
                services.add_singleton(service_type)
            case ServiceLifetime.SCOPED:
                services.add_scoped(service_type)
            case ServiceLifetime.TRANSIENT:
                services.add_transient(service_type)

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_service(service_type)

            assert isinstance(resolved_service, service_type)
            assert resolved_service.is_disposed_initialized

        assert resolved_service.is_disposed

    @pytest.mark.parametrize(
        argnames=("service_lifetime"),
        argvalues=[
            ServiceLifetime.SINGLETON,
            ServiceLifetime.SCOPED,
            ServiceLifetime.TRANSIENT,
        ],
    )
    async def test_resolve_and_dispose_service_with_context_manager_and_dependencies(
        self, service_lifetime: ServiceLifetime
    ) -> None:
        services = ServiceCollection()

        match service_lifetime:
            case ServiceLifetime.SINGLETON:
                services.add_singleton(ServiceWithAsyncContextManagerAndNoDependencies)
                services.add_singleton(ServiceWithAsyncContextManagerAndDependencies)
            case ServiceLifetime.SCOPED:
                services.add_scoped(ServiceWithAsyncContextManagerAndNoDependencies)
                services.add_scoped(ServiceWithAsyncContextManagerAndDependencies)
            case ServiceLifetime.TRANSIENT:
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

    async def test_return_a_different_transient_instance_each_time_is_requested(
        self,
    ) -> None:
        services = ServiceCollection()
        services.add_transient(ServiceWithNoDependencies)

        async with services.build_service_provider() as service_provider:
            resolved_service_1 = await service_provider.get_required_service(
                ServiceWithNoDependencies
            )
            assert isinstance(resolved_service_1, ServiceWithNoDependencies)

            resolved_service_2 = await service_provider.get_required_service(
                ServiceWithNoDependencies
            )
            assert isinstance(resolved_service_2, ServiceWithNoDependencies)

            assert resolved_service_1 is not resolved_service_2

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

    @pytest.mark.parametrize(
        argnames=("service_lifetime"),
        argvalues=[
            ServiceLifetime.SINGLETON,
            ServiceLifetime.SCOPED,
            ServiceLifetime.TRANSIENT,
        ],
    )
    async def test_resolve_implementation_factory_with_explicit_service_type(
        self, service_lifetime: ServiceLifetime
    ) -> None:
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

        match service_lifetime:
            case ServiceLifetime.SINGLETON:
                services.add_singleton(Service2, implementation_factory)
                services.add_singleton(Service1)
            case ServiceLifetime.SCOPED:
                services.add_scoped(Service2, implementation_factory)
                services.add_scoped(Service1)
            case ServiceLifetime.TRANSIENT:
                services.add_transient(Service2, implementation_factory)
                services.add_transient(Service1)

        async with services.build_service_provider() as service_provider:
            resolved_service_1 = await service_provider.get_required_service(Service1)
            assert isinstance(resolved_service_1, Service1)

            resolved_service_2 = await service_provider.get_required_service(Service2)
            assert isinstance(resolved_service_2, Service2)

    @pytest.mark.parametrize(
        argnames=("service_lifetime"),
        argvalues=[
            ServiceLifetime.SINGLETON,
            ServiceLifetime.SCOPED,
            ServiceLifetime.TRANSIENT,
        ],
    )
    async def test_resolve_implementation_factory_with_explicit_service_type_being_a_base_class(
        self, service_lifetime: ServiceLifetime
    ) -> None:
        class BaseService(ABC):  # noqa: B024
            pass

        class Service(BaseService):
            pass

        def implementation_factory() -> Service:
            return Service()

        services = ServiceCollection()

        match service_lifetime:
            case ServiceLifetime.SINGLETON:
                services.add_singleton(Service, implementation_factory)
            case ServiceLifetime.SCOPED:
                services.add_scoped(Service, implementation_factory)
            case ServiceLifetime.TRANSIENT:
                services.add_transient(Service, implementation_factory)

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_service(Service)

            assert isinstance(resolved_service, BaseService)
            assert issubclass(type(resolved_service), BaseService)
            assert isinstance(resolved_service, Service)

    @pytest.mark.parametrize(
        argnames=(
            "service_lifetime",
            "is_async_implementation_factory",
            "is_async_context_manager",
        ),
        argvalues=[
            (ServiceLifetime.SINGLETON, True, True),
            (ServiceLifetime.SINGLETON, True, False),
            (ServiceLifetime.SINGLETON, False, True),
            (ServiceLifetime.SINGLETON, False, False),
            (ServiceLifetime.SCOPED, True, True),
            (ServiceLifetime.SCOPED, True, False),
            (ServiceLifetime.SCOPED, False, True),
            (ServiceLifetime.SCOPED, False, False),
            (ServiceLifetime.TRANSIENT, True, True),
            (ServiceLifetime.TRANSIENT, True, False),
            (ServiceLifetime.TRANSIENT, False, True),
            (ServiceLifetime.TRANSIENT, False, False),
        ],
    )
    async def test_call_context_manager_when_implementation_factory_is_provided(  # noqa: C901, PLR0912, PLR0915
        self,
        service_lifetime: ServiceLifetime,
        is_async_implementation_factory: bool,
        is_async_context_manager: bool,
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

        match service_lifetime:
            case ServiceLifetime.SINGLETON:
                services.add_singleton(
                    AsyncService1 if is_async_context_manager else SyncService1
                )
            case ServiceLifetime.SCOPED:
                services.add_scoped(
                    AsyncService1 if is_async_context_manager else SyncService1
                )
            case ServiceLifetime.TRANSIENT:
                services.add_transient(
                    AsyncService1 if is_async_context_manager else SyncService1
                )

        if is_async_implementation_factory:
            if is_async_context_manager:
                match service_lifetime:
                    case ServiceLifetime.SINGLETON:
                        services.add_singleton(
                            AsyncService2, async_inject_async_service_2
                        )
                    case ServiceLifetime.SCOPED:
                        services.add_scoped(AsyncService2, async_inject_async_service_2)
                    case ServiceLifetime.TRANSIENT:
                        services.add_transient(
                            AsyncService2, async_inject_async_service_2
                        )

            else:
                match service_lifetime:
                    case ServiceLifetime.SINGLETON:
                        services.add_singleton(
                            SyncService2, async_inject_sync_service_2
                        )
                    case ServiceLifetime.SCOPED:
                        services.add_scoped(SyncService2, async_inject_sync_service_2)
                    case ServiceLifetime.TRANSIENT:
                        services.add_transient(
                            SyncService2, async_inject_sync_service_2
                        )
        elif is_async_context_manager:
            match service_lifetime:
                case ServiceLifetime.SINGLETON:
                    services.add_singleton(AsyncService2, sync_inject_async_service_2)
                case ServiceLifetime.SCOPED:
                    services.add_scoped(AsyncService2, sync_inject_async_service_2)
                case ServiceLifetime.TRANSIENT:
                    services.add_transient(AsyncService2, sync_inject_async_service_2)
        else:
            match service_lifetime:
                case ServiceLifetime.SINGLETON:
                    services.add_singleton(SyncService2, sync_inject_sync_service_2)
                case ServiceLifetime.SCOPED:
                    services.add_scoped(SyncService2, sync_inject_sync_service_2)
                case ServiceLifetime.TRANSIENT:
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

    @pytest.mark.parametrize(
        argnames=("service_lifetime"),
        argvalues=[
            ServiceLifetime.SINGLETON,
            ServiceLifetime.SCOPED,
            ServiceLifetime.TRANSIENT,
        ],
    )
    async def test_fail_when_implementation_factory_requests_not_registered_service(
        self, service_lifetime: ServiceLifetime
    ) -> None:
        class Service1:
            pass

        class Service2:
            pass

        def implementation_factory(
            _: Service1,
        ) -> Service2:
            return Service2()

        services = ServiceCollection()

        match service_lifetime:
            case ServiceLifetime.SINGLETON:
                services.add_singleton(Service2, implementation_factory)
            case ServiceLifetime.SCOPED:
                services.add_scoped(Service2, implementation_factory)
            case ServiceLifetime.TRANSIENT:
                services.add_transient(Service2, implementation_factory)

        async with services.build_service_provider() as service_provider:
            with pytest.raises(RuntimeError):
                await service_provider.get_required_service(Service2)

    @pytest.mark.parametrize(
        argnames=("service_lifetime", "is_async_implementation_factory"),
        argvalues=[
            (ServiceLifetime.SINGLETON, True),
            (ServiceLifetime.SINGLETON, False),
            (ServiceLifetime.SCOPED, True),
            (ServiceLifetime.SCOPED, False),
            (ServiceLifetime.TRANSIENT, True),
            (ServiceLifetime.TRANSIENT, False),
        ],
    )
    async def test_infer_the_type_of_implementation_factory_when_service_type_is_not_provided(
        self, service_lifetime: ServiceLifetime, is_async_implementation_factory: bool
    ) -> None:
        async def async_implementation_factory(
            _: BaseServiceProvider,
        ) -> ServiceWithGeneric[str]:
            return ServiceWithGeneric[str]()

        def sync_implementation_factory(
            _: BaseServiceProvider,
        ) -> ServiceWithGeneric[str]:
            return ServiceWithGeneric[str]()

        expected_type = ServiceWithGeneric[str]

        implementation_factory = (
            async_implementation_factory
            if is_async_implementation_factory
            else sync_implementation_factory
        )

        services = ServiceCollection()

        match service_lifetime:
            case ServiceLifetime.SINGLETON:
                services.add_singleton(implementation_factory)
            case ServiceLifetime.SCOPED:
                services.add_scoped(implementation_factory)
            case ServiceLifetime.TRANSIENT:
                services.add_transient(implementation_factory)

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_service(
                expected_type
            )

            assert TypedType.from_instance(resolved_service) == TypedType.from_type(
                ServiceWithGeneric[str]
            )

    @pytest.mark.parametrize(
        argnames=("service_lifetime"),
        argvalues=[
            ServiceLifetime.SINGLETON,
            ServiceLifetime.SCOPED,
            ServiceLifetime.TRANSIENT,
        ],
    )
    def test_fail_when_register_service_with_implementation_factory_but_without_type_hints(
        self, service_lifetime: ServiceLifetime
    ) -> None:
        def implementation_factory(  # noqa: ANN202
            _: BaseServiceProvider,
        ):
            return 0

        expected_error_message = (
            "Missing return type hints from 'implementation_factory'"
        )
        services = ServiceCollection()

        with pytest.raises(ValueError, match=expected_error_message):  # noqa: PT012
            match service_lifetime:
                case ServiceLifetime.SINGLETON:
                    services.add_singleton(implementation_factory)
                case ServiceLifetime.SCOPED:
                    services.add_scoped(implementation_factory)
                case ServiceLifetime.TRANSIENT:
                    services.add_transient(implementation_factory)

        with pytest.raises(ValueError, match=expected_error_message):  # noqa: PT012
            match service_lifetime:
                case ServiceLifetime.SINGLETON:
                    services.add_singleton(lambda: 0)
                case ServiceLifetime.SCOPED:
                    services.add_scoped(lambda: 0)
                case ServiceLifetime.TRANSIENT:
                    services.add_transient(lambda: 0)

    @pytest.mark.parametrize(
        argnames=("service_lifetime"),
        argvalues=[
            ServiceLifetime.SINGLETON,
            ServiceLifetime.SCOPED,
            ServiceLifetime.TRANSIENT,
        ],
    )
    async def test_resolve_service_when_implementation_type_is_provided(
        self, service_lifetime: ServiceLifetime
    ) -> None:
        class Parent:
            pass

        class Child(Parent):
            pass

        services = ServiceCollection()

        match service_lifetime:
            case ServiceLifetime.SINGLETON:
                services.add_singleton(Parent, Child)
            case ServiceLifetime.SCOPED:
                services.add_scoped(Parent, Child)
            case ServiceLifetime.TRANSIENT:
                services.add_transient(Parent, Child)

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_service(Parent)

            assert isinstance(resolved_service, Parent)
            assert issubclass(type(resolved_service), Parent)
            assert isinstance(resolved_service, Child)
