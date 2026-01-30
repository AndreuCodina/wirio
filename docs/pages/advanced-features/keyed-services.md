# Keyed services

## Overview

Keyed services let us register multiple implementations of the same abstraction and pick the one we need at resolution time by supplying a key. They are ideal for multi-tenant workloads, per-region clients, feature flags, or whenever a single interface must be backed by different resources.

## Introductory example

We have two implementations of `NotificationService`: one that sends emails and another that sends push notifications. We want to be able to choose which implementation to use when injecting `NotificationService` into `UserService`.

We can use `add_keyed_transient`, `add_keyed_scoped`, or `add_keyed_singleton` to bind an implementation to a specific key.

```python hl_lines="31 32"
class NotificationService(ABC):
    @abstractmethod
    async def send_notification(self, recipient: str, message: str) -> None:
        ...


class EmailService(NotificationService):
    @override
    async def send_notification(self, recipient: str, message: str) -> None:
        pass


class PushNotificationService(NotificationService):
    @override
    async def send_notification(self, recipient: str, message: str) -> None:
        pass


class UserService:
    def __init__(
        self,
        notification_service: Annotated[NotificationService, FromKeyedServices("email")],
    ) -> None:
        self.notification_service = notification_service

    async def create_user(self, email: str) -> None:
        user = self.create_user(email)
        await self.notification_service.send_notification(user.id, "Welcome to our service!")


services.add_keyed_transient("email", NotificationService, EmailService)
services.add_keyed_transient("push", NotificationService, PushNotificationService)
```

In the example we're using a key of type string, but we can use any type (enums, integers, etc.).

## Example with feature flags

```python hl_lines="20-21"
class OrderService:
    def __init__(
        self,
        feature_manager: FeatureManager,
        service_provider: BaseServiceProvider
    ) -> None:
        self.feature_manager = feature_manager
        self.service_provider = services


    async def calculate_price(self, product: Product) -> Decimal:
        pricing_service = (
            await self.service_provider.get_required_keyed_service("new", PricingService)
            if await self.feature_manager.is_enabled("NewPricing")
            else await self.service_provider.get_required_keyed_service("legacy", PricingService)
        )
        return pricing_service.calculate_price(product)


services.add_keyed_transient("new", PricingService, NewPricingService)
services.add_keyed_transient("legacy", PricingService, LegacyPricingService)
```

Or we can also use a factory to encapsulate the logic and a transient registration.

## Register multiple and dynamic keyed services

Factories receive the requested key as their first argument so we can flow it into the created object when needed.

```python
def inject_principal_postgres_client(_: str | None) -> PostgresClient:
    return PostgresClient(f"postgresql://principal1239139123213.example/db")


def inject_secondary_postgres_client(_: str | None) -> PostgresClient:
    return PostgresClient(f"postgresql://secondary9954322u3912u123.example/db")


def inject_tenant_postgres_client(tenant_id: str | None) -> PostgresClient:
    return PostgresClient(f"postgresql://{tenant_id}.example/db")


services = ServiceCollection()
services.add_keyed_singleton("principal", inject_principal_postgres_client)
services.add_keyed_singleton("secondary", inject_secondary_postgres_client)
services.add_keyed_singleton(KeyedService.ANY_KEY, inject_tenant_postgres_client)

async with services.build_service_provider() as service_provider:
    postgres_client = await service_provider.get_required_keyed_service(
        "principal", PostgresClient
    )
```

The `ANY_KEY` registration works as a fallback: any lookup that does not find a dedicated key reuses that instance.

Passing `None` as the key resolves services that were explicitly registered with `None`, but it also falls back to the unkeyed registration of the same service type when no keyed entry exists. This makes it easy to gradually adopt keyed services without duplicating registrations.

We can query registrations programmatically through `ServiceProviderIsKeyedService.is_keyed_service(key, service_type)` to decide when to fall back to defaults.

## Composing services with `FromKeyedServices`

We can inject keyed dependencies into other services via `typing.Annotated` and the `FromKeyedServices` helper:

```python
class TenantRepository:
    def __init__(
        self,
        connection: Annotated[PostgresClient, FromKeyedServices("tenant-1")],
    ) -> None:
        self.connection = connection
```

`FromKeyedServices` behaves differently depending on how we call it:

- `FromKeyedServices("tenant-1")` resolves that exact key.
- `FromKeyedServices(None)` forces the `None` key (or the unkeyed registration fallback).
- `FromKeyedServices()` inherits the key that was used to resolve the parent service. This is ideal when the parent itself is keyed and we want every nested dependency to share the same key automatically.

## Receiving the key inside a service

To know which key was requested when our service was resolved, annotate a constructor parameter with `ServiceKey()`:

```python
from typing import Annotated
from wirio.annotations import ServiceKey


class KeyAwareCache:
    def __init__(self, key: Annotated[str, ServiceKey()]) -> None:
        self._cache_namespace = f"tenant:{key}"
```

This works only when the service is itself resolved via a key (explicitly or through inheritance). Trying to use `ServiceKey()` on an unkeyed service raises `CannotResolveServiceError`.

## Wildcard registrations and caveats

- `KeyedService.ANY_KEY` lets us register a catch-all implementation but **cannot** be used when resolving services. Attempting to resolve with that sentinel value raises `KeyedServiceAnyKeyUsedToResolveServiceError`.
- Factories registered under `ANY_KEY` receive the requested key so they can still personalize the instance.
- Register with `None` when we want a dedicated "default" slot that can still be requested explicitly via `get_required_keyed_service(None, service_type)` or `FromKeyedServices(None)`.

## Best practices

- Pick a stable key type (string tenant IDs, enums, UUIDs) and reuse it consistently.
- Prefer inherited keys (`FromKeyedServices()`) for chains of dependent services so they all operate within the same tenant context.
- Use `ServiceProviderIsKeyedService` to guard features that require a keyed registration and to emit helpful errors during startup.
- Fall back to `KeyedService.ANY_KEY` or `None` to provide safe defaults, but keep the wildcard work lightweight to avoid becoming a hotspot.
