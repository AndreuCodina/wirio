from tests.utils.services import ServiceWithNoDependencies
from wirio.abstractions.service_container_is_keyed_service import (
    ServiceContainerIsKeyedService,
)
from wirio.abstractions.service_container_is_service import (
    ServiceContainerIsService,
)
from wirio.abstractions.service_scope_factory import (
    ServiceScopeFactory,
)
from wirio.base_service_container import BaseServiceContainer
from wirio.service_container import ServiceContainer


class TestServiceContainerIsService:
    async def test_resolve_service_container_is_service(self) -> None:
        services = ServiceContainer()

        async with services:
            service_container_is_service = await services.get(ServiceContainerIsService)

            assert isinstance(service_container_is_service, ServiceContainerIsService)

    async def test_built_in_services_with_is_service_returns_true(
        self,
    ) -> None:
        services = ServiceContainer()
        services.add_transient(ServiceWithNoDependencies)

        async with services:
            service_container_is_service = await services.get(ServiceContainerIsService)

            assert service_container_is_service.is_service(BaseServiceContainer)
            assert service_container_is_service.is_service(ServiceScopeFactory)
            assert service_container_is_service.is_service(ServiceContainerIsService)
            assert service_container_is_service.is_service(
                ServiceContainerIsKeyedService
            )
