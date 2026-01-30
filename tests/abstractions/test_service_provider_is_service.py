from tests.utils.services import ServiceWithNoDependencies
from wirio.abstractions.service_provider_is_keyed_service import (
    ServiceProviderIsKeyedService,
)
from wirio.abstractions.service_provider_is_service import (
    ServiceProviderIsService,
)
from wirio.abstractions.service_scope_factory import (
    ServiceScopeFactory,
)
from wirio.base_service_provider import BaseServiceProvider
from wirio.service_collection import ServiceCollection


class TestServiceProviderIsService:
    async def test_resolve_service_provider_is_service(self) -> None:
        services = ServiceCollection()

        async with services.build_service_provider() as service_provider:
            service_provider_is_service = await service_provider.get_required_service(
                ServiceProviderIsService
            )

            assert isinstance(service_provider_is_service, ServiceProviderIsService)

    async def test_built_in_services_with_is_service_returns_true(
        self,
    ) -> None:
        services = ServiceCollection()
        services.add_transient(ServiceWithNoDependencies)

        async with services.build_service_provider() as service_provider:
            service_provider_is_service = await service_provider.get_required_service(
                ServiceProviderIsService
            )

            assert service_provider_is_service.is_service(BaseServiceProvider)
            assert service_provider_is_service.is_service(ServiceScopeFactory)
            assert service_provider_is_service.is_service(ServiceProviderIsService)
            assert service_provider_is_service.is_service(ServiceProviderIsKeyedService)
