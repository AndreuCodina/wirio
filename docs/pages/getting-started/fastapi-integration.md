# FastAPI integration

## Installation

Meanwhile we can install `Wirio` with `uv add wirio`, it's recommended to add the `fastapi` extra to ensure the installed FastAPI version is compatible.

```bash
uv add wirio[fastapi]
```

## Usage

Inject services into async endpoints using `Annotated[..., FromServices()]`.

```python hl_lines="26 34"
--8<-- "docs/code/getting_started/fastapi-integration/fastapi_integration.py"
```

1. This will configure FastAPI to use Wirio's dependency injection
