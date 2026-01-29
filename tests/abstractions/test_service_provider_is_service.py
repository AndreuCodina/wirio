from aspy_dependency_injection.abstractions.base_service_provider import (
    BaseServiceProvider,
)
from aspy_dependency_injection.abstractions.service_provider_is_keyed_service import (
    ServiceProviderIsKeyedService,
)
from aspy_dependency_injection.abstractions.service_provider_is_service import (
    ServiceProviderIsService,
)
from aspy_dependency_injection.abstractions.service_scope_factory import (
    ServiceScopeFactory,
)
from aspy_dependency_injection.service_collection import ServiceCollection
from tests.utils.services import ServiceWithNoDependencies


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
