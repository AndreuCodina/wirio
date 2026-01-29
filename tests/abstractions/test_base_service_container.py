from wirio.base_service_container import BaseServiceContainer
from wirio.service_container import ServiceContainer


class TestBaseServiceContainer:
    async def test_resolve_base_service_container(self) -> None:
        services = ServiceContainer()

        async with services:
            base_service_container = await services.get(BaseServiceContainer)

            assert isinstance(base_service_container, BaseServiceContainer)
