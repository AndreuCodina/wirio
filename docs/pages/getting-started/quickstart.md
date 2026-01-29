# Quickstart

## Define dependencies

To showcase the basics of Wirio, we will create a container able to resolve the following:

- `EmailService`: A simple service with no dependencies.
- `UserService`: A service depending on `EmailService`.

```python
--8<-- "docs/code/getting_started/quickstart/define_dependencies.py"
```

## Create the container

The next step is to create a container and register the dependencies we just defined.

```python title="main.py" hl_lines="4-5"
from wirio.service_container import ServiceContainer

services = ServiceContainer()
services.add_transient(EmailService)  # (1)!
services.add_transient(UserService)
```

1. Both services are registered as transient, meaning a new instance will be created each time it's requested.

We'll use `.add_X` depending on the desired [lifetime](../core-concepts/lifetimes.md). For example: `.add_transient` for transient services, `.add_singleton` for singleton services and `.add_scoped` for scoped services.

## Use

Finally, we convert the service collection into a service provider, which will validate and build the dependency graph, and we'll be able to request instances from it.

=== "Console application"

    To fetch dependencies from the container, we call `.get` on the container instance with the type we want to retrieve.

    ```python title="main.py"
    user_service = await services.get(UserService)
    ```

=== "Jupyter notebook"

    To fetch dependencies from the container, we call `.get` on the container instance with the type we want to retrieve.

    ```python title="notebook.py"
    user_service = await services.get(UserService)
    ```

=== "FastAPI"

    We annotate the parameter with the dependency to retrieve.

    ```python title="main.py" hl_lines="5"
    from wirio.annotations import FromServices

    @app.post("/users")
    async def create_user(
        user_service: Annotated[UserService, FromServices()],
    ) -> None:
        pass
    ```

## Test

We can substitute dependencies on the fly meanwhile the context manager is active.

```python
with services.override(EmailService, email_service_mock):
    user_service = await services.get(UserService)
```

## Full code

=== "Console application"

    ```python hl_lines="20"
    import asyncio

    from wirio.service_container import ServiceContainer

    class EmailService:
        pass

    class UserService:
        def __init__(self, email_service: EmailService) -> None:
            self.email_service = email_service

            async def create_user(self) -> None:
                pass


    async def main() -> None:
        services = ServiceContainer()
        services.add_transient(EmailService)
        services.add_transient(UserService)

        async with services:  # (1)!
            user_service = await services.get(UserService)

    if __name__ == "__main__":
        asyncio.run(main())
    ```

    1. We recommended calling `.close` or using a context manager to ensure a proper disposal of resources when the application ends

=== "Jupyter notebook"

    ```python hl_lines="1"
    from main import services  # (1)!

    user_service = await services.get(UserService)
    ```

    1. Jupyter works with async by default, so we can directly call `await` in the cells

=== "FastAPI"

    ```python hl_lines="34"
    --8<-- "docs/code/getting_started/quickstart/fastapi_full_code.py"
    ```

    1. This will configure FastAPI to use Wirio's dependency injection
