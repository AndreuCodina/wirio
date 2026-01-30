import asyncio
from abc import ABC
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from dataclasses import dataclass
from types import TracebackType
from typing import Annotated, Self, final, override

import pytest

from tests.utils.services import (
    DisposeViewer,
    SelfCircularDependencyService,
    ServiceWithAsyncContextManagerAndDependencies,
    ServiceWithAsyncContextManagerAndNoDependencies,
    ServiceWithDependencies,
    ServiceWithGeneric,
    ServiceWithNoDependencies,
    ServiceWithOptionalDependency,
    ServiceWithOptionalDependencyWithDefault,
    ServiceWithSyncContextManagerAndNoDependencies,
)
from wirio._service_lookup._typed_type import TypedType
from wirio.abstractions.keyed_service import KeyedService
from wirio.abstractions.service_provider_is_keyed_service import (
    ServiceProviderIsKeyedService,
)
from wirio.abstractions.service_provider_is_service import (
    ServiceProviderIsService,
)
from wirio.annotations import FromKeyedServices, ServiceKey
from wirio.base_service_provider import BaseServiceProvider
from wirio.exceptions import (
    CannotResolveParameterServiceFromImplementationFactoryError,
    CannotResolveServiceError,
    CircularDependencyError,
    InvalidServiceKeyTypeError,
    KeyedServiceAnyKeyUsedToResolveServiceError,
    NoKeyedServiceRegisteredError,
    NoKeyedSingletonServiceRegisteredError,
    NoServiceRegisteredError,
    NoSingletonServiceRegisteredError,
)
from wirio.service_collection import ServiceCollection
from wirio.service_lifetime import ServiceLifetime


@final
class _CounterService(AbstractContextManager["_CounterService"]):
    @override
    def __enter__(self) -> Self:
        return self

    @override
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        return None


async def _inject_counter_service() -> _CounterService:
    await asyncio.sleep(0.01)
    return _CounterService()


