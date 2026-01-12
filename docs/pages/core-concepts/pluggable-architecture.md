# Pluggable architecture

**Aspy Dependency Injection** follows the same extension-friendly design that ASP.NET Core popularized. Rather than hiding registrations behind a monolithic container, the library exposes the `ServiceCollection` and encourages features to be layered through small, self-contained modules. This lets applications opt into only the capabilities they need while keeping configurations declarative and easy to reason about.

## Service Collection as the Composition Root

- `ServiceCollection` is the single aggregation point for all services. Each feature contributes registrations by receiving an instance of the collection and calling standard helpers.
- The resulting graph is immutable once `build_service_provider()` is invoked, ensuring the runtime container is predictable and thread-safe.
- Because everything flows through the collection, reusable packages can add services without assuming how the host application instantiates the provider.

## Extension modules (`add_*` helpers)

You, or the own libraries you use, can provide functions that accept a `ServiceCollection` and register the required services. For example, a logging package might expose an `add_logging` function, providing good defaults and injectable services:

```python
def add_logging(services: ServiceCollection) -> ServiceCollection:
	services.add_singleton(LoggerFactory, DefaultLoggerFactory)
	services.add_transient(Logger)
	return services
```

Similarly, an observability package could offer an `add_observability` function:

```python
def add_observability(services: ServiceCollection) -> ServiceCollection:
	services.add_singleton(MetricsClient, PrometheusMetricsClient)
	services.add_singleton(Tracer, OtelTracer)
	return services
```

A database integration package might provide an `add_sqlmodel` function that sets up SQLModel, so all the typical boilerplate is handled for you with just a single line of code:

```python
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from aspy_dependency_injection.service_collection import ServiceCollection

services = ServiceCollection()


def add_sqlmodel(services: ServiceCollection, connection_string: str) -> None:
    def inject_async_engine() -> AsyncEngine:
        return create_async_engine(connection_string)

    def inject_async_sessionmaker(
        async_engine: AsyncEngine,
    ) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(
            async_engine, class_=AsyncSession, expire_on_commit=False
        )

    def inject_async_session(
        async_sessionmaker: async_sessionmaker[AsyncSession],
    ) -> AsyncSession:
        return async_sessionmaker()

    services.add_singleton(inject_async_engine)
    services.add_singleton(inject_async_sessionmaker)
    services.add_transient(inject_async_session)
```

And then your `main.py` would be:

```python
services = ServiceCollection()
add_logging(services)
add_observability(services)
add_sqlmodel(services, connection_string="...")
```

In a real application, you might have:

```python
services = ServiceCollection()
application_settings = ApplicationSettings()
services.add_singleton(ApplicationSettings, application_settings)
add_logging(services)
add_observability(services)
add_sqlmodel(
    services,
    connection_string=application_settings.database_connection_string,
)
```

## Why not a Container subclass?

Other libraries embrace a container-class API: you extend a `Container`, override methods, or mutate attributes to register services. That style works, but it comes with trade-offs that `Aspy Dependency Injection` intentionally avoids:

- **Interoperability:** Both approaches technically work across frameworks, but the collection style keeps things primitive—just create an instance and start registering. Container subclasses introduce class-level state, overridden hooks, and metaclass magic that become friction points when you try to share the same container between, say, a CLI bootstrapper and an async worker, or application code and test cases.
- **Composability:** Collection-first helpers (`add_logging`, `add_sqlmodel`, etc.) compose like ordinary functions. Container subclasses tend to accumulate registration logic across inheritance hierarchies, making it harder to cherry-pick modules or share them between apps.
- **Predictability:** Once `build_service_provider()` runs, the provider is sealed. Container-class APIs often allow late mutation or rely on attribute access magic, which can hide ordering bugs.
- **Testability:** Tests can spin up a fresh `ServiceCollection`, register fakes, and build a provider in a few lines. When registrations sit inside container subclasses, swapping implementations usually means subclassing again or using custom hooks.

In short, the ServiceCollection model mirrors ASP.NET Core’s ergonomics while staying idiomatic to Python: no inheritance requirements, just functional building blocks you can plug together as needed.

### How to Structure Feature Packages

1. **Expose a single public entry point** (for example, `def add_feature(services: ServiceCollection, **options) -> ServiceCollection`).
2. **Register abstractions, not concrete types.** Use interfaces or protocols in shared libraries so consumers can replace implementations when needed.
3. **Keep configuration explicit.** Pass options via parameters or small dataclasses instead of global state.
4. **Document prerequisites.** If `add_sqlmodel` expects a configured `Engine`, accept it as a parameter or register a factory that builds one from provided settings.

## Putting It Together

The end result is a plug-and-play ecosystem: logging, observability, data stores, caching, and custom application modules all plug into `ServiceCollection` the same way. This symmetry makes it trivial to port patterns from ASP.NET Core DI, reuse mental models, and share modules across Python services that embrace the dependency injection container.