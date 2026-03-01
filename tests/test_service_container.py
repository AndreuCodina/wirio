from collections.abc import Sequence

import pytest
from pytest_mock import MockerFixture

from tests.utils.services import ServiceWithDependencies, ServiceWithNoDependencies
from wirio.exceptions import ServiceContainerNotBuiltError
from wirio.service_container import ServiceContainer


class TestServiceContainer:
    async def test_initialize_service_provider_automatically(self) -> None:  # noqa: PLR0915
        services = ServiceContainer()
        services.add_transient(ServiceWithNoDependencies)
        assert services.service_provider is None

        try:
            await services.get(ServiceWithNoDependencies)
            assert services.service_provider is not None
            assert services.service_provider.is_fully_initialized
        finally:
            await services.aclose()

        services = ServiceContainer()
        services.add_transient(ServiceWithNoDependencies)
        assert services.service_provider is None

        try:
            await services.try_get(ServiceWithNoDependencies)
            assert services.service_provider is not None
            assert services.service_provider.is_fully_initialized
        finally:
            await services.aclose()

        service_key = "key"
        services = ServiceContainer()
        services.add_keyed_transient(service_key, ServiceWithNoDependencies)
        assert services.service_provider is None

        try:
            await services.get_keyed(service_key, ServiceWithNoDependencies)
            assert services.service_provider is not None
            assert services.service_provider.is_fully_initialized
        finally:
            await services.aclose()

        services = ServiceContainer()
        services.add_keyed_transient(service_key, ServiceWithNoDependencies)
        assert services.service_provider is None

        try:
            await services.try_get_keyed(service_key, ServiceWithNoDependencies)
            assert services.service_provider is not None
            assert services.service_provider.is_fully_initialized
        finally:
            await services.aclose()

        services = ServiceContainer()
        services.add_transient(ServiceWithNoDependencies)
        assert services.service_provider is None

        try:
            async with services.create_scope():
                assert services.service_provider is not None
                assert services.service_provider.is_fully_initialized
        finally:
            await services.aclose()

        services = ServiceContainer()
        services.add_transient(ServiceWithNoDependencies)

        async with services:
            assert services.service_provider is not None
            assert services.service_provider.is_fully_initialized

    async def test_override_service(self, mocker: MockerFixture) -> None:
        services = ServiceContainer()
        services.add_transient(ServiceWithNoDependencies)

        async with services:
            resolved_service = await services.get(ServiceWithNoDependencies)
            assert isinstance(resolved_service, ServiceWithNoDependencies)

            service_mock = mocker.create_autospec(
                ServiceWithNoDependencies, instance=True
            )

            with services.override(ServiceWithNoDependencies, service_mock):
                resolved_service = await services.get(ServiceWithNoDependencies)
                assert resolved_service is service_mock
                assert isinstance(resolved_service, ServiceWithNoDependencies)

            resolved_service = await services.get(ServiceWithNoDependencies)
            assert resolved_service is not service_mock
            assert isinstance(resolved_service, ServiceWithNoDependencies)

    async def test_override_keyed_service(self, mocker: MockerFixture) -> None:
        services = ServiceContainer()
        service_key = "key"
        services.add_keyed_transient(service_key, ServiceWithNoDependencies)

        async with services:
            resolved_service = await services.get_keyed(
                service_key, ServiceWithNoDependencies
            )
            assert isinstance(resolved_service, ServiceWithNoDependencies)

            service_mock = mocker.create_autospec(
                ServiceWithNoDependencies, instance=True
            )

            with services.override_keyed(
                service_key, ServiceWithNoDependencies, service_mock
            ):
                resolved_service = await services.get_keyed(
                    service_key, ServiceWithNoDependencies
                )
                assert resolved_service is service_mock
                assert isinstance(resolved_service, ServiceWithNoDependencies)

            resolved_service = await services.get_keyed(
                service_key, ServiceWithNoDependencies
            )
            assert resolved_service is not service_mock
            assert isinstance(resolved_service, ServiceWithNoDependencies)

    async def test_fail_when_overriding_when_container_is_not_built(self) -> None:
        services = ServiceContainer()

        with pytest.raises(ServiceContainerNotBuiltError):  # noqa: SIM117
            with services.override(ServiceWithNoDependencies, object()):
                pass

    @pytest.mark.parametrize(
        argnames="is_keyed_service",
        argvalues=[
            (True),
            (False),
        ],
    )
    async def test_resolve_service_added_after_initialization(
        self, is_keyed_service: bool
    ) -> None:
        constructed_instances: list[object] = []

        class AdditionalService:
            def __init__(self) -> None:
                constructed_instances.append(self)

        expected_descriptors = 3
        service_key = "key"
        services = ServiceContainer()

        if is_keyed_service:
            services.add_keyed_transient(service_key, ServiceWithNoDependencies)
        else:
            services.add_transient(ServiceWithNoDependencies)

        if is_keyed_service:
            resolved_service = await services.get_keyed(
                service_key, ServiceWithNoDependencies
            )
        else:
            resolved_service = await services.get(ServiceWithNoDependencies)

        assert isinstance(resolved_service, ServiceWithNoDependencies)
        assert services.service_provider is not None
        assert len(list(services)) == 2  # noqa: PLR2004

        if is_keyed_service:
            services.add_keyed_transient(service_key, AdditionalService)
        else:
            services.add_transient(AdditionalService)

        assert services.service_provider is not None
        assert len(list(services)) == expected_descriptors

        if is_keyed_service:
            resolved_service = await services.get_keyed(service_key, AdditionalService)
        else:
            resolved_service = await services.get(AdditionalService)

        assert isinstance(resolved_service, AdditionalService)
        assert len(constructed_instances) == 1
        assert resolved_service is constructed_instances[0]
        assert services.service_provider is not None
        assert len(list(services)) == expected_descriptors

        if is_keyed_service:
            resolved_service = await services.get_keyed(service_key, AdditionalService)
        else:
            resolved_service = await services.get(AdditionalService)

        assert isinstance(resolved_service, AdditionalService)
        assert len(constructed_instances) == 2  # noqa: PLR2004
        assert resolved_service is constructed_instances[1]
        assert services.service_provider is not None
        assert len(list(services)) == expected_descriptors

    @pytest.mark.parametrize(
        argnames="is_keyed_service",
        argvalues=[
            (True),
            (False),
        ],
    )
    async def test_resolve_service_added_after_initialization_using_context_manager(
        self, is_keyed_service: bool
    ) -> None:
        constructed_instances: list[object] = []

        class AdditionalService:
            def __init__(self) -> None:
                constructed_instances.append(self)

        expected_descriptors = 3
        service_key = "key"
        services = ServiceContainer()

        if is_keyed_service:
            services.add_keyed_transient(service_key, ServiceWithNoDependencies)
        else:
            services.add_transient(ServiceWithNoDependencies)

        async with services:
            if is_keyed_service:
                resolved_service = await services.get_keyed(
                    service_key, ServiceWithNoDependencies
                )
            else:
                resolved_service = await services.get(ServiceWithNoDependencies)

            assert isinstance(resolved_service, ServiceWithNoDependencies)
            assert services.service_provider is not None
            assert len(list(services)) == 2  # noqa: PLR2004

            if is_keyed_service:
                services.add_keyed_transient(service_key, AdditionalService)
            else:
                services.add_transient(AdditionalService)

            assert services.service_provider is not None
            assert len(list(services)) == expected_descriptors

            if is_keyed_service:
                resolved_service = await services.get_keyed(
                    service_key, AdditionalService
                )
            else:
                resolved_service = await services.get(AdditionalService)

            assert isinstance(resolved_service, AdditionalService)
            assert len(constructed_instances) == 1
            assert resolved_service is constructed_instances[0]
            assert services.service_provider is not None
            assert len(list(services)) == expected_descriptors

            if is_keyed_service:
                resolved_service = await services.get_keyed(
                    service_key, AdditionalService
                )
            else:
                resolved_service = await services.get(AdditionalService)

            assert isinstance(resolved_service, AdditionalService)
            assert len(constructed_instances) == 2  # noqa: PLR2004
            assert resolved_service is constructed_instances[1]
            assert services.service_provider is not None
            assert len(list(services)) == expected_descriptors

    async def test_auto_activate_service_added_after_initialization(self) -> None:
        constructed_instances: list[object] = []

        class AutoActivatedService:
            def __init__(self) -> None:
                constructed_instances.append(self)

        services = ServiceContainer()
        services.add_transient(ServiceWithNoDependencies)

        async with services:
            await services.get(ServiceWithNoDependencies)
            assert len(constructed_instances) == 0

            services.add_auto_activated_singleton(AutoActivatedService)

            await services.get(ServiceWithNoDependencies)
            assert len(constructed_instances) == 1

            resolved_service = await services.get(AutoActivatedService)

            assert isinstance(resolved_service, AutoActivatedService)
            assert resolved_service is constructed_instances[0]
            assert len(constructed_instances) == 1

    async def test_auto_initialize_service_after_context_manager(self) -> None:
        constructed_instances: list[object] = []

        class Service1:
            pass

        class Service2:
            def __init__(self, service_1: Service1) -> None:
                self.service_1 = service_1
                constructed_instances.append(self)

        services = ServiceContainer()
        services.add_transient(Service1)

        service_1 = await services.get(Service1)
        assert isinstance(service_1, Service1)

        services.add_auto_activated_singleton(Service2)
        assert services.service_provider is not None
        assert not services.service_provider.is_fully_initialized

        assert len(constructed_instances) == 0

        async with services:
            assert services.service_provider is not None
            assert services.service_provider.is_fully_initialized
            assert len(constructed_instances) == 1

            auto_activated_service = constructed_instances[0]
            assert isinstance(auto_activated_service, Service2)
            assert isinstance(auto_activated_service.service_1, Service1)

            resolved_service = await services.get(Service2)
            assert resolved_service is auto_activated_service

    async def test_not_accumulate_pending_descriptors_before_initialization(
        self,
    ) -> None:
        expected_descriptors = 3
        services = ServiceContainer()
        services.add_transient(ServiceWithNoDependencies)

        assert services.service_provider is None
        assert len(list(services)) == 2  # noqa: PLR2004

        services.add_transient(ServiceWithDependencies)
        assert services.service_provider is None
        assert len(list(services)) == expected_descriptors

        await services.get(ServiceWithDependencies)
        assert services.service_provider is not None
        assert len(services.service_provider.pending_descriptors) == 0
        assert len(list(services)) == expected_descriptors

    async def test_accumulate_pending_descriptors_after_initialization(
        self,
    ) -> None:
        services = ServiceContainer()
        services.add_transient(ServiceWithNoDependencies)
        assert services.service_provider is None
        assert len(list(services)) == 2  # noqa: PLR2004

        await services.get(ServiceWithNoDependencies)
        assert services.service_provider is not None
        assert len(services.service_provider.pending_descriptors) == 0
        assert len(list(services)) == 2  # noqa: PLR2004

        services.add_transient(ServiceWithDependencies)
        assert services.service_provider is not None
        assert len(services.service_provider.pending_descriptors) == 1
        assert len(list(services)) == 3  # noqa: PLR2004

    async def test_return_service_provider_if_it_is_already_built(self) -> None:
        services = ServiceContainer()
        services.add_transient(ServiceWithNoDependencies)

        async with services:
            expected_service_provider = services.service_provider
            built_service_provider = services.build_service_provider()

            assert expected_service_provider is built_service_provider

    async def test_add_singleton_service_after_initialization(self) -> None:
        constructed_instances: list[object] = []

        class SingletonService:
            def __init__(self) -> None:
                constructed_instances.append(self)

        services = ServiceContainer()
        services.add_transient(ServiceWithNoDependencies)

        async with services:
            # Add singleton after container is initialized
            services.add_singleton(SingletonService)

            # First resolution
            service1 = await services.get(SingletonService)
            assert isinstance(service1, SingletonService)
            assert len(constructed_instances) == 1

            # Second resolution should return the same instance
            service2 = await services.get(SingletonService)
            assert service2 is service1
            assert len(constructed_instances) == 1

    async def test_add_scoped_service_after_initialization(self) -> None:
        constructed_instances: list[object] = []

        class ScopedService:
            def __init__(self) -> None:
                constructed_instances.append(self)

        services = ServiceContainer()
        services.add_transient(ServiceWithNoDependencies)

        async with services:
            # Add scoped service after container is initialized
            services.add_scoped(ScopedService)

            # Create first scope
            async with services.create_scope() as scope1:
                service1 = await scope1.get_required_service(ScopedService)
                assert isinstance(service1, ScopedService)
                assert len(constructed_instances) == 1

                # Same instance within scope
                service1_again = await scope1.get_required_service(ScopedService)
                assert service1_again is service1
                assert len(constructed_instances) == 1

            # Create second scope. It should get a different instance
            async with services.create_scope() as scope2:
                service2 = await scope2.get_required_service(ScopedService)
                assert isinstance(service2, ScopedService)
                assert service2 is not service1
                assert len(constructed_instances) == 2  # noqa: PLR2004

    async def test_add_service_with_dependencies_after_initialization(self) -> None:
        constructed_instances: list[object] = []

        class DependentService:
            def __init__(self, dependency: ServiceWithNoDependencies) -> None:
                self.dependency = dependency
                constructed_instances.append(self)

        services = ServiceContainer()
        services.add_transient(ServiceWithNoDependencies)

        async with services:
            # Add service with dependencies after initialization
            services.add_transient(DependentService)

            # Resolve and verify dependencies are injected
            service = await services.get(DependentService)
            assert isinstance(service, DependentService)
            assert isinstance(service.dependency, ServiceWithNoDependencies)
            assert len(constructed_instances) == 1

    async def test_add_factory_based_service_after_initialization(self) -> None:
        constructed_instances: list[object] = []
        factory_call_count = [0]

        class FactoryService:
            def __init__(self) -> None:
                constructed_instances.append(self)

        def service_factory() -> FactoryService:
            factory_call_count[0] += 1
            return FactoryService()

        services = ServiceContainer()
        services.add_transient(ServiceWithNoDependencies)

        async with services:
            # Add factory-based service after initialization
            services.add_transient(FactoryService, service_factory)

            # Verify factory is called
            service = await services.get(FactoryService)
            assert isinstance(service, FactoryService)
            assert factory_call_count[0] == 1
            assert len(constructed_instances) == 1

    async def test_add_multiple_services_sequentially_after_initialization(
        self,
    ) -> None:
        class Service1:
            pass

        class Service2:
            def __init__(self, service1: Service1) -> None:
                self.service1 = service1

        class Service3:
            def __init__(self, service2: Service2) -> None:
                self.service2 = service2

        services = ServiceContainer()
        services.add_transient(ServiceWithNoDependencies)

        async with services:
            # Add services one by one
            services.add_singleton(Service1)
            service1 = await services.get(Service1)
            assert isinstance(service1, Service1)

            services.add_singleton(Service2)
            service2 = await services.get(Service2)
            assert isinstance(service2, Service2)
            assert isinstance(service2.service1, Service1)

            services.add_singleton(Service3)
            service3 = await services.get(Service3)
            assert isinstance(service3, Service3)
            assert isinstance(service3.service2, Service2)
            assert isinstance(service3.service2.service1, Service1)

    async def test_resolve_same_service_with_different_implementation_instance_added_after_build(
        self,
    ) -> None:
        service_instance_1 = ServiceWithNoDependencies()
        service_instance_2 = ServiceWithNoDependencies()
        services = ServiceContainer()
        services.add_singleton(ServiceWithNoDependencies, service_instance_1)

        async with services:
            resolved_service_1 = await services.get(ServiceWithNoDependencies)
            assert resolved_service_1 is service_instance_1

            services.add_singleton(ServiceWithNoDependencies, service_instance_2)
            resolved_service_2 = await services.get(ServiceWithNoDependencies)
            assert resolved_service_2 is service_instance_2

    async def test_replace_singleton_registration_with_different_implementation_type_after_initialization(
        self,
    ) -> None:
        services = ServiceContainer()

        class BaseService:
            pass

        class InitialService(BaseService):
            pass

        class ReplacementService(BaseService):
            pass

        services.add_singleton(BaseService, InitialService)

        try:
            first_instance = await services.get(BaseService)
            assert isinstance(first_instance, InitialService)

            services.add_singleton(BaseService, ReplacementService)

            replacement_instance = await services.get(BaseService)
            assert isinstance(replacement_instance, ReplacementService)
            assert replacement_instance is not first_instance

            repeated_instance = await services.get(BaseService)
            assert repeated_instance is replacement_instance
        finally:
            await services.aclose()

    async def test_replace_keyed_singleton_registration_after_initialization(
        self,
    ) -> None:
        service_key = "key"
        services = ServiceContainer()

        class BaseService:
            pass

        class InitialService(BaseService):
            pass

        class ReplacementService(BaseService):
            pass

        services.add_keyed_singleton(service_key, BaseService, InitialService)

        try:
            first_instance = await services.get_keyed(service_key, BaseService)
            assert isinstance(first_instance, InitialService)

            services.add_keyed_singleton(service_key, BaseService, ReplacementService)

            replacement_instance = await services.get_keyed(service_key, BaseService)
            assert isinstance(replacement_instance, ReplacementService)
            assert replacement_instance is not first_instance

            repeated_instance = await services.get_keyed(service_key, BaseService)
            assert repeated_instance is replacement_instance
        finally:
            await services.aclose()

    async def test_not_reexecute_previous_singleton_factory_after_replacement(
        self,
    ) -> None:
        services = ServiceContainer()
        first_factory_invocations = 0
        second_factory_invocations = 0

        class BaseService:
            pass

        class InitialService(BaseService):
            pass

        class ReplacementService(BaseService):
            pass

        def first_factory() -> BaseService:
            nonlocal first_factory_invocations
            first_factory_invocations += 1
            return InitialService()

        def second_factory() -> BaseService:
            nonlocal second_factory_invocations
            second_factory_invocations += 1
            return ReplacementService()

        services.add_singleton(BaseService, first_factory)

        try:
            initial_instance = await services.get(BaseService)
            assert isinstance(initial_instance, InitialService)
            assert first_factory_invocations == 1
            assert second_factory_invocations == 0

            services.add_singleton(BaseService, second_factory)

            replacement_instance = await services.get(BaseService)
            assert isinstance(replacement_instance, ReplacementService)
            assert replacement_instance is not initial_instance
            assert first_factory_invocations == 1
            assert second_factory_invocations == 1
        finally:
            await services.aclose()

    @pytest.mark.parametrize(
        argnames=("is_keyed_service"),
        argvalues=[
            (True),
            (False),
        ],
    )
    async def test_resolve_all_services_of_the_same_type(
        self, is_keyed_service: bool
    ) -> None:
        expected_services = 3
        service_key = "key"
        services = ServiceContainer()

        if is_keyed_service:
            services.add_keyed_transient(service_key, ServiceWithNoDependencies)
            services.add_keyed_transient(service_key, ServiceWithNoDependencies)
            services.add_keyed_transient(service_key, ServiceWithNoDependencies)
        else:
            services.add_transient(ServiceWithNoDependencies)
            services.add_transient(ServiceWithNoDependencies)
            services.add_transient(ServiceWithNoDependencies)

        async with services:
            resolved_services = (
                await services.get_all_keyed(service_key, ServiceWithNoDependencies)
                if is_keyed_service
                else await services.get_all(ServiceWithNoDependencies)
            )

            assert isinstance(resolved_services, Sequence)
            assert len(resolved_services) == expected_services
            assert all(
                isinstance(service, ServiceWithNoDependencies)
                for service in resolved_services
            )
