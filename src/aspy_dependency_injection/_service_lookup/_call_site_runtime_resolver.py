import inspect
import typing
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Flag
from typing import (
    ClassVar,
    final,
    override,
)

from aspy_dependency_injection._aspy_undefined import AspyUndefined
from aspy_dependency_injection._service_lookup._async_factory_call_site import (
    AsyncFactoryCallSite,
)
from aspy_dependency_injection._service_lookup._call_site_visitor import CallSiteVisitor
from aspy_dependency_injection._service_lookup._constant_call_site import (
    ConstantCallSite,
)
from aspy_dependency_injection._service_lookup._constructor_call_site import (
    ConstructorCallSite,
)
from aspy_dependency_injection._service_lookup._parameter_information import (
    ParameterInformation,
)
from aspy_dependency_injection._service_lookup._service_call_site import (
    ServiceCallSite,
)
from aspy_dependency_injection._service_lookup._service_provider_call_site import (
    ServiceProviderCallSite,
)
from aspy_dependency_injection._service_lookup._supports_async_context_manager import (
    SupportsAsyncContextManager,
)
from aspy_dependency_injection._service_lookup._supports_context_manager import (
    SupportsContextManager,
)
from aspy_dependency_injection._service_lookup._sync_factory_call_site import (
    SyncFactoryCallSite,
)
from aspy_dependency_injection._service_lookup._typed_type import TypedType
from aspy_dependency_injection.service_provider_engine_scope import (
    ServiceProviderEngineScope,
)


class _RuntimeResolverLock(Flag):
    NONE = 0
    SCOPE = 1
    ROOT = 2


@dataclass(frozen=True)
class RuntimeResolverContext:
    scope: ServiceProviderEngineScope
    acquired_locks: _RuntimeResolverLock


