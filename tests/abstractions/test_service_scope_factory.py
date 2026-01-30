import pytest

from tests.utils.services import (
    ServiceWithAsyncContextManagerAndNoDependencies,
    ServiceWithNoDependencies,
)
from wirio.abstractions.keyed_service import KeyedService
from wirio.abstractions.service_scope_factory import (
    ServiceScopeFactory,
)
from wirio.exceptions import (
    KeyedServiceAnyKeyUsedToResolveServiceError,
)
from wirio.service_collection import ServiceCollection


class TestServiceScopeFactory:
    async def test_resolve_service_scope_factory(self) -> None:
        services = ServiceCollection()

        async with services.build_service_provider() as service_provider:
            service_scope_factory = await service_provider.get_required_service(
                ServiceScopeFactory
            )

            assert isinstance(service_scope_factory, ServiceScopeFactory)

    async def test_service_scope_factory_is_singleton(self) -> None:
        services = ServiceCollection()

        async with services.build_service_provider() as service_provider:
            scope_factory_1 = await service_provider.get_required_service(
                ServiceScopeFactory
            )
            scope_factory_2 = await service_provider.get_required_service(
                ServiceScopeFactory
            )

            async with service_provider.create_scope() as service_scope:
                scope_factory_3 = (
                    await service_scope.service_provider.get_required_service(
                        ServiceScopeFactory
                    )
                )

                assert scope_factory_1 is scope_factory_2
                assert scope_factory_1 is scope_factory_3

    async def test_can_resolve_and_dispose_scoped_services_from_cached_scope_factory(
        self,
    ) -> None:
        services = ServiceCollection()
        services.add_scoped(ServiceWithAsyncContextManagerAndNoDependencies)

        async with services.build_service_provider() as service_provider:
            cached_scope_factory = await service_provider.get_required_service(
                ServiceScopeFactory
            )

            for _ in range(3):
                async with cached_scope_factory.create_scope() as outer_scope:
                    async with (
                        outer_scope.service_provider.create_scope() as inner_scope
                    ):
                        outer_scoped_service = (
                            await outer_scope.service_provider.get_required_service(
                                ServiceWithAsyncContextManagerAndNoDependencies
                            )
                        )
                        inner_scoped_service = (
                            await inner_scope.service_provider.get_required_service(
                                ServiceWithAsyncContextManagerAndNoDependencies
                            )
                        )

                        assert outer_scoped_service is not None
                        assert inner_scoped_service is not None
                        assert outer_scoped_service is not inner_scoped_service

                    assert not outer_scoped_service.is_disposed
                    assert inner_scoped_service.is_disposed

                assert outer_scoped_service.is_disposed

    async def test_resolve_keyed_singleton_service_from_scope_service_provider(
        self,
    ) -> None:
        service_key = "key"
        services = ServiceCollection()
        services.add_keyed_singleton(service_key, ServiceWithNoDependencies)

        async with (
            services.build_service_provider() as service_provider,
            (
                await service_provider.get_required_service(ServiceScopeFactory)
            ).create_scope() as scope_a,
            (
                await service_provider.get_required_service(ServiceScopeFactory)
            ).create_scope() as scope_b,
        ):
            assert (
                await scope_a.service_provider.get_service(ServiceWithNoDependencies)
                is None
            )
            assert (
                await scope_b.service_provider.get_service(ServiceWithNoDependencies)
                is None
            )

            with pytest.raises(KeyedServiceAnyKeyUsedToResolveServiceError):
                await scope_a.service_provider.get_keyed_service(
                    service_key=KeyedService.ANY_KEY,
                    service_type=ServiceWithNoDependencies,
                )

            with pytest.raises(KeyedServiceAnyKeyUsedToResolveServiceError):
                await scope_b.service_provider.get_keyed_service(
                    service_key=KeyedService.ANY_KEY,
                    service_type=ServiceWithNoDependencies,
                )

            service_a_1 = await scope_a.service_provider.get_keyed_service(
                service_key=service_key,
                service_type=ServiceWithNoDependencies,
            )
            service_a_2 = await scope_a.service_provider.get_keyed_service(
                service_key=service_key,
                service_type=ServiceWithNoDependencies,
            )

            service_b_1 = await scope_b.service_provider.get_keyed_service(
                service_key=service_key,
                service_type=ServiceWithNoDependencies,
            )
            service_b_2 = await scope_b.service_provider.get_keyed_service(
                service_key=service_key,
                service_type=ServiceWithNoDependencies,
            )

            assert service_a_1 is service_a_2
            assert service_b_1 is service_b_2
            assert service_a_1 is service_b_1
            assert service_a_2 is service_b_2

    async def test_resolve_keyed_scoped_service_from_scope_service_provider(
        self,
    ) -> None:
        service_key = "key"
        services = ServiceCollection()
        services.add_keyed_scoped(service_key, ServiceWithNoDependencies)

        async with (
            services.build_service_provider() as service_provider,
            (
                await service_provider.get_required_service(ServiceScopeFactory)
            ).create_scope() as scope_a,
            (
                await service_provider.get_required_service(ServiceScopeFactory)
            ).create_scope() as scope_b,
        ):
            assert (
                await scope_a.service_provider.get_service(ServiceWithNoDependencies)
                is None
            )
            assert (
                await scope_b.service_provider.get_service(ServiceWithNoDependencies)
                is None
            )

            with pytest.raises(KeyedServiceAnyKeyUsedToResolveServiceError):
                await scope_a.service_provider.get_keyed_service(
                    service_key=KeyedService.ANY_KEY,
                    service_type=ServiceWithNoDependencies,
                )

            with pytest.raises(KeyedServiceAnyKeyUsedToResolveServiceError):
                await scope_b.service_provider.get_keyed_service(
                    service_key=KeyedService.ANY_KEY,
                    service_type=ServiceWithNoDependencies,
                )

            service_a_1 = await scope_a.service_provider.get_keyed_service(
                service_key=service_key,
                service_type=ServiceWithNoDependencies,
            )
            service_a_2 = await scope_a.service_provider.get_keyed_service(
                service_key=service_key,
                service_type=ServiceWithNoDependencies,
            )

            service_b_1 = await scope_b.service_provider.get_keyed_service(
                service_key=service_key,
                service_type=ServiceWithNoDependencies,
            )
            service_b_2 = await scope_b.service_provider.get_keyed_service(
                service_key=service_key,
                service_type=ServiceWithNoDependencies,
            )

            assert service_a_1 is service_a_2
            assert service_b_1 is service_b_2
            assert service_a_1 is not service_b_1
            assert service_a_2 is not service_b_2

    async def test_resolve_keyed_transient_service_from_scope_service_provider(
        self,
    ) -> None:
        service_key = "key"
        services = ServiceCollection()
        services.add_keyed_transient(service_key, ServiceWithNoDependencies)

        async with (
            services.build_service_provider() as service_provider,
            (
                await service_provider.get_required_service(ServiceScopeFactory)
            ).create_scope() as scope_a,
            (
                await service_provider.get_required_service(ServiceScopeFactory)
            ).create_scope() as scope_b,
        ):
            assert (
                await scope_a.service_provider.get_service(ServiceWithNoDependencies)
                is None
            )
            assert (
                await scope_b.service_provider.get_service(ServiceWithNoDependencies)
                is None
            )

            with pytest.raises(KeyedServiceAnyKeyUsedToResolveServiceError):
                await scope_a.service_provider.get_keyed_service(
                    service_key=KeyedService.ANY_KEY,
                    service_type=ServiceWithNoDependencies,
                )

            with pytest.raises(KeyedServiceAnyKeyUsedToResolveServiceError):
                await scope_b.service_provider.get_keyed_service(
                    service_key=KeyedService.ANY_KEY,
                    service_type=ServiceWithNoDependencies,
                )

            service_a_1 = await scope_a.service_provider.get_keyed_service(
                service_key=service_key,
                service_type=ServiceWithNoDependencies,
            )
            service_a_2 = await scope_a.service_provider.get_keyed_service(
                service_key=service_key,
                service_type=ServiceWithNoDependencies,
            )

            service_b_1 = await scope_b.service_provider.get_keyed_service(
                service_key=service_key,
                service_type=ServiceWithNoDependencies,
            )
            service_b_2 = await scope_b.service_provider.get_keyed_service(
                service_key=service_key,
                service_type=ServiceWithNoDependencies,
            )

            assert service_a_1 is not service_a_2
            assert service_b_1 is not service_b_2
            assert service_a_1 is not service_b_1
            assert service_a_2 is not service_b_2
