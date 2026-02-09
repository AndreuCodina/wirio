from fastapi import FastAPI

from wirio.service_container import ServiceContainer
from wirio.service_provider import ServiceProvider


def get_services(app: FastAPI) -> ServiceContainer:
    return app.state.wirio_services


def get_service_provider(app: FastAPI) -> ServiceProvider:
    return app.state.wirio_service_provider
