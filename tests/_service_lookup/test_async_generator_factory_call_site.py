from collections.abc import AsyncGenerator

from tests.utils.services import ServiceWithNoDependencies
from wirio._service_lookup._async_generator_factory_call_site import (
    AsyncGeneratorFactoryCallSite,
)
from wirio._service_lookup._result_cache import ResultCache
from wirio._service_lookup._typed_type import TypedType


class TestAsyncGeneratorFactoryCallSite:
    def test_return_service_type(self) -> None:
        async def implementation_factory() -> AsyncGenerator[object]:
            yield object()

        service_type = TypedType.from_type(ServiceWithNoDependencies)
        cache = ResultCache.none(service_type)
        call_site = AsyncGeneratorFactoryCallSite.from_implementation_factory(
            cache=cache,
            service_type=service_type,
            implementation_factory=implementation_factory,
        )

        assert call_site.service_type is service_type
