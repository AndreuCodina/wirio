# Testing

## Quickstart

We can substitute dependencies on the fly meanwhile the context manager is active.

```python
with services.override(EmailService, email_service_mock):
    user_service = await services.get(UserService)
```

## Override services

`UserService` could have the dependency `EmailService`, that sends real emails. During testing, we want to replace it with a mock implementation that doesn't send real emails.

To replace a service during testing, we can use the `override` and `override_keyed` methods provided by `ServiceContainer`. This allows us to temporarily replace a service for the duration of context manager block.

```python
async def test_create_user(mocker: MockerFixture) -> None:
    mail_service_mock = mocker.create_autospec(EmailService, instance=True)

    with services.override(EmailService, mail_service_mock):
        user_service = await services.get(UserService)

        await user_service.create_user()
```

As a good practice, we recommend using a fixture instead of importing `services` from `main.py`. This way, it's decoupled from the application code, and we can modify it as needed for testing, as we'll see in the next sections. It would look like this:

```python
@pytest.fixture
async def services() -> AsyncGenerator[ServiceContainer]:
    async with services:
        yield services


async def test_create_user(services: ServiceContainer) -> None:
    user_service = await services.get(UserService)

    await user_service.create_user()
```

## Globally override services

We can also override a service for all tests by modifying the fixture that provides the `ServiceContainer` instance. This is useful when we want to use a mock for a service across multiple tests, or all tests.

```python
@pytest.fixture
async def services(mocker: MockerFixture) -> AsyncGenerator[ServiceContainer]:
    email_service_mock = mocker.create_autospec(EmailService, instance=True)

    async with services:
        with services.override(EmailService, mail_service_mock):
            yield services
```
