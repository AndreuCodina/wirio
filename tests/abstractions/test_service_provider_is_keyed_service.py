from aspy_dependency_injection.abstractions.service_provider_is_keyed_service import (
    ServiceProviderIsKeyedService,
)
from aspy_dependency_injection.service_collection import ServiceCollection


class TestServiceProviderIsKeyedService:
    async def test_resolve_service_provider_is_keyed_service(self) -> None:
        services = ServiceCollection()

        async with services.build_service_provider() as service_provider:
            service_scope_factory = await service_provider.get_required_service(
                ServiceProviderIsKeyedService
            )

            assert isinstance(service_scope_factory, ServiceProviderIsKeyedService)