class TestServiceProvider:
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
            resolved_service = await service_scope.get_required_service(
                ServiceWithNoDependencies
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
    async def test_resolve_keyed_service_with_implementation_factory(
        self,
        service_lifetime: ServiceLifetime,
        is_async_implementation_factory: bool,
    ) -> None:
        class KeyedServiceClas:
            def __init__(self, the_service_key: str) -> None:
                self.the_service_key = the_service_key

        async def async_implementation_factory(
            the_key: str | None,
            _: BaseServiceProvider,
        ) -> KeyedServiceClas:
            assert the_key is not None
            return KeyedServiceClas(the_service_key=the_key)

        def sync_implementation_factory(
            the_key: str | None,
            _: BaseServiceProvider,
        ) -> KeyedServiceClas:
            assert the_key is not None
            return KeyedServiceClas(the_service_key=the_key)

        service_key = "test_key"
        services = ServiceCollection()

        implementation_factory = (
            async_implementation_factory
            if is_async_implementation_factory
            else sync_implementation_factory
        )

        match service_lifetime:
            case ServiceLifetime.SINGLETON:
                services.add_keyed_singleton(
                    service_key, KeyedServiceClas, implementation_factory
                )
            case ServiceLifetime.SCOPED:
                services.add_keyed_scoped(
                    service_key, KeyedServiceClas, implementation_factory
                )
            case ServiceLifetime.TRANSIENT:
                services.add_keyed_transient(
                    service_key, KeyedServiceClas, implementation_factory
                )

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_keyed_service(
                service_key, KeyedServiceClas
            )

            assert isinstance(resolved_service, KeyedServiceClas)
            assert resolved_service.the_service_key == service_key

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

    async def test_fail_when_resolving_circular_dependency(self) -> None:
        services = ServiceCollection()
        services.add_transient(SelfCircularDependencyService)

        async with services.build_service_provider() as service_provider:
            with pytest.raises(CircularDependencyError):
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

    async def test_get_service_with_built_in_base_service_provider(self) -> None:
        services = ServiceCollection()
        services.add_transient(ServiceWithNoDependencies)

        async with services.build_service_provider() as service_provider:
            resolved_base_service_provider = (
                await service_provider.get_required_service(BaseServiceProvider)
            )

            assert isinstance(resolved_base_service_provider, BaseServiceProvider)

            resolved_service = (
                await resolved_base_service_provider.get_required_service(
                    ServiceWithNoDependencies
                )
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
            with pytest.raises(
                CannotResolveParameterServiceFromImplementationFactoryError
            ):
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

    @pytest.mark.parametrize(
        argnames=("service_lifetime"),
        argvalues=[
            ServiceLifetime.SINGLETON,
            ServiceLifetime.SCOPED,
            ServiceLifetime.TRANSIENT,
        ],
    )
    async def test_fail_when_registering_implementation_instance_which_is_not_subclass_of_service_type(
        self, service_lifetime: ServiceLifetime
    ) -> None:
        class Parent:
            pass

        class NotChild:
            pass

        services = ServiceCollection()

        expected_error_message = f"{NotChild} is not subclass of {Parent}"

        with pytest.raises(TypeError) as exception_info:  # noqa: PT012
            match service_lifetime:
                case ServiceLifetime.SINGLETON:
                    services.add_singleton(Parent, NotChild)
                case ServiceLifetime.SCOPED:
                    services.add_scoped(Parent, NotChild)
                case ServiceLifetime.TRANSIENT:
                    services.add_transient(Parent, NotChild)

        assert str(exception_info.value) == expected_error_message

        expected_error_message = f"{Parent} is not subclass of {Parent}"

        with pytest.raises(TypeError) as exception_info:  # noqa: PT012
            match service_lifetime:
                case ServiceLifetime.SINGLETON:
                    services.add_singleton(Parent, Parent)
                case ServiceLifetime.SCOPED:
                    services.add_scoped(Parent, Parent)
                case ServiceLifetime.TRANSIENT:
                    services.add_transient(Parent, Parent)

        assert str(exception_info.value) == expected_error_message

    @pytest.mark.parametrize(
        argnames=("service_lifetime"),
        argvalues=[
            ServiceLifetime.SINGLETON,
            ServiceLifetime.SCOPED,
            ServiceLifetime.TRANSIENT,
        ],
    )
    async def test_assign_default_values_to_constructor_parameters_when_services_are_not_registered(
        self, service_lifetime: ServiceLifetime
    ) -> None:
        class ServiceWithDefaultValues:
            def __init__(
                self,
                value1: str | None = None,
                value2: str = "default2",
                value3: str = "default3",
            ) -> None:
                self.value1 = value1
                self.value2 = value2
                self.value3 = value3

        services = ServiceCollection()

        match service_lifetime:
            case ServiceLifetime.SINGLETON:
                services.add_singleton(ServiceWithDefaultValues)
            case ServiceLifetime.SCOPED:
                services.add_scoped(ServiceWithDefaultValues)
            case ServiceLifetime.TRANSIENT:
                services.add_transient(ServiceWithDefaultValues)

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_service(
                ServiceWithDefaultValues
            )

            assert isinstance(resolved_service, ServiceWithDefaultValues)
            assert resolved_service.value1 is None
            assert resolved_service.value2 == "default2"
            assert resolved_service.value3 == "default3"

    @pytest.mark.parametrize(
        argnames="is_async_implementation_factory",
        argvalues=[
            True,
            False,
        ],
    )
    async def test_resolve_service_with_optional_implementation_factory_parameter(
        self, is_async_implementation_factory: bool
    ) -> None:
        async def async_implementation_factory(
            optional_dependency: ServiceWithNoDependencies | None,
        ) -> ServiceWithOptionalDependency:
            return ServiceWithOptionalDependency(optional_dependency)

        def sync_implementation_factory(
            optional_dependency: ServiceWithNoDependencies | None,
        ) -> ServiceWithOptionalDependency:
            return ServiceWithOptionalDependency(optional_dependency)

        services = ServiceCollection()
        services.add_transient(
            ServiceWithOptionalDependency,
            async_implementation_factory
            if is_async_implementation_factory
            else sync_implementation_factory,
        )

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_service(
                ServiceWithOptionalDependency
            )

        assert resolved_service.optional_dependency is None

    @pytest.mark.parametrize(
        argnames="is_async_implementation_factory",
        argvalues=[
            True,
            False,
        ],
    )
    async def test_resolve_service_with_optional_implementation_and_default_value_factory_parameter(
        self, is_async_implementation_factory: bool
    ) -> None:
        async def async_implementation_factory(
            optional_dependency: ServiceWithNoDependencies | None = None,
        ) -> ServiceWithOptionalDependency:
            return ServiceWithOptionalDependency(optional_dependency)

        def sync_implementation_factory(
            optional_dependency: ServiceWithNoDependencies | None = None,
        ) -> ServiceWithOptionalDependency:
            return ServiceWithOptionalDependency(optional_dependency)

        services = ServiceCollection()
        services.add_transient(
            ServiceWithOptionalDependency,
            async_implementation_factory
            if is_async_implementation_factory
            else sync_implementation_factory,
        )

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_service(
                ServiceWithOptionalDependency
            )

        assert resolved_service.optional_dependency is None

    async def test_resolve_service_with_optional_dependency_not_registered(
        self,
    ) -> None:
        services = ServiceCollection()
        services.add_transient(ServiceWithOptionalDependency)

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_service(
                ServiceWithOptionalDependency
            )

        assert resolved_service.optional_dependency is None

    async def test_resolve_service_with_optional_dependency_and_default_not_registered(
        self,
    ) -> None:
        services = ServiceCollection()
        services.add_transient(ServiceWithOptionalDependencyWithDefault)

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_service(
                ServiceWithOptionalDependencyWithDefault
            )

        assert (
            resolved_service.optional_dependency
            is ServiceWithOptionalDependencyWithDefault.DEFAULT_DEPENDENCY
        )

    async def test_fail_when_resolving_non_optional_service_parameter(
        self,
    ) -> None:
        class Service:
            def __init__(self, service: str) -> None:
                self.service = service

        services = ServiceCollection()
        services.add_transient(Service)

        async with services.build_service_provider() as service_provider:
            with pytest.raises(CannotResolveServiceError):
                await service_provider.get_required_service(Service)

    async def test_register_implementation_instance(
        self,
    ) -> None:
        services = ServiceCollection()
        implementation_instance = ServiceWithNoDependencies()
        services.add_singleton(ServiceWithNoDependencies, implementation_instance)

        async with services.build_service_provider() as service_provider:
            resolved_service_1 = await service_provider.get_required_service(
                ServiceWithNoDependencies
            )
            resolved_service_2 = await service_provider.get_required_service(
                ServiceWithNoDependencies
            )

            assert resolved_service_1 is implementation_instance
            assert resolved_service_2 is implementation_instance

    @pytest.mark.parametrize(
        argnames=("service_lifetime"),
        argvalues=[
            ServiceLifetime.SINGLETON,
            ServiceLifetime.SCOPED,
            ServiceLifetime.TRANSIENT,
        ],
    )
    async def test_resolve_keyed_service(
        self, service_lifetime: ServiceLifetime
    ) -> None:
        key = "key"
        services = ServiceCollection()

        match service_lifetime:
            case ServiceLifetime.SINGLETON:
                services.add_keyed_singleton(key, ServiceWithNoDependencies)
            case ServiceLifetime.SCOPED:
                services.add_keyed_scoped(key, ServiceWithNoDependencies)
            case ServiceLifetime.TRANSIENT:
                services.add_keyed_transient(key, ServiceWithNoDependencies)

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_keyed_service(
                key, ServiceWithNoDependencies
            )

            assert isinstance(resolved_service, ServiceWithNoDependencies)

    async def test_fail_when_the_required_keyed_service_with_a_key_is_not_provided(
        self,
    ) -> None:
        key = "key"
        services = ServiceCollection()

        async with services.build_service_provider() as service_provider:
            with pytest.raises(NoKeyedServiceRegisteredError):
                await service_provider.get_required_keyed_service(
                    key, ServiceWithNoDependencies
                )

    async def test_fail_when_the_required_keyed_service_without_a_key_is_not_provided(
        self,
    ) -> None:
        services = ServiceCollection()

        async with services.build_service_provider() as service_provider:
            with pytest.raises(NoServiceRegisteredError):
                await service_provider.get_required_keyed_service(
                    None, ServiceWithNoDependencies
                )

    async def test_fail_when_resolving_non_keyed_service_with_a_key(
        self,
    ) -> None:
        key = "key"
        services = ServiceCollection()
        services.add_transient(ServiceWithNoDependencies)

        async with services.build_service_provider() as service_provider:
            with pytest.raises(NoKeyedServiceRegisteredError):
                await service_provider.get_required_keyed_service(
                    key, ServiceWithNoDependencies
                )

    async def test_resolve_non_keyed_service_without_a_key(
        self,
    ) -> None:
        services = ServiceCollection()
        services.add_transient(ServiceWithNoDependencies)

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_keyed_service(
                None, ServiceWithNoDependencies
            )

            assert isinstance(resolved_service, ServiceWithNoDependencies)

    async def test_get_service_key_using_service_key_annotation(
        self,
    ) -> None:
        expected_service_key = 1

        class ServiceWithServiceKey:
            def __init__(self, service_key: Annotated[int, ServiceKey()]) -> None:
                self.service_key = service_key

        services = ServiceCollection()
        services.add_keyed_transient(expected_service_key, ServiceWithServiceKey)

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_keyed_service(
                expected_service_key, ServiceWithServiceKey
            )

            assert isinstance(resolved_service, ServiceWithServiceKey)
            assert resolved_service.service_key == expected_service_key

    async def test_get_service_key_registered_with_any_key_using_service_key_annotation(
        self,
    ) -> None:
        expected_service_key = 1

        class ServiceWithServiceKey:
            def __init__(self, service_key: Annotated[int, ServiceKey()]) -> None:
                self.service_key = service_key

        services = ServiceCollection()
        services.add_keyed_transient(KeyedService.ANY_KEY, ServiceWithServiceKey)

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_keyed_service(
                expected_service_key, ServiceWithServiceKey
            )

            assert isinstance(resolved_service, ServiceWithServiceKey)
            assert resolved_service.service_key == expected_service_key

    async def test_fail_when_service_key_annotation_type_mismatches_service_key_type(
        self,
    ) -> None:
        class ServiceWithServiceKey:
            def __init__(self, service_key: Annotated[str, ServiceKey()]) -> None:
                self.service_key = service_key

        services = ServiceCollection()
        services.add_keyed_transient(1, ServiceWithServiceKey)

        async with services.build_service_provider() as service_provider:
            with pytest.raises(InvalidServiceKeyTypeError):
                await service_provider.get_required_keyed_service(
                    1, ServiceWithServiceKey
                )

    async def test_resolve_keyed_service_using_from_keyed_services_annotation(
        self,
    ) -> None:
        service_key = "key"

        class ServiceWithKeyedDependency:
            def __init__(
                self,
                dependency: Annotated[
                    ServiceWithNoDependencies, FromKeyedServices(service_key)
                ],
            ) -> None:
                self.dependency = dependency

        services = ServiceCollection()
        services.add_keyed_transient(service_key, ServiceWithNoDependencies)
        services.add_transient(ServiceWithKeyedDependency)

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_service(
                ServiceWithKeyedDependency
            )

            assert isinstance(resolved_service, ServiceWithKeyedDependency)
            assert isinstance(resolved_service.dependency, ServiceWithNoDependencies)

    async def test_resolve_keyed_service_without_a_key_using_from_keyed_services_annotation_with_none(
        self,
    ) -> None:
        class ServiceWithKeyedDependency:
            def __init__(
                self,
                dependency: Annotated[
                    ServiceWithNoDependencies, FromKeyedServices(None)
                ],
            ) -> None:
                self.dependency = dependency

        services = ServiceCollection()
        services.add_transient(ServiceWithNoDependencies)
        services.add_transient(ServiceWithKeyedDependency)

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_service(
                ServiceWithKeyedDependency
            )

            assert isinstance(resolved_service, ServiceWithKeyedDependency)
            assert isinstance(resolved_service.dependency, ServiceWithNoDependencies)

    async def test_resolve_keyed_service_inheriting_key_using_from_keyed_services_annotation(
        self,
    ) -> None:
        service_key = "key"

        class ServiceWithKeyedDependency:
            def __init__(
                self,
                dependency: Annotated[ServiceWithNoDependencies, FromKeyedServices()],
            ) -> None:
                self.dependency = dependency

        services = ServiceCollection()
        services.add_keyed_transient(service_key, ServiceWithNoDependencies)
        services.add_keyed_transient(service_key, ServiceWithKeyedDependency)

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_keyed_service(
                service_key, ServiceWithKeyedDependency
            )

            assert isinstance(resolved_service, ServiceWithKeyedDependency)
            assert isinstance(resolved_service.dependency, ServiceWithNoDependencies)

    async def test_resolve_service_registered_with_any_key(self) -> None:
        key = KeyedService.ANY_KEY
        another_key = "another_key"

        services = ServiceCollection()
        services.add_keyed_transient(key, ServiceWithNoDependencies)

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_keyed_service(
                another_key, ServiceWithNoDependencies
            )

            assert isinstance(resolved_service, ServiceWithNoDependencies)

    async def test_fail_when_resolving_a_single_service_with_any_key_as_lookup_key(
        self,
    ) -> None:
        key = KeyedService.ANY_KEY

        services = ServiceCollection()
        services.add_keyed_transient(key, ServiceWithNoDependencies)

        async with services.build_service_provider() as service_provider:
            with pytest.raises(KeyedServiceAnyKeyUsedToResolveServiceError):
                await service_provider.get_required_keyed_service(
                    key, ServiceWithNoDependencies
                )

            with pytest.raises(KeyedServiceAnyKeyUsedToResolveServiceError):
                await service_provider.get_required_keyed_service(
                    key, ServiceWithNoDependencies
                )

    async def test_register_a_service_for_any_key_using_from_keyed_services_annotation(
        self,
    ) -> None:
        key = KeyedService.ANY_KEY
        another_key = "another_key"

        class ServiceWithKeyedDependency:
            def __init__(
                self,
                dependency: Annotated[
                    ServiceWithNoDependencies, FromKeyedServices(another_key)
                ],
            ) -> None:
                self.dependency = dependency

        services = ServiceCollection()
        services.add_transient(ServiceWithKeyedDependency)
        services.add_keyed_transient(key, ServiceWithNoDependencies)

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_service(
                ServiceWithKeyedDependency
            )

            assert isinstance(resolved_service, ServiceWithKeyedDependency)
            assert isinstance(resolved_service.dependency, ServiceWithNoDependencies)

    async def test_resolve_latest_registered_service(
        self,
    ) -> None:
        expected_field = "Yes"

        @dataclass(frozen=True)
        class Service1:
            field: str

        def implementation_factory_1() -> Service1:
            return Service1(field="No")

        def implementation_factory_2() -> Service1:
            return Service1(field=expected_field)

        services = ServiceCollection()
        services.add_transient(implementation_factory_1)
        services.add_transient(implementation_factory_2)

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_service(Service1)

            assert isinstance(resolved_service, Service1)
            assert resolved_service.field == expected_field

    async def test_resolve_keyed_service_and_dependency_using_implementation_factory_using_from_keyed_services_annotation(
        self,
    ) -> None:
        class ApplicationSettings:
            pass

        @dataclass(frozen=True)
        class Service:
            key: str
            application_settings: ApplicationSettings

        def inject_service(
            service_key: str | None, application_settings: ApplicationSettings
        ) -> Service:
            assert service_key is not None
            return Service(key=service_key, application_settings=application_settings)

        key = "key"
        services = ServiceCollection()
        services.add_transient(ApplicationSettings)
        services.add_keyed_transient(key, inject_service)

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_keyed_service(
                key, Service
            )

            assert isinstance(resolved_service, Service)
            assert resolved_service.key == key
            assert isinstance(
                resolved_service.application_settings,
                ApplicationSettings,
            )

    async def test_resolve_service_registered_as_a_key_without_a_key_using_implementation_factory(
        self,
    ) -> None:
        @dataclass(frozen=True)
        class KeyedService1:
            service_key: int | None

        @dataclass(frozen=True)
        class KeyedService2:
            service_key: int | None

        services = ServiceCollection()

        def inject_service_1(key: int | None) -> KeyedService1:
            return KeyedService1(service_key=key)

        def inject_service_2(key: int | None) -> KeyedService2:
            return KeyedService2(service_key=key)

        services.add_keyed_transient(None, inject_service_1)
        services.add_keyed_transient(None, KeyedService2, inject_service_2)

        async with services.build_service_provider() as service_provider:
            resolved_service_1 = await service_provider.get_required_service(
                KeyedService1
            )

            assert isinstance(resolved_service_1, KeyedService1)
            assert resolved_service_1.service_key is None

            resolved_service_2 = await service_provider.get_required_service(
                KeyedService2
            )

            assert isinstance(resolved_service_2, KeyedService2)
            assert resolved_service_2.service_key is None

    async def test_resolve_service_using_none_as_key_when_registered_keyed_service_with_none_key(
        self,
    ) -> None:
        @dataclass(frozen=True)
        class KeyedServiceClass:
            service_key: object | None

        services = ServiceCollection()

        def inject_service(key: object | None) -> KeyedServiceClass:
            return KeyedServiceClass(service_key=key)

        services.add_keyed_transient(None, inject_service)

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_keyed_service(
                None, KeyedServiceClass
            )

            assert isinstance(resolved_service, KeyedServiceClass)
            assert resolved_service.service_key is None

    async def test_resolve_a_service_using_none_as_key_but_not_registered_as_a_keyed_service(
        self,
    ) -> None:
        services = ServiceCollection()
        services.add_transient(ServiceWithNoDependencies)

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_keyed_service(
                None, ServiceWithNoDependencies
            )

            assert isinstance(resolved_service, ServiceWithNoDependencies)

    async def test_send_requested_key_to_implementation_factory_when_service_is_registered_with_any_key(
        self,
    ) -> None:
        @dataclass(frozen=True)
        class Service:
            key: str | None

        def inject_service(service_key: object | None) -> Service:
            assert isinstance(service_key, str | None)
            return Service(key=service_key)

        expected_service_key = "expected_key"
        service_key = KeyedService.ANY_KEY
        services = ServiceCollection()
        services.add_keyed_transient(service_key, inject_service)

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_keyed_service(
                expected_service_key, Service
            )

            assert isinstance(resolved_service, Service)
            assert resolved_service.key == expected_service_key

    async def test_resolve_keyed_service_of_implementation_factory_using_from_keyed_services_annotation(
        self,
    ) -> None:
        class ServiceDependency:
            pass

        @dataclass(frozen=True)
        class Service:
            service_dependency: ServiceDependency

        service_key = "key"

        def inject_service(
            application_settings: Annotated[
                ServiceDependency, FromKeyedServices(service_key)
            ],
        ) -> Service:
            return Service(service_dependency=application_settings)

        services = ServiceCollection()
        services.add_keyed_transient(service_key, ServiceDependency)
        services.add_transient(inject_service)

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_service(Service)

            assert isinstance(resolved_service, Service)
            assert isinstance(
                resolved_service.service_dependency,
                ServiceDependency,
            )

    async def test_fail_when_service_key_annotation_can_not_be_used_when_parent_service_is_not_a_keyed_service(
        self,
    ) -> None:
        class ServiceWithServiceKey:
            def __init__(self, service_key: Annotated[int, ServiceKey()]) -> None:
                self.service_key = service_key

        services = ServiceCollection()
        services.add_transient(ServiceWithServiceKey)

        async with services.build_service_provider() as service_provider:
            with pytest.raises(CannotResolveServiceError):
                await service_provider.get_required_service(ServiceWithServiceKey)

    async def test_check_if_service_is_registered(self) -> None:
        class RegisteredService:
            pass

        class UnregisteredService:
            pass

        services = ServiceCollection()
        services.add_transient(RegisteredService)

        async with services.build_service_provider() as service_provider:
            service_provider_is_service = await service_provider.get_required_service(
                ServiceProviderIsService
            )
            service_provider_is_keyed_service = (
                await service_provider.get_required_service(
                    ServiceProviderIsKeyedService
                )
            )

            is_registered = service_provider_is_service.is_service(RegisteredService)
            assert is_registered is True
            is_registered = service_provider_is_keyed_service.is_service(
                RegisteredService
            )
            assert is_registered is True

            is_registered = service_provider_is_service.is_service(UnregisteredService)
            assert not is_registered
            is_registered = service_provider_is_keyed_service.is_service(
                UnregisteredService
            )
            assert not is_registered

    async def test_check_if_keyed_service_is_registered(self) -> None:
        class RegisteredService:
            pass

        class UnregisteredService:
            pass

        service_key = "key"
        services = ServiceCollection()
        services.add_keyed_transient(service_key, RegisteredService)

        async with services.build_service_provider() as service_provider:
            service_provider_is_keyed_service = (
                await service_provider.get_required_service(
                    ServiceProviderIsKeyedService
                )
            )

            is_registered = service_provider_is_keyed_service.is_keyed_service(
                service_key, RegisteredService
            )

            assert is_registered is True

            is_registered = service_provider_is_keyed_service.is_keyed_service(
                service_key, UnregisteredService
            )

            assert not is_registered

    async def test_return_same_singleton_instance_when_resolving_a_singleton(
        self,
    ) -> None:
        services = ServiceCollection()
        services.add_singleton(_inject_counter_service)

        async with services.build_service_provider() as service_provider:
            resolved_services = await asyncio.gather(
                service_provider.get_required_service(_CounterService),
                service_provider.get_required_service(_CounterService),
                service_provider.get_required_service(_CounterService),
                service_provider.get_required_service(_CounterService),
                service_provider.get_required_service(_CounterService),
            )

            unique_instances = set(resolved_services)
            assert len(unique_instances) == 1, (
                f"Expected 1 singleton instance, got {len(unique_instances)}"
            )

    async def test_return_same_singleton_instance_when_resolving_a_singleton_using_a_scope(
        self,
    ) -> None:
        services = ServiceCollection()
        services.add_scoped(_inject_counter_service)

        async with services.build_service_provider() as service_provider:
            async with service_provider.create_scope() as service_scope:
                resolved_services = await asyncio.gather(
                    service_scope.get_required_service(_CounterService),
                    service_scope.get_required_service(_CounterService),
                    service_scope.get_required_service(_CounterService),
                    service_scope.get_required_service(_CounterService),
                    service_scope.get_required_service(_CounterService),
                )

            unique_instances = set(resolved_services)
            assert len(unique_instances) == 1, (
                f"Expected 1 scoped instance within same scope, got {len(unique_instances)}"
            )

    async def test_return_different_scoped_instance_when_resolving_a_scoped_service_in_different_scopes(
        self,
    ) -> None:
        services = ServiceCollection()
        services.add_scoped(_inject_counter_service)

        async with services.build_service_provider() as service_provider:
            async with service_provider.create_scope() as service_scope_1:
                resolved_service_1 = await service_scope_1.get_required_service(
                    _CounterService
                )

            async with service_provider.create_scope() as service_scope_2:
                resolved_service_2 = await service_scope_2.get_required_service(
                    _CounterService
                )

            assert resolved_service_1 is not resolved_service_2

    async def test_return_same_singleton_instance_when_resolving_a_singleton_in_different_scopes(
        self,
    ) -> None:
        services = ServiceCollection()
        services.add_singleton(_inject_counter_service)

        async with services.build_service_provider() as service_provider:
            async with service_provider.create_scope() as service_scope_1:
                resolved_service_1 = await service_scope_1.get_required_service(
                    _CounterService
                )

            async with service_provider.create_scope() as service_scope_2:
                resolved_service_2 = await service_scope_2.get_required_service(
                    _CounterService
                )

            assert resolved_service_1 is resolved_service_2

    async def test_return_different_scoped_instances_when_resolving_a_scoped_service_in_different_scopes(
        self,
    ) -> None:
        services = ServiceCollection()
        services.add_scoped(_inject_counter_service)

        async with services.build_service_provider() as service_provider:
            async with service_provider.create_scope() as service_scope_1:
                resolved_service_1 = await service_scope_1.get_required_service(
                    _CounterService
                )

            async with service_provider.create_scope() as service_scope_2:
                resolved_service_2 = await service_scope_2.get_required_service(
                    _CounterService
                )

            assert resolved_service_1 is not resolved_service_2

    @pytest.mark.parametrize(
        argnames=("is_keyed_service"),
        argvalues=[
            True,
            False,
        ],
    )
    async def test_enable_auto_activation_of_registered_singleton_service(
        self, is_keyed_service: bool
    ) -> None:
        expected_instances = 1
        created_instances: list[object] = []
        service_key = "key"

        class Service:
            def __init__(self) -> None:
                created_instances.append(self)

        services = ServiceCollection()

        if is_keyed_service:
            services.add_keyed_singleton(service_key, Service)
            services.enable_keyed_singleton_auto_activation(service_key, Service)
        else:
            services.add_singleton(Service)
            services.enable_singleton_auto_activation(Service)

        async with services.build_service_provider() as service_provider:
            assert len(created_instances) == expected_instances

            if is_keyed_service:
                resolved_service = await service_provider.get_required_keyed_service(
                    service_key, Service
                )
            else:
                resolved_service = await service_provider.get_required_service(Service)

            assert len(created_instances) == expected_instances
            assert resolved_service is created_instances[0]

    @pytest.mark.parametrize(
        argnames=("is_keyed_service", "exception_type"),
        argvalues=[
            (True, NoKeyedSingletonServiceRegisteredError),
            (False, NoSingletonServiceRegisteredError),
        ],
    )
    async def test_fail_when_enabling_auto_activation_of_unregistered_singleton_service(
        self, is_keyed_service: bool, exception_type: type[BaseException]
    ) -> None:
        services = ServiceCollection()

        with pytest.raises(exception_type):  # noqa: PT012
            if is_keyed_service:
                services.enable_keyed_singleton_auto_activation(
                    "key", ServiceWithNoDependencies
                )
            else:
                services.enable_singleton_auto_activation(ServiceWithNoDependencies)
