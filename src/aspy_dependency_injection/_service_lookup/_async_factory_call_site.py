from typing import TYPE_CHECKING, Final, final, override

from aspy_dependency_injection._service_lookup._call_site_kind import CallSiteKind
from aspy_dependency_injection._service_lookup._service_call_site import ServiceCallSite

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aspy_dependency_injection._service_lookup._result_cache import ResultCache
    from aspy_dependency_injection._service_lookup._typed_type import TypedType


@final
class AsyncFactoryCallSite(ServiceCallSite):
    _service_type: Final[TypedType]
    _implementation_factory: Final[Callable[..., Awaitable[object]]]

    def __init__(
        self,
        cache: ResultCache,
        service_type: TypedType,
        implementation_factory: Callable[..., Awaitable[object]],
    ) -> None:
        super().__init__(cache)
        self._service_type = service_type
        self._implementation_factory = implementation_factory

    @property
    @override
    def service_type(self) -> TypedType:
        return self._service_type

    @property
    @override
    def kind(self) -> CallSiteKind:
        return CallSiteKind.ASYNC_FACTORY

    @property
    def implementation_factory(
        self,
    ) -> Callable[..., Awaitable[object]]:
        return self._implementation_factory
