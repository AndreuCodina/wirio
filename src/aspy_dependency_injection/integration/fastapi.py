import functools
import inspect
from contextlib import asynccontextmanager
from contextvars import ContextVar
from inspect import Parameter
from typing import TYPE_CHECKING, Any

from fastapi.routing import APIRoute
from starlette.requests import Request
from starlette.websockets import WebSocket

from aspy_dependency_injection.types import InjectableType

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable, Sequence

    from fastapi import FastAPI
    from starlette.routing import BaseRoute
    from starlette.types import ASGIApp, Receive, Scope, Send

    from aspy_dependency_injection.service_collection import ServiceCollection
    from aspy_dependency_injection.types import AnyCallable

current_request: ContextVar[Request | WebSocket] = ContextVar("aspy_starlette_request")


def _update_lifespan(app: FastAPI, services: ServiceCollection) -> None:
    old_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def new_lifespan(app: FastAPI) -> AsyncGenerator[Any]:
        async with old_lifespan(app) as state:
            yield state

        await services.uninitialize()

    app.router.lifespan_context = new_lifespan


class _AspyAsgiMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in {"http", "websocket"}:
            return await self.app(scope, receive, send)

        if scope["type"] == "http":
            request = Request(scope, receive=receive, send=send)
        else:
            request = WebSocket(scope, receive, send)

        token = current_request.set(request)
        try:
            # async with request.app.state.aspy_services.create_scope() as service_scope:
            #     request.state.service_scope = service_scope
            #     await self.app(scope, receive, send)
            service_scope = request.app.state.aspy_services.create_scope()
            request.state.service_scope = service_scope
            await self.app(scope, receive, send)
        finally:
            current_request.reset(token)


def are_annotated_parameters_with_aspy_dependencies(
    target: AnyCallable,
) -> bool:
    for parameter in inspect.signature(target).parameters.values():
        if parameter.annotation is not None and isinstance(
            parameter.annotation, InjectableType
        ):
            return True

    return False


def _inject_routes(routes: list[BaseRoute], services: ServiceCollection) -> None:
    for route in routes:
        if not (
            isinstance(route, APIRoute)
            and route.dependant.call is not None
            and not are_annotated_parameters_with_aspy_dependencies(
                route.dependant.call
            )
        ):
            continue

        route.dependant.call = inject_from_container(route.dependant.call, services)


def inject_from_container(
    target: Callable[..., Any], services: ServiceCollection
) -> Callable[..., Any]:
    @functools.wraps(target)
    async def _inject_async_target(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
        parameters_to_inject = get_parameters_to_inject(target)
        parameters_to_inject_resolved: dict[str, Any] = {
            injected_parameter_name: services.get(injected_parameter_class)
            for injected_parameter_name, injected_parameter_class in parameters_to_inject.items()
        }
        return await target(*args, **{**kwargs, **parameters_to_inject_resolved})

    return _inject_async_target


def get_request_container() -> ServiceCollection:
    """When inside a request, returns the scoped container instance handling the current request.

    This is what you almost always want.It has all the information the app container has in addition
    to data specific to the current request.
    """
    return current_request.get().state.service_scope


def get_parameters_to_inject(
    target: AnyCallable,
) -> dict[str, type[Any]]:
    result: dict[str, type[Any]] = {}

    for parameter_name, parameter in inspect.signature(target).parameters.items():
        if parameter.annotation is Parameter.empty:
            continue

        injectable_dependency = get_injectable_dependency(
            parameter.annotation.__metadata__
        )

        if injectable_dependency is None:
            continue

        service_type = parameter.annotation.__args__[0]
        result[parameter_name] = service_type

    return result


def get_injectable_dependency(metadata: Sequence[Any]) -> InjectableType | None:
    for metadata_item in metadata:
        if hasattr(metadata_item, "dependency"):
            dependency = metadata_item.dependency()  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType, reportAttributeAccessIssue]

            if isinstance(dependency, InjectableType):
                return dependency

    return None


def setup(app: FastAPI, services: ServiceCollection) -> None:
    app.state.aspy_services = services
    app.add_middleware(_AspyAsgiMiddleware)
    _update_lifespan(app, services)
    _inject_routes(app.routes, services)
