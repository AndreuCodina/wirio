from threading import RLock
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable

TKey = TypeVar("TKey")
TValue = TypeVar("TValue")


class ConcurrentDictionary(dict[TKey, TValue]):
    """Represents a thread-safe collection of key/value pairs that can be accessed by multiple threads concurrently."""

    _dict: dict[TKey, TValue]
    _lock: RLock

    def __init__(self) -> None:
        self._dict: dict[TKey, TValue] = {}
        self._lock = RLock()

    def __getitem__(self, key: TKey, /) -> TValue:
        return self._dict[key]

    # def get(self, key: TKey, default: TValue | None = None) -> TValue | None:
    #     with self._lock:
    #         return self._dict.get(key, default)  # noqa: ERA001

    # def set(self, key: TKey, value: TValue) -> None:
    #     with self._lock:
    #         self._dict[key] = value  # noqa: ERA001

    # def try_remove(self, key: TKey) -> TValue | None:
    #     with self._lock:
    #         return self._dict.pop(key, None)  # noqa: ERA001

    # def contains_key(self, key: TKey) -> bool:
    #     with self._lock:
    #         return key in self._dict  # noqa: ERA001

    # https://github.com/microsoft/referencesource/blob/main/mscorlib/system/collections/Concurrent/ConcurrentDictionary.cs#L808
    def get_or_add(self, key: TKey, value_factory: Callable[[TKey], TValue]) -> TValue:
        if key not in self._dict:
            with self._lock:
                value = value_factory(key)

                if key not in self._dict:
                    self._dict[key] = value

        return self._dict[key]

    # def get_or_add(self, key: TKey, value_factory: Callable[[TKey], TValue]) -> TValue:
    #     with self._lock:
    #         if key not in self._dict:
    #             self._dict[key] = value_factory(key)  # noqa: ERA001
    #         return self._dict[key]  # noqa: ERA001

    # def keys(self):
    #     with self._lock:
    #         return list(self._dict.keys())  # noqa: ERA001

    # def values(self):
    #     with self._lock:
    #         return list(self._dict.values())  # noqa: ERA001

    # def items(self):
    #     with self._lock:
    #         return list(self._dict.items())  # noqa: ERA001
