from typing import TYPE_CHECKING, Final, final, override

from aspy_dependency_injection._service_lookup._call_site_kind import CallSiteKind
from aspy_dependency_injection._service_lookup._service_call_site import ServiceCallSite

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aspy_dependency_injection._service_lookup._result_cache import ResultCache
    from aspy_dependency_injection.abstractions.service_provider import ServiceProvider


@final
class AsyncFactoryCallSite(ServiceCallSite):
    _cache: Final[ResultCache]
    _service_type: Final[type]
    _implementation_factory: Final[Callable[[ServiceProvider], Awaitable[object]]]

    def __init__(
        self,
        cache: ResultCache,
        service_type: type,
        implementation_factory: Callable[[ServiceProvider], Awaitable[object]],
    ) -> None:
        self._cache = cache
        self._service_type = service_type
        self._implementation_factory = implementation_factory

    @property
    def cache(self) -> ResultCache:
        return self._cache

    @property
    @override
    def service_type(self) -> type:
        return self._service_type

    @property
    @override
    def kind(self) -> CallSiteKind:
        return CallSiteKind.ASYNC_FACTORY

    @property
    def implementation_factory(self) -> Callable[[ServiceProvider], Awaitable[object]]:
        return self._implementation_factory
