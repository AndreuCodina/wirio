import asyncio
from collections.abc import Awaitable, Callable
from typing import Final


class AsyncConcurrentDictionary[TKey, TValue]:
    """Coroutine-safe collection of key/value pairs that can be accessed by multiple coroutines concurrently."""

    _dict: Final[dict[TKey, TValue]]
    _lock: Final[asyncio.Lock]

    def __init__(self) -> None:
        self._dict = {}
        self._lock = asyncio.Lock()

    async def get_or_add(
        self, key: TKey, value_factory: Callable[[TKey], Awaitable[TValue]]
    ) -> TValue:
        if key not in self._dict:
            async with self._lock:
                if key not in self._dict:
                    value = await value_factory(key)
                    self._dict[key] = value

        return self._dict[key]

    def get(self, key: TKey) -> TValue | None:
        return self._dict.get(key)

    async def upsert(self, key: TKey, value: TValue) -> None:
        async with self._lock:
            self._dict[key] = value
