# Get all services of a type

Sometimes you want to resolve all services registered for a given type. For example, you might want to resolve all implementations of an interface.

```python hl_lines="9"
services.add_transient(NotificationService, EmailService)
services.add_transient(NotificationService, SmsService)
services.add_transient(NotificationService, WhatsAppService)


class UserService:
    def __init__(
        self,
        notification_services: Sequence[NotificationService]
    ) -> None:
        self.notification_services = notification_services
```

You could also resolve all implementations with a specific key.

```python hl_lines="9-11"
services.add_transient("key", EmailService)
services.add_transient("key", SmsService)
services.add_transient("key", WhatsAppService)


class UserService:
    def __init__(
        self,
        notification_services: Annotated[
            Sequence[NotificationService], FromKeyedServices("key")
        ]
    ) -> None:
        self.notification_services = notification_services
```

Using a `ServiceProvider`, you can resolve all services of a type using `get_services` and `get_keyed_services`.
