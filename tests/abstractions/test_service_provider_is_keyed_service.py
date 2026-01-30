from wirio.abstractions.service_provider_is_keyed_service import (
    ServiceProviderIsKeyedService,
)
from wirio.service_collection import ServiceCollection


class TestServiceProviderIsKeyedService:
    async def test_resolve_service_provider_is_keyed_service(self) -> None:
        services = ServiceCollection()

        async with services.build_service_provider() as service_provider:
            service_provider_is_keyed_service = (
                await service_provider.get_required_service(
                    ServiceProviderIsKeyedService
                )
            )

            assert isinstance(
                service_provider_is_keyed_service, ServiceProviderIsKeyedService
            )
