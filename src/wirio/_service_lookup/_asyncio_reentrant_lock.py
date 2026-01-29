# MIT License

# Copyright (c) 2023 Joshua George Albert
# Copyright (c) 2026 Andreu Codina

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# https://github.com/Joshuaalbert/FairAsyncRLock

import asyncio
from asyncio import CancelledError, Event, Task
from collections import deque
from contextlib import AbstractAsyncContextManager
from types import TracebackType
from typing import Any, Self, override


class AsyncioReentrantLock(AbstractAsyncContextManager["AsyncioReentrantLock"]):
    _owner: Task[Any] | None
    _count: int
    _owner_transfer: bool
    _queue: deque[Event]

    def __init__(self) -> None:
        self._owner = None
        self._count = 0
        self._owner_transfer = False
        self._queue = deque()

    @property
    def owner(self) -> Task[Any] | None:
        return self._owner

    @property
    def count(self) -> int:
        return self._count

    @property
    def queue(self) -> deque[Event]:
        return self._queue

    @property
    def is_locked(self) -> bool:
        return self._owner is not None

    def is_owner(self, task: Task[Any] | None = None) -> bool:
        if task is None:
            task = asyncio.current_task()

        return self._owner == task

    async def acquire(self) -> None:
        current_task = asyncio.current_task()

        # If the lock is reentrant, acquire it immediately
        if self.is_owner(task=current_task):
            self._count += 1
            return

        # If the lock is free (and ownership not in midst of transfer), acquire it immediately
        if self._count == 0 and not self._owner_transfer:
            self._owner = current_task
            self._count = 1
            return

        # Create an event for this task, to notify when it's ready for acquire
        event = Event()
        self._queue.append(event)

        # Wait for the lock to be free, then acquire
        try:
            await event.wait()
            self._owner_transfer = False
            self._owner = current_task
            self._count = 1
        except CancelledError:
            try:
                # If in queue, then cancelled before release
                self._queue.remove(event)
            except ValueError:
                # Otherwise, release happened, this was next, and we simulate passing on
                self._owner_transfer = False
                self._owner = current_task
                self._count = 1
                self._current_task_release()
            raise

    def _current_task_release(self) -> None:
        self._count -= 1
        if self._count == 0:
            self._owner = None

            if self._queue:
                # Wake up the next task in the queue
                event = self._queue.popleft()
                event.set()

                # Setting this here prevents another task getting lock until owner transfer
                self._owner_transfer = True

    def release(self) -> None:
        """Release the lock."""
        current_task = asyncio.current_task()

        if self._owner is None:
            error_message = (
                f"Cannot release un-acquired lock. {current_task} tried to release."
            )
            raise RuntimeError(error_message)

        if not self.is_owner(task=current_task):
            error_message = f"Cannot release foreign lock. {current_task} tried to unlock {self._owner}."
            raise RuntimeError(error_message)

        self._current_task_release()

    @override
    async def __aenter__(self) -> Self:
        await self.acquire()
        return self

    @override
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        self.release()
