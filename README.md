<div align="center">
<img alt="Logo" src="https://raw.githubusercontent.com/AndreuCodina/wirio/refs/heads/main/docs/logo.png" width="522" height="348">

[![CI](https://img.shields.io/github/actions/workflow/status/AndreuCodina/wirio/main.yaml?branch=main&logo=github&label=CI)](https://github.com/AndreuCodina/wirio/actions/workflows/main.yaml)
[![Coverage status](https://coveralls.io/repos/github/AndreuCodina/wirio/badge.svg?branch=main)](https://coveralls.io/github/AndreuCodina/wirio?branch=main)
[![PyPI - version](https://img.shields.io/pypi/v/wirio?color=blue&label=pypi)](https://pypi.org/project/wirio/)
[![Python - versions](https://img.shields.io/pypi/pyversions/wirio.svg)](https://github.com/AndreuCodina/wirio)
[![License](https://img.shields.io/github/license/AndreuCodina/wirio.svg)](https://github.com/AndreuCodina/wirio/blob/main/LICENSE)
[![Documentation](https://img.shields.io/badge/📚_documentation-3D9970)](https://andreucodina.github.io/wirio)

</div>

## Features

- **Use it everywhere:** Use dependency injection in web servers, background tasks, console applications, Jupyter notebooks, tests, etc.
- **Lifetimes**: `Singleton` (same instance per application), `Scoped` (same instance per HTTP request scope) and `Transient` (different instance per resolution).
- **FastAPI integration** out of the box, and pluggable to any web framework.
- **Automatic resolution and disposal**: Automatically resolve constructor parameters and manage async and non-async context managers. It's no longer our concern to know how to create or dispose services.
- **Clear design** inspired by one of the most used and battle-tested DI libraries, adding async-native support, important features and good defaults.
- **Centralized configuration**: Register all services in one place using a clean syntax, and without decorators.
- **ty** and **Pyright** strict compliant.

## 📦 Installation

```bash
uv add wirio
```

## ✨ Quickstart with FastAPI

Inject services into async endpoints using `Annotated[..., FromServices()]`.

```python
class EmailService:
    pass


class UserService:
    def __init__(self, email_service: EmailService) -> None:
        self.email_service = email_service


app = FastAPI()

@app.post("/users")
async def create_user(user_service: Annotated[UserService, FromServices()]) -> None:
    ...

services = ServiceContainer()
services.add_transient(EmailService)
services.add_transient(UserService)
services.configure_fastapi(app)
```

## ✨ Quickstart without FastAPI

Register services and resolve them.

```python
class EmailService:
    pass


class UserService:
    def __init__(self, email_service: EmailService) -> None:
        self.email_service = email_service


services = ServiceContainer()
services.add_transient(EmailService)
services.add_transient(UserService)

user_service = await services.get(UserService)
```

If we want a scope per operation (e.g., per HTTP request or message from a queue), we can create a scope from the service provider:

```python
async with services.create_scope() as service_scope:
    user_service = await service_scope.get(UserService)
```

## 🔄 Lifetimes

- `Transient`: A new instance is created every time the service is requested. Examples: Services without state, workflows, repositories, service clients...
- `Singleton`: The same instance is used every time the service is requested. Examples: Settings (`pydantic-settings`), machine learning models, database connection pools, caches.
- `Scoped`: A new instance is created for each new scope, but the same instance is returned within the same scope. Examples: Database clients, unit of work.

## 🏭 Factories

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

## 🧪 Simplified testing

We can substitute dependencies on the fly meanwhile the context manager is active.

```python
with services.override(EmailService, email_service_mock):
    user_service = await services.get(UserService)
```

## 📝 Interfaces & abstract classes

We can register a service by specifying both the service type (interface / abstract class) and the implementation type (concrete class). This is useful when we want to inject services using abstractions.

```python
class NotificationService(ABC):
    @abstractmethod
    async def send_notification(self, user_id: str, message: str) -> None:
        ...


class EmailService(NotificationService):
    @override
    async def send_notification(self, user_id: str, message: str) -> None:
        pass


class UserService:
    def __init__(self, notification_service: NotificationService) -> None:
        self.notification_service = notification_service

    async def create_user(self, email: str) -> None:
        user = self.create_user(email)
        await self.notification_service.send_notification(user.id, "Welcome to our service!")


services.add_transient(NotificationService, EmailService)
```

## 📝 Keyed services

We can register a service by specifying both the service type and a key. This is useful when we want to resolve services using abstractions and an explicit key.

```python
class NotificationService(ABC):
    @abstractmethod
    async def send_notification(self, user_id: str, message: str) -> None:
        ...


class EmailService(NotificationService):
    @override
    async def send_notification(self, user_id: str, message: str) -> None:
        pass


class PushNotificationService(NotificationService):
    @override
    async def send_notification(self, user_id: str, message: str) -> None:
        pass


class UserService:
    def __init__(
        self,
        notification_service: Annotated[NotificationService, FromKeyedServices("email"),
    ) -> None:
        self.notification_service = notification_service

    async def create_user(self, email: str) -> None:
        user = self.create_user(email)
        await self.notification_service.send_notification(user.id, "Welcome to our service!")


services.add_keyed_transient("email", NotificationService, EmailService)
services.add_keyed_transient("push", NotificationService, PushNotificationService)
```

## 📝 Auto-activated services

We can register a service as auto-activated. This is useful when we want to ensure our FastAPI application doesn't start to serve requests until certain services are fully initialized (e.g., machine learning models, database connection pools and caches).

```python
services.add_auto_activated_singleton(MachineLearningModel)
```

## 📚 Documentation

For more information, [check out the documentation](https://AndreuCodina.github.io/wirio).
