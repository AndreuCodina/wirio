from collections.abc import Callable
from functools import partial
from typing import Final, final, override

from aspy_dependency_injection._aspy_undefined import AspyUndefined
from aspy_dependency_injection._service_lookup._call_site_kind import CallSiteKind
from aspy_dependency_injection._service_lookup._result_cache import ResultCache
from aspy_dependency_injection._service_lookup._service_call_site import ServiceCallSite
from aspy_dependency_injection._service_lookup._typed_type import TypedType


@final
class SyncFactoryCallSite(ServiceCallSite):
    _service_type: Final[TypedType]
    _implementation_factory: Callable[..., object]

    def __init__(
        self,
        cache: ResultCache,
        service_type: TypedType,
        service_key: object | None = AspyUndefined.INSTANCE,
    ) -> None:
        is_keyed_implementation_factory = service_key is not AspyUndefined.INSTANCE
        service_key_to_add = service_key if is_keyed_implementation_factory else None
        super().__init__(cache=cache, key=service_key_to_add)
        self._service_type = service_type

    @classmethod
    def from_implementation_factory(
        cls,
        cache: ResultCache,
        service_type: TypedType,
        implementation_factory: Callable[..., object],
    ) -> "SyncFactoryCallSite":
        self = cls(cache=cache, service_type=service_type)
        self._implementation_factory = implementation_factory
        return self

    @classmethod
    def from_keyed_implementation_factory(
        cls,
        cache: ResultCache,
        service_type: TypedType,
        implementation_factory: Callable[..., object],
        service_key: object | None,
    ) -> "SyncFactoryCallSite":
        self = cls(cache=cache, service_type=service_type, service_key=service_key)
        self._implementation_factory = partial(implementation_factory, service_key)
        return self

    @property
    @override
    def service_type(self) -> TypedType:
        return self._service_type

    @property
    @override
    def kind(self) -> CallSiteKind:
        return CallSiteKind.SYNC_FACTORY

    @property
    def implementation_factory(self) -> Callable[..., object]:
        return self._implementation_factory