@final
class CallSiteRuntimeResolver(CallSiteVisitor[RuntimeResolverContext, object | None]):
    INSTANCE: ClassVar["CallSiteRuntimeResolver"]

    async def resolve(
        self, call_site: ServiceCallSite, scope: ServiceProviderEngineScope
    ) -> object | None:
        # Fast path to avoid virtual calls if we already have the cached value in the root scope
        if scope.is_root_scope and call_site.value is not None:
            return call_site.value

        return await self._visit_call_site(
            call_site,
            RuntimeResolverContext(
                scope=scope, acquired_locks=_RuntimeResolverLock.NONE
            ),
        )

    @override
    async def _visit_root_cache(
        self, call_site: ServiceCallSite, argument: RuntimeResolverContext
    ) -> object | None:
        # If the value is already calculated, return it directly
        if call_site.value is not None:
            return call_site.value

        lock_type = _RuntimeResolverLock.ROOT
        service_provider_engine_scope = argument.scope.root_provider.root

        async with call_site.lock:
            # Lock the call_site and check if another coroutine already cached the value
            if call_site.value is not None:
                return call_site.value

            resolved_service = await self._visit_call_site_main(
                call_site=call_site,
                argument=RuntimeResolverContext(
                    scope=service_provider_engine_scope,
                    acquired_locks=argument.acquired_locks | lock_type,
                ),
            )
            await service_provider_engine_scope.capture_disposable(resolved_service)
            call_site.value = resolved_service
            return resolved_service

    @override
    async def _visit_scope_cache(
        self, call_site: ServiceCallSite, argument: RuntimeResolverContext
    ) -> object | None:
        # Check if we are in the situation where scoped service was promoted to singleton
        # and we need to lock the root
        if argument.scope.is_root_scope:
            return await self._visit_root_cache(call_site, argument)

        return await self._visit_cache(
            call_site, argument, argument.scope, _RuntimeResolverLock.SCOPE
        )

    async def _visit_cache(
        self,
        call_site: ServiceCallSite,
        argument: RuntimeResolverContext,
        service_provider_engine_scope: ServiceProviderEngineScope,
        lock_type: _RuntimeResolverLock,
    ) -> object | None:
        is_lock_taken = False
        resolved_services_lock = service_provider_engine_scope.resolved_services_lock
        resolved_services = service_provider_engine_scope.resolved_services

        # Taking locks only once allows us to fork resolution process
        # on another coroutine without causing the deadlock because we
        # always know that we are going to wait the other coroutine to finish before
        # releasing the lock
        if (argument.acquired_locks & lock_type) == _RuntimeResolverLock.NONE:
            await resolved_services_lock.acquire()
            is_lock_taken = True

        try:
            # Note: This method has already taken lock by the caller for resolution and access synchronization.
            # For scoped: takes a dictionary as both a resolution lock and a dictionary access lock.
            resolved_service = resolved_services.get(
                call_site.cache.key, AspyUndefined.INSTANCE
            )

            if resolved_service is not AspyUndefined.INSTANCE:
                return resolved_service

            resolved_service = await self._visit_call_site_main(
                call_site=call_site,
                argument=RuntimeResolverContext(
                    scope=service_provider_engine_scope,
                    acquired_locks=argument.acquired_locks | lock_type,
                ),
            )
            await service_provider_engine_scope.capture_disposable(resolved_service)
            resolved_services[call_site.cache.key] = resolved_service
            return resolved_service
        finally:
            if is_lock_taken:
                resolved_services_lock.release()

    @override
    async def _visit_dispose_cache(
        self, call_site: ServiceCallSite, argument: RuntimeResolverContext
    ) -> object | None:
        service = await self._visit_call_site_main(call_site, argument)
        return await argument.scope.capture_disposable(service)

    @override
    async def _visit_constructor(
        self,
        constructor_call_site: ConstructorCallSite,
        argument: RuntimeResolverContext,
    ) -> object:
        parameter_values: list[object | None] = []

        for parameter, parameter_call_site in zip(
            constructor_call_site.parameters,
            constructor_call_site.parameter_call_sites,
            strict=True,
        ):
            if parameter_call_site is None:
                if parameter.has_default_value:
                    parameter_values.append(parameter.default_value)
                    continue

                if parameter.is_optional:
                    parameter_values.append(None)
                    continue

                raise self._build_constructor_parameter_resolution_error(
                    parameter, constructor_call_site.service_type
                )

            parameter_service = await self._visit_call_site(
                parameter_call_site, argument
            )

            if parameter_service is None and not parameter.is_optional:
                raise self._build_constructor_parameter_resolution_error(
                    parameter, constructor_call_site.service_type
                )

            parameter_values.append(parameter_service)

        service = constructor_call_site.constructor_information.invoke(parameter_values)

        if isinstance(service, SupportsAsyncContextManager):
            await service.__aenter__()
        elif isinstance(service, SupportsContextManager):
            service.__enter__()

        return service

    @override
    def _visit_constant(
        self,
        constant_call_site: ConstantCallSite,
        argument: RuntimeResolverContext,
    ) -> object:
        return constant_call_site.default_value

    @override
    async def _visit_sync_factory(
        self,
        sync_factory_call_site: SyncFactoryCallSite,
        argument: RuntimeResolverContext,
    ) -> object | None:
        parameter_services = await self.get_parameter_services(
            sync_factory_call_site.implementation_factory, argument.scope
        )
        service = sync_factory_call_site.implementation_factory(*parameter_services)

        if isinstance(service, SupportsAsyncContextManager):
            await service.__aenter__()
        elif isinstance(service, SupportsContextManager):
            service.__enter__()

        return service

    @override
    async def _visit_async_factory(
        self,
        async_factory_call_site: AsyncFactoryCallSite,
        argument: RuntimeResolverContext,
    ) -> object | None:
        parameter_services = await self.get_parameter_services(
            async_factory_call_site.implementation_factory, argument.scope
        )
        service = await async_factory_call_site.implementation_factory(
            *parameter_services
        )

        if isinstance(service, SupportsAsyncContextManager):
            await service.__aenter__()
        elif isinstance(service, SupportsContextManager):
            service.__enter__()

        return service

    @override
    def _visit_service_provider(
        self,
        service_provider_call_site: ServiceProviderCallSite,
        argument: RuntimeResolverContext,
    ) -> object | None:
        return argument.scope

    async def get_parameter_services(
        self,
        implementation_factory: Callable[..., Awaitable[object]]
        | Callable[..., object],
        scope: ServiceProviderEngineScope,
    ) -> list[object | None]:
        parameter_services: list[object | None] = []
        signature = inspect.signature(implementation_factory)

        for parameter in signature.parameters.values():
            parameter_information = ParameterInformation(parameter)
            parameter_service = await scope.get_service_object(
                parameter_information.parameter_type
            )

            if parameter_service is None:
                if parameter_information.has_default_value:
                    parameter_services.append(parameter_information.default_value)
                elif parameter_information.is_optional:
                    parameter_services.append(None)
                else:
                    error_message = f"Unable to resolve service for type '{parameter_information.parameter_type}'"
                    raise RuntimeError(error_message)
            else:
                parameter_services.append(parameter_service)

        return parameter_services

    def _get_parameter_types(
        self,
        implementation_factory: Callable[..., Awaitable[object]]
        | Callable[..., object],
    ) -> list[type]:
        type_hints: dict[str, type] = typing.get_type_hints(implementation_factory)
        return [
            parameter_type
            for parameter_name, parameter_type in type_hints.items()
            if parameter_name != "return"
        ]

    def _build_constructor_parameter_resolution_error(
        self, parameter_information: ParameterInformation, service_type: TypedType
    ) -> RuntimeError:
        return RuntimeError(
            f"Unable to resolve service with type '{parameter_information.parameter_type}' while attempting to activate '{service_type}'"
        )


CallSiteRuntimeResolver.INSTANCE = CallSiteRuntimeResolver()
