from typing import Annotated

from aspy_dependency_injection.abstractions.keyed_service import KeyedService
from aspy_dependency_injection.annotations import FromKeyedServices
from aspy_dependency_injection.service_collection import ServiceCollection
from tests.utils.services import ServiceWithDependencies, ServiceWithNoDependencies


class TestServiceProvider:
    async def test_resolve_overridden_service(self) -> None:
        services = ServiceCollection()
        services.add_transient(ServiceWithNoDependencies)

        async with services.build_service_provider() as service_provider:
            overridden_instance = ServiceWithNoDependencies()

            resolved_before_override = await service_provider.get_required_service(
                ServiceWithNoDependencies
            )

            assert resolved_before_override is not overridden_instance

            with service_provider.override_service(
                ServiceWithNoDependencies, overridden_instance
            ):
                resolved_service = await service_provider.get_required_service(
                    ServiceWithNoDependencies
                )

                assert resolved_service is overridden_instance

            resolved_after_override = await service_provider.get_required_service(
                ServiceWithNoDependencies
            )

            assert resolved_after_override is not overridden_instance
            assert isinstance(resolved_after_override, ServiceWithNoDependencies)

    async def test_resolve_overridden_but_not_registered_service(self) -> None:
        services = ServiceCollection()

        async with services.build_service_provider() as service_provider:
            overridden_instance = ServiceWithNoDependencies()

            with service_provider.override_service(
                ServiceWithNoDependencies, overridden_instance
            ):
                resolved_service = await service_provider.get_required_service(
                    ServiceWithNoDependencies
                )

                assert resolved_service is overridden_instance

    async def test_resolve_overridden_keyed_service(self) -> None:
        service_key = "key"
        services = ServiceCollection()
        services.add_keyed_transient(service_key, ServiceWithNoDependencies)

        async with services.build_service_provider() as service_provider:
            overridden_instance = ServiceWithNoDependencies()

            resolved_before_override = (
                await service_provider.get_required_keyed_service(
                    service_key, ServiceWithNoDependencies
                )
            )

            assert resolved_before_override is not overridden_instance

            with service_provider.override_keyed_service(
                service_key,
                ServiceWithNoDependencies,
                overridden_instance,
            ):
                resolved_service = await service_provider.get_required_keyed_service(
                    service_key, ServiceWithNoDependencies
                )

                assert resolved_service is overridden_instance

            resolved_after_override = await service_provider.get_required_keyed_service(
                service_key, ServiceWithNoDependencies
            )

            assert resolved_after_override is not overridden_instance
            assert isinstance(resolved_after_override, ServiceWithNoDependencies)

    async def test_resolve_overridden_keyed_service_with_any_key(self) -> None:
        service_key = KeyedService.ANY_KEY
        services = ServiceCollection()
        services.add_keyed_transient("actual_key", ServiceWithNoDependencies)
        async with services.build_service_provider() as service_provider:
            overridden_instance = ServiceWithNoDependencies()

            with service_provider.override_keyed_service(
                service_key,
                ServiceWithNoDependencies,
                overridden_instance,
            ):
                resolved_service = await service_provider.get_required_keyed_service(
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

        services = ServiceCollection()
        services.add_keyed_transient(service_key, ServiceWithNoDependencies)
        services.add_transient(Service)

        async with services.build_service_provider() as service_provider:
            overridden_instance = ServiceWithNoDependencies()

            with service_provider.override_keyed_service(
                service_key,
                ServiceWithNoDependencies,
                overridden_instance,
            ):
                resolved_service = await service_provider.get_required_service(Service)

                assert resolved_service.dependency is overridden_instance

    async def test_resolve_last_overridden_service(self) -> None:
        services = ServiceCollection()
        services.add_transient(ServiceWithNoDependencies)

        async with services.build_service_provider() as service_provider:
            first_overridden_instance = ServiceWithNoDependencies()
            second_overridden_instance = ServiceWithNoDependencies()

            with service_provider.override_service(
                ServiceWithNoDependencies, first_overridden_instance
            ):
                with service_provider.override_service(
                    ServiceWithNoDependencies, second_overridden_instance
                ):
                    resolved_service = await service_provider.get_required_service(
                        ServiceWithNoDependencies
                    )

                    assert resolved_service is second_overridden_instance

                resolved_service_after_inner_override = (
                    await service_provider.get_required_service(
                        ServiceWithNoDependencies
                    )
                )

                assert (
                    resolved_service_after_inner_override is first_overridden_instance
                )

            resolved_after_all_overrides = await service_provider.get_required_service(
                ServiceWithNoDependencies
            )

            assert isinstance(resolved_after_all_overrides, ServiceWithNoDependencies)
            assert resolved_after_all_overrides is not first_overridden_instance
            assert resolved_after_all_overrides is not second_overridden_instance

    async def test_resolve_overridden_service_when_service_is_already_cached(
        self,
    ) -> None:
        services = ServiceCollection()
        services.add_singleton(ServiceWithNoDependencies)

        async with services.build_service_provider() as service_provider:
            cached_instance = await service_provider.get_required_service(
                ServiceWithNoDependencies
            )

            overridden_instance = ServiceWithNoDependencies()

            with service_provider.override_service(
                ServiceWithNoDependencies, overridden_instance
            ):
                resolved_service = await service_provider.get_required_service(
                    ServiceWithNoDependencies
                )

                assert resolved_service is overridden_instance

            resolved_after_override = await service_provider.get_required_service(
                ServiceWithNoDependencies
            )

            assert resolved_after_override is cached_instance
            assert isinstance(resolved_after_override, ServiceWithNoDependencies)

    async def test_resolve_none_when_overriding_with_none(self) -> None:
        services = ServiceCollection()
        services.add_transient(ServiceWithNoDependencies)

        async with services.build_service_provider() as service_provider:
            with service_provider.override_service(ServiceWithNoDependencies, None):
                resolved_service = await service_provider.get_service(
                    ServiceWithNoDependencies
                )

                assert resolved_service is None

            resolved_after_override = await service_provider.get_service(
                ServiceWithNoDependencies
            )

            assert isinstance(resolved_after_override, ServiceWithNoDependencies)

    async def test_resolve_overridden_service_in_implementation_factory(self) -> None:
        services = ServiceCollection()

        def implementation_factory(
            dependency: ServiceWithNoDependencies,
        ) -> ServiceWithDependencies:
            return ServiceWithDependencies(dependency)

        services.add_transient(ServiceWithNoDependencies)
        services.add_transient(implementation_factory)

        async with services.build_service_provider() as service_provider:
            overridden_instance = ServiceWithNoDependencies()

            with service_provider.override_service(
                ServiceWithNoDependencies, overridden_instance
            ):
                resolved_service = await service_provider.get_required_service(
                    ServiceWithNoDependencies
                )

                assert resolved_service is overridden_instance
