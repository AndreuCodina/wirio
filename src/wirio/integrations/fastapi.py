from fastapi import FastAPI

from wirio.service_provider import ServiceProvider


def get_service_provider(app: FastAPI) -> ServiceProvider:
    return app.state.wirio_service_provider
