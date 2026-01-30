import functools
import inspect
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from contextvars import ContextVar
from inspect import Parameter
from typing import TYPE_CHECKING, Any, final

from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.requests import Request
from starlette.routing import BaseRoute, Match
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.websockets import WebSocket

from wirio._service_lookup._parameter_information import (
    ParameterInformation,
)
from wirio._utils._param_utils import ParamUtils
from wirio.abstractions.service_scope import ServiceScope
from wirio.annotations import FromKeyedServicesInjectable
from wirio.exceptions import CannotResolveServiceFromEndpointError

if TYPE_CHECKING:
    from wirio.service_collection import ServiceCollection
    from wirio.service_provider import ServiceProvider


current_request: ContextVar[Request | WebSocket] = ContextVar("wirio_starlette_request")


@final
class FastApiDependencyInjection:
    @classmethod
    def setup(cls, app: FastAPI, services: "ServiceCollection") -> None:
        service_provider = services.build_service_provider()
        app.state.wirio_service_provider = service_provider
        app.add_middleware(_WirioAsgiMiddleware)
        cls._update_lifespan(app, service_provider)
        cls._inject_routes(app.routes)

    @classmethod
    def _update_lifespan(
        cls, app: FastAPI, service_provider: "ServiceProvider"
    ) -> None:
        old_lifespan = app.router.lifespan_context

        @asynccontextmanager
        async def new_lifespan(app: FastAPI) -> AsyncGenerator[Any]:
            await service_provider.__aenter__()

            async with old_lifespan(app) as state:
                yield state

            await service_provider.__aexit__(None, None, None)

        app.router.lifespan_context = new_lifespan

    @classmethod
    def _are_annotated_parameters_with_wirio_dependencies(
        cls, target: Callable[..., Any]
    ) -> bool:
        for parameter in inspect.signature(target).parameters.values():
            if (
                parameter.annotation is not None
                and hasattr(parameter.annotation, "__metadata__")
                and hasattr(parameter.annotation.__metadata__[0], "dependency")
                and hasattr(
                    parameter.annotation.__metadata__[0].dependency,
                    "__is_wirio_depends__",
                )
            ):
                return True

        return False

    @classmethod
    def _inject_routes(cls, routes: list[BaseRoute]) -> None:
        for route in routes:
            if not (
                isinstance(route, APIRoute)
                and route.dependant.call is not None
                and inspect.iscoroutinefunction(route.dependant.call)
                and cls._are_annotated_parameters_with_wirio_dependencies(
                    route.dependant.call
                )
            ):
                continue

            route.dependant.call = cls._inject_from_container(route.dependant.call)

    @classmethod
    def _inject_from_container(cls, target: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(target)
        async def _inject_async_target(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            parameters_to_inject = cls._get_parameters_to_inject(target)
            parameters_to_inject_resolved: dict[str, Any] = {
                injected_parameter_name: await cls._resolve_injected_parameter(
                    parameter_information
                )
                for injected_parameter_name, parameter_information in parameters_to_inject.items()
            }
            return await target(*args, **{**kwargs, **parameters_to_inject_resolved})

        return _inject_async_target

    @classmethod
    def _get_request_container(cls) -> ServiceScope:
        """When inside a request, return the scoped container instance handling the current request.

        This is what we almost always want. It has all the information the app container has in addition
        to data specific to the current request.
        """
        return current_request.get().state.wirio_service_scope

    @classmethod
    def _get_parameters_to_inject(
        cls, target: Callable[..., Any]
    ) -> dict[str, ParameterInformation]:
        result: dict[str, ParameterInformation] = {}

        for parameter_name, parameter in inspect.signature(target).parameters.items():
            if parameter.annotation is Parameter.empty:
                continue

            injectable_dependency = ParamUtils.get_injectable_dependency(parameter)

            if injectable_dependency is None:
                continue

            parameter_information = ParameterInformation(parameter=parameter)
            result[parameter_name] = parameter_information

        return result

    @classmethod
    async def _resolve_injected_parameter(
        cls, parameter_information: ParameterInformation
    ) -> object | None:
        parameter_service: object | None

        if isinstance(
            parameter_information.injectable_dependency, FromKeyedServicesInjectable
        ):
            parameter_service = await cls._get_request_container().service_provider.get_keyed_service_object(
                parameter_information.injectable_dependency.key,
                parameter_information.parameter_type,
            )
        else:
            parameter_service = (
                await cls._get_request_container().service_provider.get_service_object(
                    parameter_information.parameter_type
                )
            )

        if parameter_service is None:
            if parameter_information.is_optional:
                return None

            raise CannotResolveServiceFromEndpointError(
                parameter_information.parameter_type
            )

        return parameter_service


@final
class _WirioAsgiMiddleware:
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
            is_async_endpoint = False

            for route in scope["app"].routes:
                if (
                    isinstance(route, APIRoute)
                    and route.matches(scope)[0] == Match.FULL
                ):
                    original = inspect.unwrap(route.dependant.call)  # pyright: ignore[reportArgumentType]
                    is_async_endpoint = inspect.iscoroutinefunction(original)

                    if is_async_endpoint:
                        break

            if not is_async_endpoint:
                await self.app(scope, receive, send)
                return None

            services: ServiceProvider = request.app.state.wirio_service_provider

            async with services.create_scope() as service_scope:
                request.state.wirio_service_scope = service_scope
                await self.app(scope, receive, send)
        finally:
            current_request.reset(token)
