# Auto-activated services

## Overview

By default, services are built lazily, i.e., they're instantiated when they are requested. This behavior enables lifetime management and reduces startup time.

However, some singleton services need to be instantiated/auto-activated before the application starts handling requests, so that our customers don’t experience delayed or timed-out requests. Some examples are machine learning models, database connection pools, telemetry collectors, and background tasks.

**Example scenario**: In our FastAPI application, we have to load a machine learning model, so we add it as an auto-activated service. If we have one cloud instance for the API, when we deploy a new version, the new one isn't replaced until the model is loaded in memory, ensuring that all requests are served without delays or time-out errors. If we have autoscaling enabled, new instances aren't added to the load balancer until the model is loaded.

## Register auto-activated singletons

Use `add_auto_activated_singleton()` or `add_auto_activated_keyed_singleton()` to register singletons or keyed singletons as auto-activated services. The accepted parameters are identical to `add_singleton()` and `add_keyed_singleton()`, respectively.

```python
services.add_auto_activated_singleton(MachineLearningModel)
```

Auto-activation of keyed services is especially useful when a subset of tenants or regions need warm caches or long-lived sockets before they receive traffic.

```python
services.add_auto_activated_keyed_singleton("west-us", DataPlaneClient, RegionalClient)
```

## Upgrade existing registrations

If a singleton is already registered, we can enable auto-activation for it via `enable_singleton_auto_activation` or `enable_keyed_singleton_auto_activation`.

```python hl_lines="9-10"
# Original registration
services.add_singleton(BackgroundPublisher)
services.add_keyed_singleton("us-east", DataPlaneClient, RegionalClient)

# Later
services.enable_singleton_auto_activation(BackgroundPublisher)
services.enable_keyed_singleton_auto_activation("us-east", DataPlaneClient)
```

## When to auto-activate

- Prime caches, long-lived connections, or periodic tasks that must run before the first request.
- Fail-fast during startup by surfacing dependency errors.
- Avoid auto-activation for expensive workloads that are rarely used or that scale with tenant count; lazily resolving them keeps startup predictable.
- Combine with application health checks to make sure all auto-activated services are ready before serving traffic.
