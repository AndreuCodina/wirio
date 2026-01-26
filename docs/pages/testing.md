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

## Override services

`UserService` could have the dependency `EmailService`, that sends real emails. During testing, we want to replace it with a mock implementation that doesn't send real emails.

To replace a service during testing, we can use the `override_service` and `override_keyed_service` methods provided by `ServiceProvider`. This allows us to temporarily replace a service for the duration of context manager block.

```python
async def test_create_user(service_provider: ServiceProvider, mocker: MockerFixture) -> None:
    mail_service_mock = mocker.create_autospec(EmailService, instance=True)

    with service_provider.override_service(EmailService, mail_service_mock):
        user_service = await service_provider.get_required_service(UserService)

        await user_service.create_user()
```

## Globally override services

We can also override a service for all tests by modifying the fixture that provides the `ServiceProvider` instance. This is useful when we want to use a mock for a service across multiple tests, or all tests.

```python
@pytest.fixture
async def service_provider(mocker: MockerFixture) -> AsyncGenerator[ServiceProvider]:
    email_service_mock = mocker.create_autospec(EmailService, instance=True)

    async with services.build_service_provider() as service_provider:
        with service_provider.override_service(EmailService, mail_service_mock):
            yield service_provider
```

## ServiceCollection registration

The context manager approach is straightforward, but if we want to test more complex scenarios, we can directly register the mock implementation in the `ServiceCollection` before building the `ServiceProvider`. This way, the mock will be used whenever `EmailService` is resolved.

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
