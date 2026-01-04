import asyncio
from typing import TYPE_CHECKING, ClassVar, Final, final

from aspy_dependency_injection._async_concurrent_dictionary import (
    AsyncConcurrentDictionary,
)
from aspy_dependency_injection._service_lookup._async_factory_call_site import (
    AsyncFactoryCallSite,
)
from aspy_dependency_injection._service_lookup._constructor_call_site import (
    ConstructorCallSite,
)
from aspy_dependency_injection._service_lookup._constructor_information import (
    ConstructorInformation,
)
from aspy_dependency_injection._service_lookup._result_cache import ResultCache
from aspy_dependency_injection._service_lookup._service_call_site import (
    ServiceCallSite,
)
from aspy_dependency_injection._service_lookup._service_identifier import (
    ServiceIdentifier,
)
from aspy_dependency_injection._service_lookup._sync_factory_call_site import (
    SyncFactoryCallSite,
)
from aspy_dependency_injection._service_lookup.service_cache_key import ServiceCacheKey

if TYPE_CHECKING:
    from aspy_dependency_injection._service_lookup._call_site_chain import CallSiteChain
    from aspy_dependency_injection._service_lookup._parameter_information import (
        ParameterInformation,
    )
    from aspy_dependency_injection._service_lookup._typed_type import TypedType
    from aspy_dependency_injection.service_collection import ServiceCollection
    from aspy_dependency_injection.service_descriptor import ServiceDescriptor


