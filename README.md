<div align="center">
<img alt="Logo" src="docs/logo.png" width="522" height="348">

[![CI](https://img.shields.io/github/actions/workflow/status/AndreuCodina/aspy-dependency-injection/main.yaml?branch=main&logo=github&label=CI)](https://github.com/AndreuCodina/aspy-dependency-injection/actions/workflows/main.yaml)
[![Coverage status](https://coveralls.io/repos/github/AndreuCodina/aspy-dependency-injection/badge.svg?branch=main)](https://coveralls.io/github/AndreuCodina/aspy-dependency-injection?branch=main)
[![PyPI - version](https://img.shields.io/pypi/v/aspy-dependency-injection?color=blue&label=pypi)](https://pypi.org/project/aspy-dependency-injection/)
[![Python - versions](https://img.shields.io/pypi/pyversions/aspy-dependency-injection.svg)](https://github.com/AndreuCodina/aspy-dependency-injection)
[![License](https://img.shields.io/github/license/AndreuCodina/aspy-dependency-injection.svg)](https://github.com/AndreuCodina/aspy-dependency-injection/blob/main/LICENSE)
</div>

## Features
- **Use it everywhere:** Use dependency injection in web servers, background tasks, console applications, Jupyter notebooks, tests, etc.
- **Lifetimes**: `Singleton` (same instance per application), `Scoped` (same instance per HTTP request scope) and `Transient` (different instance per resolution).
- **FastAPI integration** out of the box, and pluggable to any web framework.
- **Automatic resolution and disposal**: Automatically resolve constructor parameters and manage async and non-async context managers. It's not longer your concern to know how to create or dispose services.
- **Clear design** inspired by one of the most used and battle-tested DI libraries, adding async-native support, important features and good defaults.
- **Centralized configuration**: Register all services in one place using a clean syntax, and without decorators.
- **ty** and **Pyright** strict compliant.

## Installation
```bash
uv add aspy-dependency-injection
```

## Quickstart with FastAPI

Inject services into async endpoints using `Annotated[..., Inject()]`.

```python
class EmailService:
    pass


class UserService:
    def __init__(self, email_service: EmailService) -> None:
        self.email_service = email_service
    
    async def create_user(self) -> None:
        pass


app = FastAPI()

@app.post("/users")
async def create_user(user_service: Annotated[UserService, Inject()]) -> None:
    await user_service.create_user()

services = ServiceCollection()
services.add_transient(EmailService)
services.add_transient(UserService)
services.configure_fastapi(app)
```

## Quickstart without FastAPI

You convert the service collection into a service provider:

```python
class EmailService:
    pass


class UserService:
    def __init__(self, email_service: EmailService) -> None:
        self.email_service = email_service
    
    async def create_user(self) -> None:
        pass

    
services = ServiceCollection()
services.add_transient(EmailService)
services.add_transient(UserService)

async def main() -> None:
    async with services.build_service_provider() as service_provider:
        user_service = await service_provider.get_required_service(UserService)
        await user_service.create_user()


if __name__ == "__main__":
    asyncio.run(main())
```

If you want a scope per operation (e.g., per HTTP request or message from a queue), you can create a scope from the service provider:

```python
async with service_provider.create_scope() as service_scope:
    user_service = await service_scope.get_required_service(UserService)
    await user_service.create_user()
```

## Lifetimes

- `Transient`: A new instance is created every time the service is requested. Examples: Services without state, workflows, repositories, service clients...
- `Singleton`: The same instance is used every time the service is requested. Examples: Settings (`pydantic-settings`), machine learning models, database connection pools, caches.
- `Scoped`: A new instance is created for each new scope, but the same instance is returned within the same scope. Examples: Database clients, unit of work.

## Registration with implementation type

You can register a service by specifying both the service type (interface or base class) and the implementation type (concrete class). This is useful when you want to program against interfaces or abstractions.

```python
class EmailServiceBase:
    async def send_email(self, to: str, subject: str, body: str) -> None:
        raise NotImplementedError


class SmtpEmailService(EmailServiceBase):
    async def send_email(self, to: str, subject: str, body: str) -> None:
        # Send email via SMTP
        pass


class UserService:
    def __init__(self, email_service: EmailServiceBase) -> None:
        self.email_service = email_service
    
    async def create_user(self, email: str) -> None:
        await self.email_service.send_email(email, "Welcome", "Welcome to our service!")


services = ServiceCollection()
services.add_singleton(EmailServiceBase, SmtpEmailService)
services.add_transient(UserService)

async with services.build_service_provider() as service_provider:
    user_service = await service_provider.get_required_service(UserService)
    await user_service.create_user("user@example.com")
```

In this example:
- `EmailServiceBase` is registered as the service type
- `SmtpEmailService` is used as the implementation
- When `UserService` requests `EmailServiceBase`, it receives an instance of `SmtpEmailService`
- This works with all lifetimes: `add_singleton`, `add_scoped`, and `add_transient`

## Factories

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

And, if you want to re-use it, you create a factory function with yield:

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

services.add_singleton(ApplicationSettings)
services.add_transient(inject_database_client)
```

## Testing

TBD
