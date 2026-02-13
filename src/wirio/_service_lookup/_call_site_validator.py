from dataclasses import dataclass
from typing import Final, final, override

from wirio._service_lookup._async_concurrent_dictionary import AsyncConcurrentDictionary
from wirio._service_lookup._async_factory_call_site import AsyncFactoryCallSite
from wirio._service_lookup._call_site_visitor import CallSiteVisitor
from wirio._service_lookup._constant_call_site import ConstantCallSite
from wirio._service_lookup._constructor_call_site import ConstructorCallSite
from wirio._service_lookup._sequence_call_site import SequenceCallSite
from wirio._service_lookup._service_call_site import ServiceCallSite
from wirio._service_lookup._service_provider_call_site import ServiceProviderCallSite
from wirio._service_lookup._sync_factory_call_site import SyncFactoryCallSite
from wirio._service_lookup._typed_type import TypedType
from wirio._service_lookup.service_cache_key import ServiceCacheKey
from wirio.abstractions.service_scope import ServiceScope
from wirio.abstractions.service_scope_factory import ServiceScopeFactory
from wirio.exceptions import (
    DirectScopedResolvedFromRootError,
    ScopedInSingletonError,
    ScopedResolvedFromRootError,
)


@final
@dataclass
class _CallSiteValidatorState:
    singleton: ServiceCallSite | None


@final
class CallSiteValidator(CallSiteVisitor[_CallSiteValidatorState, TypedType | None]):
    # Keys are services being resolved via `get_service`, values - first scoped service in their call site tree
    _scoped_services: Final[
        AsyncConcurrentDictionary[ServiceCacheKey, TypedType | None]
    ]

    def __init__(self) -> None:
        self._scoped_services = AsyncConcurrentDictionary()

    @override
    async def _visit_call_site(
        self, call_site: ServiceCallSite, argument: _CallSiteValidatorState
    ) -> TypedType | None:
        # First, check if we have encountered this call site before to prevent visiting call site trees that have already been visited
        # If first_scoped_service_in_call_site_tree is null there are no scoped dependencies in this service's call site tree
        # If first_scoped_service_in_call_site_tree has a value, it contains the first scoped service in this service's call site tree

        first_scoped_service_in_call_site_tree = self._scoped_services.get(
            call_site.cache.key
        )

        if first_scoped_service_in_call_site_tree is None:
            # This call site wasn't cached yet, walk the tree
            first_scoped_service_in_call_site_tree = await super()._visit_call_site(
                call_site, argument
            )

            # Cache the result
            await self._scoped_services.upsert(
                call_site.cache.key, first_scoped_service_in_call_site_tree
            )

        # If there is a scoped service in the call site tree, make sure we are not resolving it from a singleton
        if (
            first_scoped_service_in_call_site_tree is not None
            and argument.singleton is not None
        ):
            raise ScopedInSingletonError(
                call_site.service_type, argument.singleton.service_type
            )

        return first_scoped_service_in_call_site_tree

    async def _visit_root_cache(
        self, call_site: ServiceCallSite, argument: _CallSiteValidatorState
    ) -> TypedType | None:
        argument.singleton = call_site
        return await self._visit_call_site_main(call_site, argument)

    async def _visit_scope_cache(
        self, call_site: ServiceCallSite, argument: _CallSiteValidatorState
    ) -> TypedType | None:
        # We are fine with having ServiceScopeFactory requested by singletons
        if call_site.service_type == TypedType.from_type(ServiceScopeFactory):
            return None

        await self._visit_call_site_main(call_site, argument)
        return call_site.service_type

    @override
    async def _visit_constructor(
        self,
        constructor_call_site: ConstructorCallSite,
        argument: _CallSiteValidatorState,
    ) -> TypedType | None:
        result: TypedType | None = None

        for parameter_call_site in constructor_call_site.parameter_call_sites:
            if parameter_call_site is not None:
                scoped = await self._visit_call_site(parameter_call_site, argument)

                if scoped is not None and result is None:
                    result = scoped

        return result

    @override
    def _visit_constant(
        self, constant_call_site: ConstantCallSite, argument: _CallSiteValidatorState
    ) -> TypedType | None:
        return None

    @override
    async def _visit_sync_factory(
        self,
        sync_factory_call_site: SyncFactoryCallSite,
        argument: _CallSiteValidatorState,
    ) -> TypedType | None:
        return None

    @override
    async def _visit_async_factory(
        self,
        async_factory_call_site: AsyncFactoryCallSite,
        argument: _CallSiteValidatorState,
    ) -> TypedType | None:
        return None

    @override
    async def _visit_sequence(
        self, sequence_call_site: SequenceCallSite, argument: _CallSiteValidatorState
    ) -> TypedType | None:
        result: TypedType | None = None

        for service_call_site in sequence_call_site.service_call_sites:
            scoped = await self._visit_call_site(service_call_site, argument)

            if result is None:
                result = scoped

        return result

    @override
    def _visit_service_provider(
        self,
        service_provider_call_site: ServiceProviderCallSite,
        argument: _CallSiteValidatorState,
    ) -> TypedType | None:
        return None

    async def validate_call_site(self, call_site: "ServiceCallSite") -> None:
        default = _CallSiteValidatorState(singleton=None)
        await self._visit_call_site(call_site, default)

    def validate_resolution(
        self, call_site: ServiceCallSite, scope: ServiceScope, root_scope: ServiceScope
    ) -> None:
        if scope is not root_scope:
            return

        scoped_service = self._scoped_services.get(call_site.cache.key)

        if scoped_service is None:
            return

        service_type = call_site.service_type

        if service_type == scoped_service:
            raise DirectScopedResolvedFromRootError(service_type)

        raise ScopedResolvedFromRootError(service_type, scoped_service)
