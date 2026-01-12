# Interfaces & abstract classes

You can register a service by specifying both the service type (interface / abstract class) and the implementation type (concrete class). This is useful when you want to inject services using abstractions.

```python
class NotificationService(ABC):
    async def send_notification(self, recipient: str, message: str) -> None:
        ...


class EmailService(NotificationService):
    @override
    async def send_notification(self, recipient: str, message: str) -> None:
        pass


class UserService:
    def __init__(self, notification_service: NotificationService) -> None:
        self.notification_service = notification_service

    async def create_user(self, email: str) -> None:
        await self.notification_service.send_notification(email, "Welcome to our service!")


services.add_transient(NotificationService, EmailService)
```