# Factories

Sometimes, you need to use a factory function to create a service. For example, you have settings (a connection string, database name, etc.) stored using the package `pydantic-settings` and you want to provide them to a service `DatabaseClient` to access a database.

```python
class ApplicationSettings(BaseSettings):
    database_connection_string: str


class DatabaseClient:
    def __init__(self, connection_string: str) -> None:
        pass
```

In a real `DatabaseClient` implementation, you must use a sync or async context manager, i.e., you instance it with:

```python
async with DatabaseClient(database_connection_string) as client:
    ...
```

And, if you want to reuse it, you create a factory function with yield:

```python
async def create_database_client(application_settings: ApplicationSettings) -> AsyncGenerator[DatabaseClient]:
    async with DatabaseClient(application_settings.database_connection_string) as database_client:
        yield database_client
```

With that factory, you have to provide manually a singleton of `ApplicationSettings`, and to know if `DatabaseClient` implements a sync or async context manager, or neither. Apart from that, if you need a singleton or scoped instance of `DatabaseClient`, it's very complex to manage the disposal of the instance.

Then, why don't just return it? With this package, you just have this:

```python
def inject_database_client(application_settings: ApplicationSettings) -> DatabaseClient:
    return DatabaseClient(
        connection_string=application_settings.database_connection_string
    )

services.add_transient(inject_database_client)
```

The factories can take as parameters other services registered. In this case, `inject_database_client` takes `ApplicationSettings` as a parameter, and the dependency injection mechanism will resolve it automatically.