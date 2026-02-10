from fastapi import FastAPI

from wirio.service_container import ServiceContainer
from wirio.service_provider import ServiceProvider


def get_service_provider(app: FastAPI) -> ServiceProvider:
    assert isinstance(app.state.wirio_service_provider, ServiceProvider)
    return app.state.wirio_service_provider


def get_service_container(app: FastAPI) -> ServiceContainer:
    assert isinstance(app.state.wirio_services, ServiceContainer)
    return app.state.wirio_services
