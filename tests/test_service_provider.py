from typing import Annotated

from tests.utils.services import ServiceWithDependencies, ServiceWithNoDependencies
from wirio.abstractions.keyed_service import KeyedService
from wirio.annotations import FromKeyedServices, ServiceKey
from wirio.service_container import ServiceContainer


class TestServiceProvider:
    async def test_resolve_overridden_service(self) -> None:
        services = ServiceContainer()
        services.add_transient(ServiceWithNoDependencies)

        async with services:
            overridden_instance = ServiceWithNoDependencies()

            resolved_before_override = await services.get(ServiceWithNoDependencies)

            assert resolved_before_override is not overridden_instance

            with services.override(ServiceWithNoDependencies, overridden_instance):
                resolved_service = await services.get(ServiceWithNoDependencies)

                assert resolved_service is overridden_instance

            resolved_after_override = await services.get(ServiceWithNoDependencies)

            assert resolved_after_override is not overridden_instance
            assert isinstance(resolved_after_override, ServiceWithNoDependencies)

    async def test_resolve_overridden_but_not_registered_service(self) -> None:
        services = ServiceContainer()

        async with services:
            overridden_instance = ServiceWithNoDependencies()

            with services.override(ServiceWithNoDependencies, overridden_instance):
                resolved_service = await services.get(ServiceWithNoDependencies)

                assert resolved_service is overridden_instance

    async def test_resolve_overridden_keyed_service(self) -> None:
        service_key = "key"
        services = ServiceContainer()
        services.add_keyed_transient(service_key, ServiceWithNoDependencies)

        async with services:
            overridden_instance = ServiceWithNoDependencies()

            resolved_before_override = await services.get_keyed(
                service_key, ServiceWithNoDependencies
            )

            assert resolved_before_override is not overridden_instance

            with services.override_keyed(
                service_key,
                ServiceWithNoDependencies,
                overridden_instance,
            ):
                resolved_service = await services.get_keyed(
                    service_key, ServiceWithNoDependencies
                )

                assert resolved_service is overridden_instance

            resolved_after_override = await services.get_keyed(
                service_key, ServiceWithNoDependencies
            )

            assert resolved_after_override is not overridden_instance
            assert isinstance(resolved_after_override, ServiceWithNoDependencies)

    async def test_resolve_overridden_keyed_service_with_any_key(self) -> None:
        service_key = KeyedService.ANY_KEY
        services = ServiceContainer()
        services.add_keyed_transient("actual_key", ServiceWithNoDependencies)
        async with services:
            overridden_instance = ServiceWithNoDependencies()

            with services.override_keyed(
                service_key,
                ServiceWithNoDependencies,
                overridden_instance,
            ):
                resolved_service = await services.get_keyed(
                    "actual_key", ServiceWithNoDependencies
                )

                assert resolved_service is overridden_instance

    async def test_resolve_overridden_keyed_service_using_from_keyed_services_annotation(
        self,
    ) -> None:
        service_key = "key"

        class Service:
            def __init__(
                self,
                dependency: Annotated[
                    ServiceWithNoDependencies, FromKeyedServices("key")
                ],
            ) -> None:
                self.dependency = dependency

        services = ServiceContainer()
        services.add_keyed_transient(service_key, ServiceWithNoDependencies)
        services.add_transient(Service)

        async with services:
            overridden_instance = ServiceWithNoDependencies()

            with services.override_keyed(
                service_key,
                ServiceWithNoDependencies,
                overridden_instance,
            ):
                resolved_service = await services.get(Service)

                assert resolved_service.dependency is overridden_instance

    async def test_resolve_last_overridden_service(self) -> None:
        services = ServiceContainer()
        services.add_transient(ServiceWithNoDependencies)

        async with services:
            first_overridden_instance = ServiceWithNoDependencies()
            second_overridden_instance = ServiceWithNoDependencies()

            with services.override(
                ServiceWithNoDependencies, first_overridden_instance
            ):
                with services.override(
                    ServiceWithNoDependencies, second_overridden_instance
                ):
                    resolved_service = await services.get(ServiceWithNoDependencies)

                    assert resolved_service is second_overridden_instance

                resolved_service_after_inner_override = await services.get(
                    ServiceWithNoDependencies
                )

                assert (
                    resolved_service_after_inner_override is first_overridden_instance
                )

            resolved_after_all_overrides = await services.get(ServiceWithNoDependencies)

            assert isinstance(resolved_after_all_overrides, ServiceWithNoDependencies)
            assert resolved_after_all_overrides is not first_overridden_instance
            assert resolved_after_all_overrides is not second_overridden_instance

    async def test_resolve_overridden_service_when_service_is_already_cached(
        self,
    ) -> None:
        services = ServiceContainer()
        services.add_singleton(ServiceWithNoDependencies)

        async with services:
            cached_instance = await services.get(ServiceWithNoDependencies)

            overridden_instance = ServiceWithNoDependencies()

            with services.override(ServiceWithNoDependencies, overridden_instance):
                resolved_service = await services.get(ServiceWithNoDependencies)

                assert resolved_service is overridden_instance

            resolved_after_override = await services.get(ServiceWithNoDependencies)

            assert resolved_after_override is cached_instance
            assert isinstance(resolved_after_override, ServiceWithNoDependencies)

    async def test_resolve_none_when_overriding_with_none(self) -> None:
        services = ServiceContainer()
        services.add_transient(ServiceWithNoDependencies)

        async with services:
            with services.override(ServiceWithNoDependencies, None):
                resolved_service = await services.try_get(ServiceWithNoDependencies)

                assert resolved_service is None

            resolved_after_override = await services.try_get(ServiceWithNoDependencies)

            assert isinstance(resolved_after_override, ServiceWithNoDependencies)

    async def test_resolve_overridden_service_in_implementation_factory(self) -> None:
        services = ServiceContainer()

        def implementation_factory(
            dependency: ServiceWithNoDependencies,
        ) -> ServiceWithDependencies:
            return ServiceWithDependencies(dependency)

        services.add_transient(ServiceWithNoDependencies)
        services.add_transient(implementation_factory)

        async with services:
            overridden_instance = ServiceWithNoDependencies()

            with services.override(ServiceWithNoDependencies, overridden_instance):
                resolved_service = await services.get(ServiceWithNoDependencies)

                assert resolved_service is overridden_instance

    async def test_activate_eagerly_auto_activated_singleton_service(
        self,
    ) -> None:
        expected_instances = 1
        constructed_instances: list[object] = []

        class AutoActivatedService:
            def __init__(self) -> None:
                constructed_instances.append(self)

        services = ServiceContainer()
        services.add_auto_activated_singleton(AutoActivatedService)

        async with services:
            assert len(constructed_instances) == expected_instances

            resolved_service = await services.get(AutoActivatedService)

            assert len(constructed_instances) == expected_instances
            assert resolved_service is constructed_instances[0]

    async def test_activate_auto_activated_keyed_singleton_service(
        self,
    ) -> None:
        captured_keys: list[str] = []

        class AutoActivatedKeyedService:
            def __init__(self, service_key: Annotated[str, ServiceKey()]) -> None:
                assert service_key is not None
                captured_keys.append(service_key)

        service_key = "key"
        services = ServiceContainer()
        services.add_auto_activated_keyed_singleton(
            service_key, AutoActivatedKeyedService
        )

        async with services:
            assert captured_keys == [service_key]
            resolved_service = await services.get_keyed(
                service_key,
                AutoActivatedKeyedService,
            )

            assert isinstance(resolved_service, AutoActivatedKeyedService)
            assert captured_keys == [service_key]

    async def test_not_activate_eagerly_non_auto_activated_services(
        self,
    ) -> None:
        constructed_instances: list[object] = []

        class SingletonService:
            def __init__(self) -> None:
                constructed_instances.append(self)

        class ScopedService:
            def __init__(self) -> None:
                constructed_instances.append(self)

        class TransientService:
            def __init__(self) -> None:
                constructed_instances.append(self)

        services = ServiceContainer()
        services.add_singleton(SingletonService)
        services.add_scoped(ScopedService)
        services.add_transient(TransientService)

        async with services:
            assert len(constructed_instances) == 0
