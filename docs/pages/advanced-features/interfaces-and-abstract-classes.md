# Interfaces & abstract classes

We can register a service by specifying both the service type (interface / abstract class) and the implementation type (concrete class). This is useful when we want to inject services using abstractions.

```python hl_lines="14 22"
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
