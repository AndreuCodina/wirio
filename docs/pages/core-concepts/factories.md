# Factories

## Overview

Sometimes, we need to use a factory function to create a service. For example, we have settings (a connection string, database name, etc.) stored using the package `pydantic-settings` and we want to provide them to a service `DatabaseClient` to access a database.

```python
class ApplicationSettings(BaseSettings):
    database_connection_string: str


class DatabaseClient:
    def __init__(self, connection_string: str) -> None:
        pass
```

In a real `DatabaseClient` implementation, we must use a sync or async context manager, i.e., we instance it with:

```python
async with DatabaseClient(database_connection_string) as client:
    ...
```

And, if we want to reuse it, we create a factory function with yield:

```python
async def create_database_client(application_settings: ApplicationSettings) -> AsyncGenerator[DatabaseClient]:
    async with DatabaseClient(application_settings.database_connection_string) as database_client:
        yield database_client
```

With that factory, we have to provide manually a singleton of `ApplicationSettings`, and to know if `DatabaseClient` implements a sync or async context manager, or neither. Apart from that, if we need a singleton or scoped instance of `DatabaseClient`, it's very complex to manage the disposal of the instance.

Then, why don't just return it? With this package, we just have this:

```python
def inject_database_client(application_settings: ApplicationSettings) -> DatabaseClient:
    return DatabaseClient(
        connection_string=application_settings.database_connection_string
    )

services.add_transient(inject_database_client)
```

The factories can take as parameters other services registered. In this case, `inject_database_client` takes `ApplicationSettings` as a parameter, and the dependency injection mechanism will resolve it automatically.

## Generator factories

As we have seen, we don't need the boilerplate of creating generator factories, but in order to support the edge case you want to use a library with custom methods instead of context manager support, you also can do it with Wirio.

```python
async def inject_database_client(application_settings: ApplicationSettings) -> AsyncGenerator[DatabaseClient]:
    try:
        database_client = DatabaseClient(application_settings.database_connection_string)
        await database_client.connect()
    finally:
        await database_client.aclose()


services.add_transient(inject_database_client)
```
