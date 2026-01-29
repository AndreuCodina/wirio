from wirio.abstractions.service_container_is_keyed_service import (
    ServiceContainerIsKeyedService,
)
from wirio.service_container import ServiceContainer


class TestServiceProviderIsKeyedService:
    async def test_resolve_service_container_is_keyed_service(self) -> None:
        services = ServiceContainer()

        async with services:
            service_scope_factory = await services.get(ServiceContainerIsKeyedService)

            assert isinstance(service_scope_factory, ServiceContainerIsKeyedService)
