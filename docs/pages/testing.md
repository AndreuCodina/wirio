# Testing

## Quickstart

You can create a fixture in `conftest.py` that provides a `ServiceProvider` instance:

```python
@pytest.fixture
async def service_provider() -> AsyncGenerator[ServiceProvider]:
    async with services.build_service_provider() as service_provider:
        yield service_provider
```

And then you can inject it into your tests and resolve the services.

```python
async def test_create_user(service_provider: ServiceProvider) -> None:
    user_service = await service_provider.get_required_service(UserService)

    await user_service.create_user()
```

## Globally override a service

Imagine you have a service `EmailService` that sends real emails. During testing, you want to replace it with a mock implementation that doesn't send real emails.

```python
@pytest.fixture
async def service_provider(mocker: MockerFixture) -> AsyncGenerator[ServiceProvider]:
    email_service_mock = mocker.create_autospec(EmailService, instance=True)
    services.add_singleton(EmailService, MockEmailService)

    async with services.build_service_provider() as service_provider:
        yield service_provider
```

Remember that if `EmailService` is already registered in `services`, adding it again with will override the previous registration.
Now, when you resolve `EmailService` in your tests, you'll get the mock implementation instead of the real one.

## Override a service per test

You can also override a service for a specific test case. This is useful when you want to test different behaviors of a service.

```python
async def test_create_user(
    service_provider: ServiceProvider,
    mocker: MockerFixture
) -> None:
    email_service_mock = mocker.create_autospec(EmailService, instance=True)
    services.add_singleton(EmailService, email_service_mock)
    user_service = await service_provider.get_required_service(UserService)

    await user_service.create_user()
```

But given `services` is a singleton declared in `main.py`, you should instead create in `main.py` the function `configure_services` that returns a new `ServiceCollection` each time you call it, so that each test can call it to get a fresh `ServiceCollection` instance.

```python
def configure_services() -> ServiceCollection:
    services = ServiceCollection()
    services.add_transient(EmailService)
    return services
```

Regarding the fixture setup, it'd look like this:

```python
@pytest.fixture
def services() -> ServiceCollection:
    return configure_services()

@pytest.fixture
async def service_provider(services: ServiceCollection, mocker: MockerFixture) -> AsyncGenerator[ServiceProvider]:
    email_service_mock = mocker.create_autospec(EmailService, instance=True)
    services.add_singleton(EmailService, MockEmailService)

    async with services.build_service_provider() as service_provider:
        yield service_provider
```

And the test case:

```python
async def test_create_user(services: ServiceCollection, mocker: MockerFixture) -> None:
    email_service_mock = mocker.create_autospec(EmailService, instance=True)
    services.add_singleton(EmailService, email_service_mock)

    async with services.build_service_provider() as service_provider:
        user_service = await service_provider.get_required_service(UserService)

        await user_service.create_user()
```
