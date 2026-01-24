# Testing

## Quickstart

We can create a fixture in `conftest.py` that provides a `ServiceProvider` instance:

```python
@pytest.fixture
async def service_provider() -> AsyncGenerator[ServiceProvider]:
    async with services.build_service_provider() as service_provider:
        yield service_provider
```

And then we can inject it into our tests and resolve the services.

```python
async def test_create_user(service_provider: ServiceProvider) -> None:
    user_service = await service_provider.get_required_service(UserService)

    await user_service.create_user()
```

## Recommended setup

We have a `services` singleton declared in `main.py` that is used to build the `ServiceProvider` for the application.

```python
services = ServiceCollection()
```

Depending on the complexity of our tests, we might want to alter the services before creating the service provider. Due to this, it's always a good idea to update `main.py` and create a function instead of having a singleton, so that each test can call it to get a fresh `ServiceCollection` instance.

```python
def configure_services() -> ServiceCollection:
    services = ServiceCollection()
    return services
```

In a real FastAPI application, it'd look like this:

```python
def configure_services() -> ServiceCollection:
    services = ServiceCollection()
    return services


def create_app() -> FastAPI:
    app = FastAPI()
    return app


app = create_app()
services = configure_services()
services.configure_fastapi(app)
```

And the fixture in `conftest.py`:

```python
@pytest.fixture
async def service_provider() -> AsyncGenerator[ServiceProvider]:
    services = configure_services()

    async with services.build_service_provider() as service_provider:
        yield service_provider
```

## Globally override a service

Imagine we have a service `EmailService` that sends real emails. During testing, we want to replace it with a mock implementation that doesn't send real emails.

```python
@pytest.fixture
async def service_provider(mocker: MockerFixture) -> AsyncGenerator[ServiceProvider]:
    services = configure_services()
    email_service_mock = mocker.create_autospec(EmailService, instance=True)
    services.add_singleton(EmailService, email_service_mock)

    async with services.build_service_provider() as service_provider:
        yield service_provider
```

Remember that if `EmailService` is already registered in `services`, adding it again will override the previous registration.
Now, when we resolve `EmailService` in our tests, we'll get the mock implementation instead of the real one.

**Note:** Another option would be no to register `EmailService` in local, and register it depending on the environment.

## Override a service per test

We can also override a service for a specific test case. This is useful when we want to test different behaviors of a service.

```python
@pytest.fixture
def services() -> ServiceCollection:
    return configure_services()


async def test_create_user(services: ServiceCollection, mocker: MockerFixture) -> None:
    email_service_mock = mocker.create_autospec(EmailService, instance=True)
    services.add_singleton(EmailService, email_service_mock)

    async with services.build_service_provider() as service_provider:
        user_service = await service_provider.get_required_service(UserService)

        await user_service.create_user()
```
