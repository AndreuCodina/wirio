# Configuration

Wirio includes a built-in configuration system.

It loads environment variables as a configuration source.

## Quickstart

Define a settings model and read it from `services.configuration`:

```python
from pydantic import BaseModel
from wirio.service_collection import ServiceCollection


class ApplicationSettings(BaseModel):
    app_name: str
    port: int


services = ServiceCollection()
settings = services.configuration[ApplicationSettings]
```

Wirio maps model field names to configuration keys using snake case conventions.

For example, the `APP_NAME` environment variable is read as `app_name`.

## Defaults and required values

When building a settings model, if a field has a default value, that default is used when no value is found.

```python
from pydantic import BaseModel


class ApplicationSettings(BaseModel):
    app_name: str
    port: int | None = None
```

In this example, `port` defaults to `None` when not present.

## Source precedence

`ConfigurationManager` supports multiple sources, and the last added source has priority. This is because some sources should have priority over others. For example, we may want to load configuration from a file first and then override specific values with environment variables.

This also allows us to load base configuration first and override specific values later (for example, in tests or per environment).

## Accessing configuration in factories

A common pattern is reading typed settings inside a service factory:

```python
from pydantic import BaseModel
from wirio.service_collection import ServiceCollection


class ApplicationSettings(BaseModel):
    database_connection_string: str


class DatabaseClient:
    def __init__(self, connection_string: str) -> None:
        self.connection_string = connection_string


services = ServiceCollection()


def inject_database_client() -> DatabaseClient:
    settings = services.configuration[ApplicationSettings]
    return DatabaseClient(settings.database_connection_string)


services.add_singleton(inject_database_client)
```
