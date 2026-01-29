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
from wirio.service_container import ServiceContainer


class TestServiceScopeFactory:
    async def test_resolve_service_scope_factory(self) -> None:
        services = ServiceContainer()

        async with services:
            service_scope_factory = await services.get(ServiceScopeFactory)

            assert isinstance(service_scope_factory, ServiceScopeFactory)

    async def test_service_scope_factory_is_singleton(self) -> None:
        services = ServiceContainer()

        async with services:
            scope_factory_1 = await services.get(ServiceScopeFactory)
            scope_factory_2 = await services.get(ServiceScopeFactory)

            async with services.create_scope() as service_scope:
                scope_factory_3 = await service_scope.services.get(ServiceScopeFactory)

                assert scope_factory_1 is scope_factory_2
                assert scope_factory_1 is scope_factory_3

    async def test_can_resolve_and_dispose_scoped_services_from_cached_scope_factory(
        self,
    ) -> None:
        services = ServiceContainer()
        services.add_scoped(ServiceWithAsyncContextManagerAndNoDependencies)

        async with services:
            cached_scope_factory = await services.get(ServiceScopeFactory)

            for _ in range(3):
                async with cached_scope_factory.create_scope() as outer_scope:
                    async with outer_scope.services.create_scope() as inner_scope:
                        outer_scoped_service = await outer_scope.services.try_get(
                            ServiceWithAsyncContextManagerAndNoDependencies
                        )
                        inner_scoped_service = await inner_scope.services.try_get(
                            ServiceWithAsyncContextManagerAndNoDependencies
                        )

                        assert outer_scoped_service is not None
                        assert inner_scoped_service is not None
                        assert outer_scoped_service is not inner_scoped_service

                    assert not outer_scoped_service.is_disposed
                    assert inner_scoped_service.is_disposed

                assert outer_scoped_service.is_disposed

    async def test_resolve_keyed_singleton_service_from_scope_service_container(
        self,
    ) -> None:
        service_key = "key"
        services = ServiceContainer()
        services.add_keyed_singleton(service_key, ServiceWithNoDependencies)

        async with (
            services,
            (await services.get(ServiceScopeFactory)).create_scope() as scope_a,
            (await services.get(ServiceScopeFactory)).create_scope() as scope_b,
        ):
            assert await scope_a.services.try_get(ServiceWithNoDependencies) is None
            assert await scope_b.services.try_get(ServiceWithNoDependencies) is None

            with pytest.raises(KeyedServiceAnyKeyUsedToResolveServiceError):
                await scope_a.services.try_get_keyed(
                    service_key=KeyedService.ANY_KEY,
                    service_type=ServiceWithNoDependencies,
                )

            with pytest.raises(KeyedServiceAnyKeyUsedToResolveServiceError):
                await scope_b.services.try_get_keyed(
                    service_key=KeyedService.ANY_KEY,
                    service_type=ServiceWithNoDependencies,
                )

            service_a_1 = await scope_a.services.try_get_keyed(
                service_key=service_key,
                service_type=ServiceWithNoDependencies,
            )
            service_a_2 = await scope_a.services.try_get_keyed(
                service_key=service_key,
                service_type=ServiceWithNoDependencies,
            )

            service_b_1 = await scope_b.services.try_get_keyed(
                service_key=service_key,
                service_type=ServiceWithNoDependencies,
            )
            service_b_2 = await scope_b.services.try_get_keyed(
                service_key=service_key,
                service_type=ServiceWithNoDependencies,
            )

            assert service_a_1 is service_a_2
            assert service_b_1 is service_b_2
            assert service_a_1 is service_b_1
            assert service_a_2 is service_b_2

    async def test_resolve_keyed_scoped_service_from_scope_service_container(
        self,
    ) -> None:
        service_key = "key"
        services = ServiceContainer()
        services.add_keyed_scoped(service_key, ServiceWithNoDependencies)

        async with (
            services,
            (await services.get(ServiceScopeFactory)).create_scope() as scope_a,
            (await services.get(ServiceScopeFactory)).create_scope() as scope_b,
        ):
            assert await scope_a.services.try_get(ServiceWithNoDependencies) is None
            assert await scope_b.services.try_get(ServiceWithNoDependencies) is None

            with pytest.raises(KeyedServiceAnyKeyUsedToResolveServiceError):
                await scope_a.services.try_get_keyed(
                    service_key=KeyedService.ANY_KEY,
                    service_type=ServiceWithNoDependencies,
                )

            with pytest.raises(KeyedServiceAnyKeyUsedToResolveServiceError):
                await scope_b.services.try_get_keyed(
                    service_key=KeyedService.ANY_KEY,
                    service_type=ServiceWithNoDependencies,
                )

            service_a_1 = await scope_a.services.try_get_keyed(
                service_key=service_key,
                service_type=ServiceWithNoDependencies,
            )
            service_a_2 = await scope_a.services.try_get_keyed(
                service_key=service_key,
                service_type=ServiceWithNoDependencies,
            )

            service_b_1 = await scope_b.services.try_get_keyed(
                service_key=service_key,
                service_type=ServiceWithNoDependencies,
            )
            service_b_2 = await scope_b.services.try_get_keyed(
                service_key=service_key,
                service_type=ServiceWithNoDependencies,
            )

            assert service_a_1 is service_a_2
            assert service_b_1 is service_b_2
            assert service_a_1 is not service_b_1
            assert service_a_2 is not service_b_2

    async def test_resolve_keyed_transient_service_from_scope_service_container(
        self,
    ) -> None:
        service_key = "key"
        services = ServiceContainer()
        services.add_keyed_transient(service_key, ServiceWithNoDependencies)

        async with (
            services,
            (await services.get(ServiceScopeFactory)).create_scope() as scope_a,
            (await services.get(ServiceScopeFactory)).create_scope() as scope_b,
        ):
            assert await scope_a.services.try_get(ServiceWithNoDependencies) is None
            assert await scope_b.services.try_get(ServiceWithNoDependencies) is None

            with pytest.raises(KeyedServiceAnyKeyUsedToResolveServiceError):
                await scope_a.services.try_get_keyed(
                    service_key=KeyedService.ANY_KEY,
                    service_type=ServiceWithNoDependencies,
                )

            with pytest.raises(KeyedServiceAnyKeyUsedToResolveServiceError):
                await scope_b.services.try_get_keyed(
                    service_key=KeyedService.ANY_KEY,
                    service_type=ServiceWithNoDependencies,
                )

            service_a_1 = await scope_a.services.try_get_keyed(
                service_key=service_key,
                service_type=ServiceWithNoDependencies,
            )
            service_a_2 = await scope_a.services.try_get_keyed(
                service_key=service_key,
                service_type=ServiceWithNoDependencies,
            )

            service_b_1 = await scope_b.services.try_get_keyed(
                service_key=service_key,
                service_type=ServiceWithNoDependencies,
            )
            service_b_2 = await scope_b.services.try_get_keyed(
                service_key=service_key,
                service_type=ServiceWithNoDependencies,
            )

            assert service_a_1 is not service_a_2
            assert service_b_1 is not service_b_2
            assert service_a_1 is not service_b_1
            assert service_a_2 is not service_b_2
