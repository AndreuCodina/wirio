# FastAPI integration

## Benefits

- Use Wirio's dependency injection in FastAPI.
- Use FastAPI with a framework-agnostic dependency injection.
- Easily testable services.
- Transparent integration instead of referencing module-based singletons.

## Installation

To use the FastAPI integration, add the `fastapi` extra to automatically install the required compatible dependencies.

```bash
uv add wirio[fastapi]
```

## Quickstart

```python hl_lines="26 32"
--8<-- "docs/code/integrations/fastapi/quickstart.py"
```

1. Annotate the parameter with the type to resolve
2. This will configure FastAPI to use Wirio's dependency injection

## Testing

Information available [here](../testing.md).
