# Lifetimes

Lifetimes define how long a service instance lives and how it is shared. `Wirio` supports three lifetimes:

- `Transient`: A new instance is created every time the service is requested. Examples: Services without state, workflows, repositories, service clients...
- `Singleton`: The same instance is used every time the service is requested. Examples: Settings (`pydantic-settings`), machine learning models, database connection pools, caches.
- `Scoped`: A new instance is created for each new scope, but the same instance is returned within the same scope. Examples: Database clients, unit of work.