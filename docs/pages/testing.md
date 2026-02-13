# Testing

## Quickstart

We have to use the service provider to resolve the services we want to test. The way to get it depends on the type of application we are testing.

=== "FastAPI"

    The way FastAPI has to execute code before running the tests is different from a console application. It uses its own test client that creates an application instance for each test.

    We have to import the services from the `app` singleton of `main.py`, and create a fixture to inject the service provider.

    ```python
    from main import app
    from wirio.integrations.fastapi import get_service_provider

    @pytest.fixture
    def service_provider() -> Generator[ServiceProvider]:
        with TestClient(app):
            yield get_service_provider(app)
    ```

=== "Console application"

    We have to import the services from `main.py`. To do that, we can create the function `configure_services` (or move the `services` variable outside the `main` function).

    ```python
    def configure_services() -> ServiceCollection:
        services = ServiceCollection()
        ...

        return services
    ```

    The next step is creating a fixture to inject the service provider.

    ```python
    from main import configure_services

    @pytest.fixture
    async def service_provider() -> AsyncGenerator[ServiceProvider]:
        services = configure_services()

        async with services.build_service_provider() as service_provider:
            yield service_provider
    ```

And then we can inject it into our tests and resolve the services.

```python
async def test_create_user(service_provider: ServiceProvider) -> None:
    user_service = await service_provider.get_required_service(UserService)

    await user_service.create_user()
```

## Override services

`UserService` could have the dependency `EmailService`, that sends real emails. During testing, we want to replace it with a mock implementation that doesn't send real emails.

To replace a service during testing, we can use the `override_service` and `override_keyed_service` methods provided by `ServiceProvider`. This allows us to temporarily replace a service for the duration of context manager block.

```python
async def test_create_user(service_provider: ServiceProvider, mocker: MockerFixture) -> None:
    email_service_mock = mocker.create_autospec(EmailService, instance=True)

    with service_provider.override_service(EmailService, email_service_mock):
        user_service = await service_provider.get_required_service(UserService)

        await user_service.create_user()
```

## Globally override services

We can also override a service for all tests by modifying the fixture that provides the `ServiceProvider` instance. This is useful when we want to use a mock for a service across multiple tests, or all tests.

=== "FastAPI"

    ```python
    @pytest.fixture
    def service_provider(mocker: MockerFixture) -> Generator[ServiceProvider]:
        with TestClient(app):
            service_provider = get_service_provider(app)
            email_service_mock = mocker.create_autospec(EmailService, instance=True)

            with service_provider.override_service(EmailService, email_service_mock):
                yield service_provider
    ```

=== "Console application"

    ```python
    @pytest.fixture
    async def service_provider(mocker: MockerFixture) -> AsyncGenerator[ServiceProvider]:
        services = configure_services()

        async with services.build_service_provider() as service_provider:
            email_service_mock = mocker.create_autospec(EmailService, instance=True)

            with service_provider.override_service(EmailService, email_service_mock):
                yield service_provider
    ```

## ServiceCollection registration

The context manager approach is straightforward, but if we want to test a more complex scenario, we can directly register the mock implementation in the `ServiceCollection` before building the `ServiceProvider`. This way, the mock will be used whenever `EmailService` is resolved.

```python
@pytest.fixture
async def service_provider(mocker: MockerFixture) -> AsyncGenerator[ServiceProvider]:
    services = configure_services()
    email_service_mock = mocker.create_autospec(EmailService, instance=True)
    services.add_singleton(EmailService, email_service_mock)

    async with services.build_service_provider() as service_provider:
        yield service_provider
```

Remember that if `EmailService` is already registered, registering it again means the last registration will be used when resolving the service.

**Note:** Another strategy could be not to register `EmailService` in local, and register it depending on the environment.
