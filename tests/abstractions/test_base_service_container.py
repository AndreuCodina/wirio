from wirio.base_service_container import BaseServiceContainer
from wirio.service_container import ServiceContainer


class TestBaseServiceContainer:
    async def test_resolve_base_service_container(self) -> None:
        service_container = ServiceContainer()

        async with service_container:
            base_service_container = await service_container.get(BaseServiceContainer)

            assert isinstance(base_service_container, BaseServiceContainer)
