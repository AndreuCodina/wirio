# Async-first design

## Issue to solve

Using libraries with IO operations (databases, files, LLMs, HTTP...), we can encounter several cases:

- Libraries that provide both synchronous and asynchronous APIs, and we have to find out which one to use.
- Libraries that are synchronous, having to use `asyncio.to_thread` or similar techniques to run them without blocking the event loop.
- Libraries that are asynchronous.

Using synchronous IO code blocks the event loop, leading to performance issues and a poor user experience.

Regarding the use of those libraries, we need to know whether we need to use an async context manager, a sync context manager, or no context manager at all. This adds cognitive load and increases the chances of making mistakes.

## Why a synchronous design is not enough

We can add synchronous services to a synchronous dependency injection library, but at the moment we need to add asynchronous services, they'll crash because they can't be instantiated correctly (`__aenter__`) or we'll need to use workarounds such as creating a thread to run async code, which adds performance overhead and complexity.

At the end, if a dependency injection library is not async-first, in order to support sync and async code, it'll introduce performance issues or duplicate the codebase (async must be propagated, and the locking mechanisms and logic change).

So, if we want a dependency injection library that works well with async code and can resolve both synchronous and asynchronous, it must be designed with async in mind from the beginning.

## Aspy Dependency Injection's async-first design

`Aspy Dependency Injection` is designed to be async-first, meaning that it can handle both synchronous and asynchronous services seamlessly.
