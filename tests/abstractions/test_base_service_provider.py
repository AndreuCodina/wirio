from wirio.abstractions.base_service_provider import BaseServiceProvider
from wirio.service_collection import ServiceCollection


class TestBaseServiceProvider:
    async def test_resolve_base_service_provider(self) -> None:
        services = ServiceCollection()

        async with services.build_service_provider() as service_provider:
            base_service_provider = await service_provider.get_required_service(
                BaseServiceProvider
            )

            assert isinstance(base_service_provider, BaseServiceProvider)