@final
class CallSiteFactory:
    _DEFAULT_SLOT: ClassVar[int] = 0

    _descriptors: Final[list[ServiceDescriptor]]
    _descriptor_lookup: Final[dict[ServiceIdentifier, _ServiceDescriptorCacheItem]]
    _call_site_cache: Final[AsyncConcurrentDictionary[ServiceCacheKey, ServiceCallSite]]
    _call_site_locks: Final[AsyncConcurrentDictionary[ServiceIdentifier, asyncio.Lock]]

    def __init__(self, services: ServiceCollection) -> None:
        self._descriptors = services.descriptors.copy()
        self._descriptor_lookup = {}
        self._call_site_cache = AsyncConcurrentDictionary[
            ServiceCacheKey, ServiceCallSite
        ]()
        self._call_site_locks = AsyncConcurrentDictionary[
            ServiceIdentifier, asyncio.Lock
        ]()
        self._populate()

    async def get_call_site(
        self, service_identifier: ServiceIdentifier, call_site_chain: CallSiteChain
    ) -> ServiceCallSite | None:
        service_cache_key = ServiceCacheKey(service_identifier, self._DEFAULT_SLOT)
        service_call_site = self._call_site_cache.get(service_cache_key)

        if service_call_site is None:
            return await self._create_call_site(
                service_identifier=service_identifier, call_site_chain=call_site_chain
            )

        return service_call_site

    async def add(
        self, service_identifier: ServiceIdentifier, service_call_site: ServiceCallSite
    ) -> None:
        cache_key = ServiceCacheKey(service_identifier, self._DEFAULT_SLOT)
        await self._call_site_cache.upsert(key=cache_key, value=service_call_site)

    async def _create_call_site(
        self, service_identifier: ServiceIdentifier, call_site_chain: CallSiteChain
    ) -> ServiceCallSite | None:
        async def _create_new_lock(_: ServiceIdentifier) -> asyncio.Lock:
            return asyncio.Lock()

        # We need to lock the resolution process for a single service type at a time.
        # Consider the following:
        # C -> D -> A
        # E -> D -> A
        # Resolving C and E in parallel means that they will be modifying the callsite cache concurrently
        # to add the entry for C and E, but the resolution of D and A is synchronized
        # to make sure C and E both reference the same instance of the callsite.
        #
        # This is to make sure we can safely store singleton values on the callsites themselves

        call_site_lock = await self._call_site_locks.get_or_add(
            service_identifier, _create_new_lock
        )

        # Check if the lock is already acquired to prevent deadlocks in case of re-entrancy
        if call_site_lock.locked():
            call_site_chain.check_circular_dependency(service_identifier)

        async with call_site_lock:
            return await self._try_create_exact_from_service_identifier(
                service_identifier, call_site_chain
            )

    def _populate(self) -> None:
        for descriptor in self._descriptors:
            cache_key = ServiceIdentifier.from_descriptor(descriptor)
            cache_item = self._descriptor_lookup.get(
                cache_key, _ServiceDescriptorCacheItem()
            )
            self._descriptor_lookup[cache_key] = cache_item.add(descriptor)

    async def _try_create_exact_from_service_identifier(
        self, service_identifier: ServiceIdentifier, call_site_chain: CallSiteChain
    ) -> ServiceCallSite | None:
        service_descriptor_cache_item = self._descriptor_lookup.get(
            service_identifier, None
        )

        if service_descriptor_cache_item is not None:
            return await self._try_create_exact_from_service_descriptor(
                service_descriptor_cache_item.last,
                service_identifier,
                call_site_chain,
                self._DEFAULT_SLOT,
            )

        return None

    async def _try_create_exact_from_service_descriptor(
        self,
        service_descriptor: ServiceDescriptor,
        service_identifier: ServiceIdentifier,
        call_site_chain: CallSiteChain,
        slot: int,
    ) -> ServiceCallSite | None:
        if not self._should_create_exact(
            service_descriptor.service_type, service_identifier.service_type
        ):
            return None

        return await self._create_exact(
            service_descriptor, service_identifier, call_site_chain, slot
        )

    def _should_create_exact(
        self, descriptor_type: TypedType, service_type: TypedType
    ) -> bool:
        return descriptor_type == service_type

    async def _create_exact(
        self,
        service_descriptor: ServiceDescriptor,
        service_identifier: ServiceIdentifier,
        call_site_chain: CallSiteChain,
        slot: int,
    ) -> ServiceCallSite:
        call_site_key = ServiceCacheKey(service_identifier, slot)
        service_call_site = self._call_site_cache.get(call_site_key)

        if service_call_site is not None:
            return service_call_site

        cache = ResultCache.from_lifetime(
            service_descriptor.lifetime, service_identifier, slot
        )

        if service_descriptor.sync_implementation_factory is not None:
            assert service_descriptor.sync_implementation_factory is not None
            service_call_site = SyncFactoryCallSite(
                cache=cache,
                service_type=service_identifier.service_type,
                implementation_factory=service_descriptor.sync_implementation_factory,
            )
        elif service_descriptor.async_implementation_factory is not None:
            assert service_descriptor.async_implementation_factory is not None
            service_call_site = AsyncFactoryCallSite(
                cache=cache,
                service_type=service_identifier.service_type,
                implementation_factory=service_descriptor.async_implementation_factory,
            )
        elif service_descriptor.has_implementation_type():
            assert service_descriptor.implementation_type is not None
            service_call_site = await self._create_constructor_call_site(
                cache=cache,
                service_identifier=service_identifier,
                implementation_type=service_descriptor.implementation_type,
                call_site_chain=call_site_chain,
            )
        else:
            error_message = "Invalid service descriptor"
            raise RuntimeError(error_message)

        await self._call_site_cache.upsert(key=call_site_key, value=service_call_site)
        return service_call_site

    async def _create_constructor_call_site(
        self,
        cache: ResultCache,
        service_identifier: ServiceIdentifier,
        implementation_type: TypedType,
        call_site_chain: CallSiteChain,
    ) -> ServiceCallSite:
        try:
            call_site_chain.add(service_identifier, implementation_type)
            parameter_call_sites: list[ServiceCallSite | None] | None = None
            constructor_information = ConstructorInformation(implementation_type)
            parameters = constructor_information.get_parameters()
            parameter_call_sites = await self._create_argument_call_sites(
                parameters, call_site_chain
            )
            return ConstructorCallSite(
                cache=cache,
                service_type=service_identifier.service_type,
                constructor_information=constructor_information,
                parameters=parameters,
                parameter_call_sites=parameter_call_sites,
            )
        finally:
            call_site_chain.remove(service_identifier)

    async def _create_argument_call_sites(
        self, parameters: list[ParameterInformation], call_site_chain: CallSiteChain
    ) -> list[ServiceCallSite | None]:
        if len(parameters) == 0:
            return []

        parameter_call_sites: list[ServiceCallSite | None] = []

        for parameter in parameters:
            call_site = await self._create_call_site(
                ServiceIdentifier.from_service_type(parameter.parameter_type),
                call_site_chain,
            )

            if call_site is None:
                if parameter.is_optional or parameter.has_default_value:
                    parameter_call_sites.append(None)
                    continue

                error_message = f"Unable to resolve service with type '{parameter.parameter_type}' while attempting to activate a service"
                raise RuntimeError(error_message)

            parameter_call_sites.append(call_site)

        return parameter_call_sites


@final
class _ServiceDescriptorCacheItem:
    _item: ServiceDescriptor | None
    _items: list[ServiceDescriptor] | None

    def __init__(self) -> None:
        self._item = None
        self._items = None

    @property
    def last(self) -> ServiceDescriptor:
        if self._items is not None and len(self._items) > 0:
            return self._items[len(self._items) - 1]

        assert self._item is not None
        return self._item

    def add(self, descriptor: ServiceDescriptor) -> _ServiceDescriptorCacheItem:
        new_cache_item = _ServiceDescriptorCacheItem()

        if self._item is None:
            new_cache_item._item = descriptor
        else:
            new_cache_item._item = self._item
            new_cache_item._items = self._items if self._items is not None else []
            new_cache_item._items.append(descriptor)

        return new_cache_item
