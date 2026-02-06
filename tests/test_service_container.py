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
            await services.get_required_service(ServiceWithNoDependencies)
            assert services.service_provider is not None
            assert services.service_provider.is_fully_initialized
        finally:
            await services.aclose()

        services = ServiceContainer()
        services.add_transient(ServiceWithNoDependencies)
        assert services.service_provider is None

        try:
            await services.get_service(ServiceWithNoDependencies)
            assert services.service_provider is not None
            assert services.service_provider.is_fully_initialized
        finally:
            await services.aclose()

        service_key = "key"
        services = ServiceContainer()
        services.add_keyed_transient(service_key, ServiceWithNoDependencies)
        assert services.service_provider is None

        try:
            await services.get_required_keyed_service(
                service_key, ServiceWithNoDependencies
            )
            assert services.service_provider is not None
            assert services.service_provider.is_fully_initialized
        finally:
            await services.aclose()

        services = ServiceContainer()
        services.add_keyed_transient(service_key, ServiceWithNoDependencies)
        assert services.service_provider is None

        try:
            await services.get_keyed_service(service_key, ServiceWithNoDependencies)
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
            resolved_service = await services.get_required_service(
                ServiceWithNoDependencies
            )
            assert isinstance(resolved_service, ServiceWithNoDependencies)

            service_mock = mocker.create_autospec(
                ServiceWithNoDependencies, instance=True
            )

            with services.override_service(ServiceWithNoDependencies, service_mock):
                resolved_service = await services.get_required_service(
                    ServiceWithNoDependencies
                )
                assert resolved_service is service_mock
                assert isinstance(resolved_service, ServiceWithNoDependencies)

            resolved_service = await services.get_required_service(
                ServiceWithNoDependencies
            )
            assert resolved_service is not service_mock
            assert isinstance(resolved_service, ServiceWithNoDependencies)

    async def test_override_keyed_service(self, mocker: MockerFixture) -> None:
        services = ServiceContainer()
        service_key = "key"
        services.add_keyed_transient(service_key, ServiceWithNoDependencies)

        async with services:
            resolved_service = await services.get_required_keyed_service(
                service_key, ServiceWithNoDependencies
            )
            assert isinstance(resolved_service, ServiceWithNoDependencies)

            service_mock = mocker.create_autospec(
                ServiceWithNoDependencies, instance=True
            )

            with services.override_keyed_service(
                service_key, ServiceWithNoDependencies, service_mock
            ):
                resolved_service = await services.get_required_keyed_service(
                    service_key, ServiceWithNoDependencies
                )
                assert resolved_service is service_mock
                assert isinstance(resolved_service, ServiceWithNoDependencies)

            resolved_service = await services.get_required_keyed_service(
                service_key, ServiceWithNoDependencies
            )
            assert resolved_service is not service_mock
            assert isinstance(resolved_service, ServiceWithNoDependencies)

    async def test_fail_overriding_when_container_is_not_built(self) -> None:
        services = ServiceContainer()

        with pytest.raises(ServiceContainerNotBuiltError):  # noqa: SIM117
            with services.override_service(ServiceWithNoDependencies, object()):
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

        expected_descriptors = 2
        service_key = "key"
        services = ServiceContainer()

        if is_keyed_service:
            services.add_keyed_transient(service_key, ServiceWithNoDependencies)
        else:
            services.add_transient(ServiceWithNoDependencies)

        async with services:
            if is_keyed_service:
                resolved_service = await services.get_required_keyed_service(
                    service_key, ServiceWithNoDependencies
                )
            else:
                resolved_service = await services.get_required_service(
                    ServiceWithNoDependencies
                )

            assert isinstance(resolved_service, ServiceWithNoDependencies)
            assert services.service_provider is not None
            assert len(list(services)) == 1

            if is_keyed_service:
                services.add_keyed_transient(service_key, AdditionalService)
            else:
                services.add_transient(AdditionalService)

            assert services.service_provider is not None
            assert len(list(services)) == expected_descriptors

            if is_keyed_service:
                resolved_service = await services.get_required_keyed_service(
                    service_key, AdditionalService
                )
            else:
                resolved_service = await services.get_required_service(
                    AdditionalService
                )

            assert isinstance(resolved_service, AdditionalService)
            assert len(constructed_instances) == 1
            assert resolved_service is constructed_instances[0]
            assert services.service_provider is not None
            assert len(list(services)) == expected_descriptors

            if is_keyed_service:
                resolved_service = await services.get_required_keyed_service(
                    service_key, AdditionalService
                )
            else:
                resolved_service = await services.get_required_service(
                    AdditionalService
                )

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
            await services.get_required_service(ServiceWithNoDependencies)
            assert len(constructed_instances) == 0

            services.add_auto_activated_singleton(AutoActivatedService)

            await services.get_required_service(ServiceWithNoDependencies)
            assert len(constructed_instances) == 1

            resolved_service = await services.get_required_service(AutoActivatedService)

            assert isinstance(resolved_service, AutoActivatedService)
            assert resolved_service is constructed_instances[0]
            assert len(constructed_instances) == 1

    async def test_resolve_keyed_service_added_after_initialization(self) -> None:
        class AdditionalKeyedService:
            pass

        services = ServiceContainer()
        services.add_transient(ServiceWithNoDependencies)
        service_key = "key"
        assert services.service_provider is None

        await services.get_required_service(ServiceWithNoDependencies)
        assert services.service_provider is not None
        services.add_keyed_transient(service_key, AdditionalKeyedService)

        assert services.service_provider is not None

        resolved_service = await services.get_required_keyed_service(
            service_key, AdditionalKeyedService
        )

        assert isinstance(resolved_service, AdditionalKeyedService)

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

        service_1 = await services.get_required_service(Service1)
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

            resolved_service = await services.get_required_service(Service2)
            assert resolved_service is auto_activated_service

    async def test_not_accumulate_pending_descriptors_before_initialization(
        self,
    ) -> None:
        expected_descriptors = 2
        services = ServiceContainer()
        services.add_transient(ServiceWithNoDependencies)

        assert services.service_provider is None
        assert len(list(services)) == 1

        services.add_transient(ServiceWithDependencies)
        assert services.service_provider is None
        assert len(list(services)) == expected_descriptors

        await services.get_required_service(ServiceWithDependencies)
        assert services.service_provider is not None
        assert len(services.service_provider._pending_descriptors) == 0  # noqa: SLF001
        assert len(list(services)) == expected_descriptors

    async def test_accumulate_pending_descriptors_after_initialization(
        self,
    ) -> None:
        services = ServiceContainer()
        services.add_transient(ServiceWithNoDependencies)
        assert services.service_provider is None
        assert len(list(services)) == 1

        await services.get_required_service(ServiceWithNoDependencies)
        assert services.service_provider is not None
        assert len(services.service_provider._pending_descriptors) == 0  # noqa: SLF001
        assert len(list(services)) == 1

        services.add_transient(ServiceWithDependencies)
        assert services.service_provider is not None
        assert len(services.service_provider._pending_descriptors) == 1  # noqa: SLF001
        assert len(list(services)) == 2  # noqa: PLR2004

    async def test_return_service_provider_is_it_is_already_built(self) -> None:
        services = ServiceContainer()
        services.add_transient(ServiceWithNoDependencies)

        async with services:
            expected_service_provider = services.service_provider
            built_service_provider = services.build_service_provider()

            assert expected_service_provider is built_service_provider
