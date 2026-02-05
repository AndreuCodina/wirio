# Service validation

## Overview

`Wirio` validates your service graph at startup and during resolution so that dependency issues fail fast instead of surfacing as runtime bugs. Validation is opt-in through the `ServiceCollection.build_service_provider(validate_scopes=True, validate_on_build=True)` switches, both enabled by default. Use them to:

- Catch missing registrations (`CannotResolveServiceError`) before the first request.
- Detect scoped services flowing into singletons (`ScopedInSingletonError`).
- Block scoped services from being resolved directly from the root provider (`DirectScopedResolvedFromRootError`, `ScopedResolvedFromRootError`).

## Build-time validation (`validate_on_build`)

When `validate_on_build=True`, the provider walks every registered descriptor while entering the `async with services.build_service_provider()` context. Each failure is wrapped in an `ExceptionGroup` so you can see every misconfiguration at once.

```python
services = ServiceCollection()
services.add_transient(CacheWarmer)

try:
    async with services.build_service_provider():
        pass
except ExceptionGroup as exc:
    for error in exc.exceptions:
        # Inspect error.__cause__ for the original CannotResolveServiceError, etc.
        print(error.__cause__)
```

Set `validate_on_build=False` when you prefer lazy validation.

## Scope validation (`validate_scopes`)

Scope validation has two layers:

1. **Graph inspection at build time.** The call-site validator walks every service tree and raises `ScopedInSingletonError` if a singleton depends (even indirectly) on a scoped service.
2. **Runtime guard rails.** At resolution time, the provider tracks when code tries to resolve scoped services from the root scope and raises the corresponding error.

### Prevent scoped services inside singletons

```python
import pytest

class TenantContext:  # Scoped
    pass

class ReportGenerator:
    def __init__(self, context: TenantContext) -> None:
        self.context = context

services.add_scoped(TenantContext)
services.add_singleton(ReportGenerator)

with pytest.raises(ExceptionGroup):
    async with services.build_service_provider(validate_scopes=True, validate_on_build=True):
        pass
```

Fix the dependency by either making `ReportGenerator` scoped or moving the scoped dependency behind an abstracted service that supplies per-request values lazily.

### Resolve scoped services using child scopes

Valid scoped resolutions happen inside a scope created from the root provider:

```python
async with services.build_service_provider() as service_provider:
    async with service_provider.create_scope() as service_scope:
        report_generator = await service_scope.get_required_service(ReportGenerator)
```

Attempting to resolve a scoped service (or something that depends on it) directly from the root scope raises `DirectScopedResolvedFromRootError` or `ScopedResolvedFromRootError`. These errors usually mean you forgot to create a scope for your background job or test.

## Troubleshooting reference

- `CannotResolveServiceError`: register the missing dependency or adjust the constructor signature.
- `ScopedInSingletonError`: change the singleton into a scoped service or extract a factory/service locator that captures scoped state per resolution.
- `DirectScopedResolvedFromRootError`: create a scope via `provider.create_scope()` (or let your framework manage scopes) before resolving scoped services.
- `ScopedResolvedFromRootError`: same as above, but triggered when a transient or singleton indirectly requires a scoped service from the root provider.

## Putting it together

- You can disable validations selectively when you prefer lazy validation or no validation for faster startup times.
- Keeping both validation flags enabled in production—together with auto-activated services— provides the fastest feedback loop and guarantees that your container is consistent before accepting traffic.
