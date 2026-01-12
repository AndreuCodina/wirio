# Quickstart

**Use case:** Your application needs to instance two services, `EmailService` and `UserService`, and `UserService` depends on the former.

```python
class EmailService:
    pass


class UserService:
    def __init__(self, email_service: EmailService) -> None:
        self.email_service = email_service
```

Then, instead of creating the instances manually, you register them as services.

```python
services = ServiceCollection()
services.add_transient(EmailService)
services.add_transient(UserService)
```

You'll use `.add_X` depending on the desired [lifetime](../core-concepts/lifetimes.md). In this case, both services are registered as transient, meaning a new instance will be created each time it's requested.

Finally, you convert the service collection into a service provider, which will validate and build the dependency graph, and you'll be able to request instances from it.

```python
async with services.build_service_provider() as service_provider:
    user_service = await service_provider.get_required_service(UserService)
```

**Full code:**

```python hl_lines="18-20 24-25"
--8<-- "docs/code/quickstart.py"
```
