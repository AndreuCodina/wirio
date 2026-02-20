from collections.abc import Generator

from tests.utils.services import ServiceWithNoDependencies
from wirio._service_lookup._result_cache import ResultCache
from wirio._service_lookup._sync_generator_factory_call_site import (
    SyncGeneratorFactoryCallSite,
)
from wirio._service_lookup._typed_type import TypedType


class TestSyncGeneratorFactoryCallSite:
    def test_return_service_type(self) -> None:
        def implementation_factory() -> Generator[object]:
            yield object()

        service_type = TypedType.from_type(ServiceWithNoDependencies)
        cache = ResultCache.none(service_type)
        call_site = SyncGeneratorFactoryCallSite.from_implementation_factory(
            cache=cache,
            service_type=service_type,
            implementation_factory=implementation_factory,
        )

        assert call_site.service_type is service_type
