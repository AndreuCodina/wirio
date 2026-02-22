# Factories

## Quickstart

Sometimes, a service cannot be created automatically. For example, consider `DatabaseClient`, which requires a connection string:

```python
class DatabaseClient:
    def __init__(self, connection_string: str) -> None:
        pass
```

`str` is too generic to register as a service. We could have other strings registered (e.g., API URL, logging level, service bus queue), and it wouldn't be clear which string is the connection string.

The connection string could come from anywhere: an environment variable, a config file, a secrets manager, etc.

Let's say we want to get the connection string from an environment variable. We can create a factory function that reads the environment variable and returns `DatabaseClient`, the service we want to register, and then we can register that factory as a service:

```python
def inject_database_client() -> DatabaseClient:
    return DatabaseClient(
        connection_string=os.environ["DATABASE_CONNECTION_STRING"]
    )

services.add_transient(inject_database_client)
```

Wirio will automatically resolve the dependencies of the factory (in this case, none, because the factory has no parameters) and use the returned type (`DatabaseClient`) as the service type to register.

!!! note "Note"

    The factory can be async if we need to perform asynchronous operations during service creation, such as fetching secrets or performing I/O operations.

## Dependencies

We've seen that we can register services by providing a factory, but what if our factory needs dependencies itself? No problem! Just add them as parameters to the factory, and Wirio will resolve them for us.

For example, the typical approach to manage settings is to centralize them in an `ApplicationSettings` class, which we register as a singleton service:

```python
from pydantic_settings import BaseSettings


class ApplicationSettings(BaseSettings):
    database_connection_string: str

services.add_singleton(ApplicationSettings, ApplicationSettings())
```

Then, we can inject `ApplicationSettings` into our factory to create the `DatabaseClient`:

```python
def inject_database_client(application_settings: ApplicationSettings) -> DatabaseClient:
    return DatabaseClient(
        connection_string=application_settings.database_connection_string
    )

services.add_transient(inject_database_client)
```

## Generator factories

Wirio is smart and doesn't need the boilerplate of creating generator factories, but in order to support the edge case where we want to use a library that provides custom methods instead of context manager support, Wirio can handle that as well.

```python
async def inject_database_client(application_settings: ApplicationSettings) -> AsyncGenerator[DatabaseClient]:
    database_client = DatabaseClient(application_settings.database_connection_string)

    try:
        await database_client.connect()
        yield database_client
    finally:
        await database_client.aclose()


services.add_transient(inject_database_client)
```
