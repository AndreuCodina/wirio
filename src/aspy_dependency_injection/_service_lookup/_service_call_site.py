import asyncio
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aspy_dependency_injection._service_lookup._call_site_kind import CallSiteKind
    from aspy_dependency_injection._service_lookup._result_cache import ResultCache
    from aspy_dependency_injection._service_lookup._typed_type import TypedType


class ServiceCallSite(ABC):
    """Representation of how a service must be created."""

    _cache: ResultCache
    _value: object | None
    _lock: asyncio.Lock

    def __init__(self, cache: ResultCache) -> None:
        self._cache = cache
        self._value = None
        self._lock = asyncio.Lock()

    @property
    def cache(self) -> ResultCache:
        return self._cache

    @property
    def value(self) -> object | None:
        return None

    @value.setter
    def value(self, value: object | None) -> None:
        self._value = value

    @property
    def lock(self) -> asyncio.Lock:
        return self._lock

    @property
    @abstractmethod
    def service_type(self) -> TypedType: ...

    @property
    @abstractmethod
    def kind(self) -> CallSiteKind: ...
