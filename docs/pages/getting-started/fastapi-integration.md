# FastAPI integration

Inject services into async endpoints using `Annotated[..., FromServices()]`.

```python hl_lines="26 34"
--8<-- "docs/code/getting_started/fastapi-integration/fastapi_integration.py"
```

1. This will configure FastAPI to use Wirio's dependency injection
