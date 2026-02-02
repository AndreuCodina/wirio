# FastAPI integration

## Installation

While we can install `Wirio` with `uv add wirio`, it's recommended to add the `fastapi` extra to ensure the installed FastAPI version is compatible.

```bash
uv add wirio[fastapi]
```

## Quickstart

```python hl_lines="26 34"
--8<-- "docs/code/integrations/fastapi/quickstart.py"
```

1. Annotate the parameter with the type to resolve
2. This will configure FastAPI to use Wirio's dependency injection

## Testing

Information available [here](../testing.md).
