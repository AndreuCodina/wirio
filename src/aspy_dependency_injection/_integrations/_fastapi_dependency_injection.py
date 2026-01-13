import functools
import inspect
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from contextvars import ContextVar
from inspect import Parameter
from typing import TYPE_CHECKING, Any, cast, final

from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.requests import Request
from starlette.routing import BaseRoute, Match
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.websockets import WebSocket

from aspy_dependency_injection._service_lookup._parameter_information import (
    ParameterInformation,
)
from aspy_dependency_injection.abstractions.base_service_provider import (
    BaseServiceProvider,
)
from aspy_dependency_injection.injectable import Injectable
from aspy_dependency_injection.service_provider import (
    ServiceProvider,
    ServiceScope,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from aspy_dependency_injection.service_collection import ServiceCollection


current_request: ContextVar[Request | WebSocket] = ContextVar("aspy_starlette_request")


@final
class FastApiDependencyInjection:
    @classmethod
    def setup(cls, app: FastAPI, services: "ServiceCollection") -> None:
        service_provider = services.build_service_provider()
        app.state.aspy_service_provider = service_provider
        app.add_middleware(_AspyAsgiMiddleware)
        cls._update_lifespan(app, service_provider)
        cls._inject_routes(app.routes)

    @classmethod
    def _update_lifespan(cls, app: FastAPI, service_provider: ServiceProvider) -> None:
        old_lifespan = app.router.lifespan_context

        @asynccontextmanager
        async def new_lifespan(app: FastAPI) -> AsyncGenerator[Any]:
            await service_provider.__aenter__()

            async with old_lifespan(app) as state:
                yield state

            await service_provider.__aexit__(None, None, None)

        app.router.lifespan_context = new_lifespan

    @classmethod
    def _are_annotated_parameters_with_aspy_dependencies(
        cls, target: Callable[..., Any]
    ) -> bool:
        for parameter in inspect.signature(target).parameters.values():
            if (
                parameter.annotation is not None
                and hasattr(parameter.annotation, "__metadata__")
                and hasattr(parameter.annotation.__metadata__[0], "dependency")
                and hasattr(
                    parameter.annotation.__metadata__[0].dependency,
                    "__is_aspy_depends__",
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
                and cls._are_annotated_parameters_with_aspy_dependencies(
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
        """When inside a request, returns the scoped container instance handling the current request.

        This is what you almost always want.It has all the information the app container has in addition
        to data specific to the current request.
        """
        return current_request.get().state.aspy_service_scope

    @classmethod
    def _get_parameters_to_inject(
        cls, target: Callable[..., Any]
    ) -> dict[str, ParameterInformation]:
        result: dict[str, ParameterInformation] = {}

        for parameter_name, parameter in inspect.signature(target).parameters.items():
            if parameter.annotation is Parameter.empty:
                continue

            injectable_dependency = cls._get_injectable_dependency(parameter)

            if injectable_dependency is None:
                continue

            parameter_information = ParameterInformation(parameter=parameter)
            result[parameter_name] = parameter_information

        return result

    @classmethod
    def _get_injectable_dependency(cls, parameter: Parameter) -> Injectable | None:
        if not hasattr(parameter.annotation, "__metadata__"):
            return None

        metadata: Sequence[Any] = parameter.annotation.__metadata__

        for metadata_item in metadata:
            if hasattr(metadata_item, "dependency") and hasattr(
                metadata_item.dependency, "__is_aspy_depends__"
            ):
                dependency = metadata_item.dependency()  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType, reportAttributeAccessIssue]

                if isinstance(dependency, Injectable):
                    return dependency

        return None

    @classmethod
    async def _resolve_injected_parameter(
        cls, parameter_information: ParameterInformation
    ) -> object | None:
        scoped_provider = cast(BaseServiceProvider, cls._get_request_container())
        parameter_service = await scoped_provider.get_service_object(
            parameter_information.parameter_type
        )

        if parameter_service is None:
            if parameter_information.is_optional:
                return None

            error_message = f"Unable to resolve service for type '{parameter_information.parameter_type}' while attempting to invoke endpoint"
            raise RuntimeError(error_message)

        return parameter_service


@final
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

            service_provider: ServiceProvider = request.app.state.aspy_service_provider

            async with service_provider.create_scope() as service_scope:
                request.state.aspy_service_scope = service_scope
                await self.app(scope, receive, send)
        finally:
            current_request.reset(token)
