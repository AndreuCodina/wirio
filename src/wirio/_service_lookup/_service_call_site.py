from abc import ABC, abstractmethod

from wirio._service_lookup._asyncio_reentrant_lock import AsyncioReentrantLock
from wirio._service_lookup._call_site_kind import CallSiteKind
from wirio._service_lookup._result_cache import ResultCache
from wirio._service_lookup._typed_type import TypedType


class ServiceCallSite(ABC):
    """Representation of how a service must be created."""

    _cache: ResultCache
    _value: object | None
    _key: object | None
    _lock: AsyncioReentrantLock

    def __init__(
        self, cache: ResultCache, key: object | None, value: object | None = None
    ) -> None:
        self._cache = cache
        self._key = key
        self._value = value
        self._lock = AsyncioReentrantLock()

    @property
    def cache(self) -> ResultCache:
        return self._cache

    @property
    def key(self) -> object | None:
        return self._key

    @property
    def value(self) -> object | None:
        return self._value

    @value.setter
    def value(self, value: object | None) -> None:
        self._value = value

    @property
    def lock(self) -> AsyncioReentrantLock:
        return self._lock

    @property
    @abstractmethod
    def service_type(self) -> TypedType: ...

    @property
    @abstractmethod
    def kind(self) -> CallSiteKind: ...
