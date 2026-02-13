from collections.abc import Generator, Iterator, Sequence
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from typing import ClassVar, Final, final, override

from wirio._service_lookup._async_concurrent_dictionary import (
    AsyncConcurrentDictionary,
)
from wirio._service_lookup._async_factory_call_site import (
    AsyncFactoryCallSite,
)
from wirio._service_lookup._asyncio_reentrant_lock import AsyncioReentrantLock
from wirio._service_lookup._call_site_chain import CallSiteChain
from wirio._service_lookup._constant_call_site import (
    ConstantCallSite,
)
from wirio._service_lookup._constructor_call_site import (
    ConstructorCallSite,
)
from wirio._service_lookup._constructor_information import (
    ConstructorInformation,
)
from wirio._service_lookup._parameter_information import (
    ParameterInformation,
)
from wirio._service_lookup._result_cache import ResultCache
from wirio._service_lookup._sequence_call_site import SequenceCallSite
from wirio._service_lookup._service_call_site import (
    ServiceCallSite,
)
from wirio._service_lookup._service_identifier import (
    ServiceIdentifier,
)
from wirio._service_lookup._sync_factory_call_site import (
    SyncFactoryCallSite,
)
from wirio._service_lookup._typed_type import TypedType
from wirio._service_lookup.call_site_result_cache_location import (
    CallSiteResultCacheLocation,
)
from wirio._service_lookup.service_cache_key import ServiceCacheKey
from wirio.abstractions.base_service_provider import BaseServiceProvider
from wirio.abstractions.keyed_service import KeyedService
from wirio.abstractions.service_key_lookup_mode import (
    ServiceKeyLookupMode,
)
from wirio.abstractions.service_provider_is_keyed_service import (
    ServiceProviderIsKeyedService,
)
from wirio.abstractions.service_provider_is_service import (
    ServiceProviderIsService,
)
from wirio.abstractions.service_scope_factory import (
    ServiceScopeFactory,
)
from wirio.annotations import (
    FromKeyedServicesInjectable,
    ServiceKeyInjectable,
)
from wirio.exceptions import (
    CannotResolveServiceError,
    InvalidServiceDescriptorError,
    InvalidServiceKeyTypeError,
    ServiceDescriptorDoesNotExistError,
)
from wirio.service_descriptor import ServiceDescriptor


@final
class ServiceDescriptorCacheItem:
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

    def add(self, descriptor: ServiceDescriptor) -> "ServiceDescriptorCacheItem":
        new_cache_item = ServiceDescriptorCacheItem()

        if self._item is None:
            new_cache_item._item = descriptor
        else:
            new_cache_item._item = self._item
            new_cache_item._items = self._items if self._items is not None else []
            new_cache_item._items.append(descriptor)

        return new_cache_item

    def __len__(self) -> int:
        if self._item is None:
            assert self._items is None
            return 0

        items_count = len(self._items) if self._items is not None else 0
        return items_count + 1

    def get_slot(self, service_descriptor: ServiceDescriptor) -> int:
        if service_descriptor == self._item:
            return len(self) - 1

        if self._items is not None:
            index: int | None = None

            with suppress(ValueError):
                index = self._items.index(service_descriptor)

            if index is not None:
                return len(self._items) - (index + 1)

        raise ServiceDescriptorDoesNotExistError

    def __iter__(self) -> Iterator[ServiceDescriptor]:
        if self._item is None:
            return iter([])

        if self._items is None:
            return iter([self._item])

        items: list[ServiceDescriptor] = [self._item]
        items.extend(self._items)
        return iter(items)


@final
@dataclass(frozen=True)
class _ServiceOverride:
    exists: bool
    value: object | None = None


@final
class CallSiteFactory(ServiceProviderIsKeyedService, ServiceProviderIsService):
    _DEFAULT_SLOT: ClassVar[int] = 0

    _descriptors: Final[list[ServiceDescriptor]]
    _descriptor_lookup: Final[dict[ServiceIdentifier, ServiceDescriptorCacheItem]]
    _call_site_cache: Final[AsyncConcurrentDictionary[ServiceCacheKey, ServiceCallSite]]
    _call_site_locks: Final[
        AsyncConcurrentDictionary[ServiceIdentifier, AsyncioReentrantLock]
    ]
    _service_overrides: Final[dict[ServiceIdentifier, list[object | None]]]
    _service_type_to_cache_keys: Final[dict[TypedType, set[ServiceCacheKey]]]
    _dirty_service_types: Final[set[TypedType]]
    _service_type_invalidation_lock: Final[AsyncioReentrantLock]

    def __init__(self, descriptors: list["ServiceDescriptor"]) -> None:
        self._descriptors = descriptors.copy()
        self._descriptor_lookup = {}
        self._call_site_cache = AsyncConcurrentDictionary[
            ServiceCacheKey, ServiceCallSite
        ]()
        self._call_site_locks = AsyncConcurrentDictionary[
            ServiceIdentifier, AsyncioReentrantLock
        ]()
        self._service_overrides = {}
        self._service_type_to_cache_keys = {}
        self._dirty_service_types = set()
        self._service_type_invalidation_lock = AsyncioReentrantLock()
        self._populate(self._descriptors)

    @override
    def is_service(self, service_type: type) -> bool:
        return self._is_service(
            ServiceIdentifier.from_service_type(
                service_type=TypedType.from_type(service_type)
            )
        )

    @override
    def is_keyed_service(self, service_key: object | None, service_type: type) -> bool:
        return self._is_service(
            ServiceIdentifier.from_service_type(
                service_type=TypedType.from_type(service_type), service_key=service_key
            )
        )

    async def get_call_site_from_service_identifier(
        self, service_identifier: ServiceIdentifier, call_site_chain: CallSiteChain
    ) -> ServiceCallSite | None:
        await self._invalidate_service_type_if_needed(service_identifier.service_type)
        overridden_call_site = self.get_overridden_call_site(service_identifier)

        if overridden_call_site is not None:
            return overridden_call_site

        service_cache_key = self._create_service_cache_key(
            service_identifier, self._DEFAULT_SLOT
        )
        service_call_site = self._call_site_cache.get(service_cache_key)

        if service_call_site is None:
            return await self._create_call_site(
                service_identifier=service_identifier, call_site_chain=call_site_chain
            )

        return service_call_site

    async def get_call_site_from_service_descriptor(
        self, service_descriptor: ServiceDescriptor, call_site_chain: CallSiteChain
    ) -> ServiceCallSite | None:
        await self._invalidate_service_type_if_needed(service_descriptor.service_type)
        service_identifier = ServiceIdentifier.from_descriptor(service_descriptor)
        service_descriptor_cache_item = self._descriptor_lookup.get(service_identifier)

        if service_descriptor_cache_item is not None:
            return await self._try_create_exact_from_service_descriptor(
                service_descriptor,
                service_identifier,
                call_site_chain,
                service_descriptor_cache_item.get_slot(service_descriptor),
            )

        return None

    async def add(
        self, service_identifier: ServiceIdentifier, service_call_site: ServiceCallSite
    ) -> None:
        cache_key = self._create_service_cache_key(
            service_identifier, self._DEFAULT_SLOT
        )
        await self._call_site_cache.upsert(key=cache_key, value=service_call_site)
        self._track_cache_key(service_identifier.service_type, cache_key)

    @contextmanager
    def override_service(
        self,
        service_identifier: ServiceIdentifier,
        implementation_instance: object | None,
    ) -> Generator[None]:
        self._add_override(service_identifier, implementation_instance)

        try:
            yield
        finally:
            self._remove_override(service_identifier)

    def get_overridden_call_site(
        self, service_identifier: ServiceIdentifier
    ) -> ServiceCallSite | None:
        service_override = self._get_service_override(service_identifier)

        if not service_override.exists:
            return None

        return ConstantCallSite(
            service_type=service_identifier.service_type,
            default_value=service_override.value,
            service_key=service_identifier.service_key,
        )

    def add_descriptor(self, descriptor: ServiceDescriptor) -> None:
        self._descriptors.append(descriptor)
        self._populate([descriptor])
        self.mark_service_type_dirty(descriptor.service_type)

    def mark_service_type_dirty(self, service_type: TypedType) -> None:
        self._dirty_service_types.add(service_type)

    async def try_create_sequence(  # noqa: C901, PLR0915
        self, service_identifier: ServiceIdentifier, call_site_chain: CallSiteChain
    ) -> ServiceCallSite | None:
        call_site_key = ServiceCacheKey(service_identifier, slot=self._DEFAULT_SLOT)

        if (service_call_site := self._call_site_cache.get(call_site_key)) is not None:
            return service_call_site

        try:
            call_site_chain.add(service_identifier)
            service_type = service_identifier.service_type

            if (
                not service_type.is_generic_type
                or service_type.get_generic_type_definition()
                != TypedType.from_type(Sequence)
            ):
                return None

            item_type = service_type.generic_type_arguments()[0]
            cache_key = ServiceIdentifier.from_service_type(
                service_type=item_type, service_key=service_identifier.service_key
            )

            cache_location = CallSiteResultCacheLocation.ROOT
            service_call_sites: list[ServiceCallSite] = []
            is_any_key_lookup = service_identifier.service_key == KeyedService.ANY_KEY

            # If `item_type` is not generic we can safely use descriptor cache
            # Special case for `KeyedService.ANY_KEY`, we don't want to check the cache because a `KeyedService.ANY_KEY` registration
            # will "hide" all the other service registration
            if (
                not item_type.is_generic_type
                and not is_any_key_lookup
                and (service_descriptors := self._descriptor_lookup.get(cache_key))
                is not None
            ):
                # Last service will get slot 0
                slot = len(service_descriptors)

                for service_descriptor in service_descriptors:
                    # There are no open generics here, so we only need to call `_create_exact`
                    slot -= 1
                    service_call_site = await self._create_exact(
                        service_descriptor=service_descriptor,
                        service_identifier=cache_key,
                        call_site_chain=call_site_chain,
                        slot=slot,
                    )
                    cache_location = self._get_common_cache_location(
                        cache_location, service_call_site.cache.location
                    )
                    service_call_sites.append(service_call_site)
            else:
                # We need to construct a list of matching call sites in declaration order, but to ensure
                # correct caching we must assign slots in reverse declaration order and with slots being
                # given out first to any exact matches before any open generic matches. Therefore, we
                # iterate over the descriptors twice in reverse, catching exact matches on the first pass
                # and open generic matches on the second pass.

                service_call_sites_by_index: list[tuple[int, ServiceCallSite]] = []
                keyed_slot_assignment: dict[ServiceIdentifier, int] | None = None
                slot = 0

                def keys_match(
                    lookup_key: object | None, descriptor_key: object | None
                ) -> bool:
                    if lookup_key is None and descriptor_key is None:
                        # Both are non keyed services
                        return True

                    if lookup_key is not None and descriptor_key is not None:
                        # Both are keyed services

                        # We don't want to return `ANY_KEY` registration, so ignore it
                        if descriptor_key is KeyedService.ANY_KEY:
                            return False

                        # Check if both keys are equal, or if the lookup key
                        # should matches all keys (except `ANY_KEY`)
                        return (
                            lookup_key == descriptor_key
                            or lookup_key is KeyedService.ANY_KEY
                        )

                    # One is a keyed service, one is not
                    return False

                def get_slot(key: ServiceIdentifier) -> int:
                    if not is_any_key_lookup:
                        return slot

                    # Each unique key (including its service type) maintains its own slot counter for ordering and identity

                    nonlocal keyed_slot_assignment

                    if keyed_slot_assignment is None:
                        keyed_slot_assignment = {key: 0}
                        return 0

                    if (existing_slot := keyed_slot_assignment.get(key)) is not None:
                        return existing_slot

                    keyed_slot_assignment[key] = 0
                    return 0

                def add_service_call_site(
                    service_call_site: ServiceCallSite, index: int
                ) -> None:
                    nonlocal cache_location
                    cache_location = self._get_common_cache_location(
                        cache_location, service_call_site.cache.location
                    )
                    service_call_sites_by_index.append((index, service_call_site))

                def update_slot(key: ServiceIdentifier) -> None:
                    if not is_any_key_lookup:
                        nonlocal slot
                        slot += 1
                    else:
                        assert keyed_slot_assignment is not None
                        keyed_slot_assignment[key] = slot + 1

                # Do the exact matches first
                for i, service_descriptor in reversed(
                    list(enumerate(self._descriptors))
                ):
                    if keys_match(
                        cache_key.service_key, service_descriptor.service_key
                    ) and self._should_create_exact(
                        service_descriptor.service_type, cache_key.service_type
                    ):
                        # For `ANY_KEY`, we want to cache based on descriptor identity, not `ANY_KEY` that cacheKey has
                        registration_key = (
                            service_identifier.from_descriptor(service_descriptor)
                            if is_any_key_lookup
                            else cache_key
                        )
                        slot = get_slot(registration_key)
                        service_call_site = await self._create_exact(
                            service_descriptor=service_descriptor,
                            service_identifier=registration_key,
                            call_site_chain=call_site_chain,
                            slot=slot,
                        )
                        add_service_call_site(service_call_site, i)
                        update_slot(registration_key)

                service_call_sites_by_index.sort(key=lambda x: x[0])
                service_call_sites = [x[1] for x in service_call_sites_by_index]

            result_cache = (
                ResultCache(cache_location, call_site_key)
                if cache_location is CallSiteResultCacheLocation.SCOPE
                or cache_location is CallSiteResultCacheLocation.ROOT
                else ResultCache(CallSiteResultCacheLocation.NONE, call_site_key)
            )
            sequence_call_site = SequenceCallSite(
                result_cache=result_cache,
                item_type=item_type,
                service_call_sites=service_call_sites,
                service_key=service_identifier.service_key,
            )
            await self._call_site_cache.upsert(call_site_key, sequence_call_site)
            return sequence_call_site

        finally:
            call_site_chain.remove(service_identifier)

    async def _invalidate_service_type_if_needed(self, service_type: TypedType) -> None:
        if service_type not in self._dirty_service_types:
            return

        async with self._service_type_invalidation_lock:
            if service_type not in self._dirty_service_types:
                return

            cache_keys = self._service_type_to_cache_keys.pop(service_type, set())

            for cache_key in cache_keys:
                await self._call_site_cache.try_remove(cache_key)

            self._dirty_service_types.remove(service_type)

    def _create_service_cache_key(
        self, service_identifier: ServiceIdentifier, slot: int
    ) -> ServiceCacheKey:
        return ServiceCacheKey(service_identifier, slot)

    def _track_cache_key(
        self, service_type: TypedType, cache_key: ServiceCacheKey
    ) -> None:
        cache_keys = self._service_type_to_cache_keys.setdefault(service_type, set())
        cache_keys.add(cache_key)

    async def _create_call_site(
        self, service_identifier: ServiceIdentifier, call_site_chain: CallSiteChain
    ) -> ServiceCallSite | None:
        async def _create_new_lock(_: ServiceIdentifier) -> AsyncioReentrantLock:
            return AsyncioReentrantLock()

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
        call_site_chain.check_circular_dependency(service_identifier)

        async with call_site_lock:
            service_call_site = await self._try_create_exact_from_service_identifier(
                service_identifier, call_site_chain
            )

            if service_call_site is None:
                service_call_site = await self.try_create_sequence(
                    service_identifier, call_site_chain
                )

            return service_call_site

    def _populate(self, descriptors: list[ServiceDescriptor]) -> None:
        for descriptor in descriptors:
            cache_key = ServiceIdentifier.from_descriptor(descriptor)
            cache_item = self._descriptor_lookup.get(
                cache_key, ServiceDescriptorCacheItem()
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

        # Check if there is a registration with `KeyedService.ANY_KEY`
        if service_identifier.service_key is not None:
            catch_all_identifier = ServiceIdentifier(
                service_type=service_identifier.service_type,
                service_key=KeyedService.ANY_KEY,
            )

            service_descriptor_cache_item = self._descriptor_lookup.get(
                catch_all_identifier, None
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
        call_site_key = self._create_service_cache_key(service_identifier, slot)
        service_call_site = self._call_site_cache.get(call_site_key)

        if service_call_site is not None:
            return service_call_site

        cache = ResultCache.from_lifetime(
            service_descriptor.lifetime, service_identifier, slot
        )

        if service_descriptor.has_implementation_instance():
            service_call_site = ConstantCallSite(
                service_type=service_descriptor.service_type,
                default_value=service_descriptor.get_implementation_instance(),
                service_key=service_descriptor.service_key,
            )
        elif (
            not service_descriptor.is_keyed_service
            and service_descriptor.sync_implementation_factory is not None
        ):
            service_call_site = SyncFactoryCallSite.from_implementation_factory(
                cache=cache,
                service_type=service_descriptor.service_type,
                implementation_factory=service_descriptor.sync_implementation_factory,
            )
        elif (
            service_descriptor.is_keyed_service
            and service_descriptor.keyed_sync_implementation_factory is not None
        ):
            service_call_site = SyncFactoryCallSite.from_keyed_implementation_factory(
                cache=cache,
                service_type=service_descriptor.service_type,
                implementation_factory=service_descriptor.keyed_sync_implementation_factory,
                service_key=service_identifier.service_key,
            )
        elif (
            not service_descriptor.is_keyed_service
            and service_descriptor.async_implementation_factory is not None
        ):
            service_call_site = AsyncFactoryCallSite.from_implementation_factory(
                cache=cache,
                service_type=service_descriptor.service_type,
                implementation_factory=service_descriptor.async_implementation_factory,
            )
        elif (
            service_descriptor.is_keyed_service
            and service_descriptor.keyed_async_implementation_factory is not None
        ):
            service_call_site = AsyncFactoryCallSite.from_keyed_implementation_factory(
                cache=cache,
                service_type=service_descriptor.service_type,
                implementation_factory=service_descriptor.keyed_async_implementation_factory,
                service_key=service_identifier.service_key,
            )
        elif service_descriptor.has_implementation_type():
            implementation_type = service_descriptor.get_implementation_type()
            assert implementation_type is not None
            service_call_site = await self._create_constructor_call_site(
                cache=cache,
                service_identifier=service_identifier,
                implementation_type=implementation_type,
                call_site_chain=call_site_chain,
            )
        else:
            raise InvalidServiceDescriptorError

        await self._call_site_cache.upsert(key=call_site_key, value=service_call_site)
        self._track_cache_key(service_identifier.service_type, call_site_key)
        return service_call_site

    def _get_service_override(
        self, service_identifier: ServiceIdentifier
    ) -> _ServiceOverride:
        overrides = self._service_overrides.get(service_identifier)

        if overrides is not None and len(overrides) > 0:
            return _ServiceOverride(exists=True, value=overrides[-1])

        catch_all_identifier = self._get_catch_all_service_identifier(
            service_identifier
        )

        if catch_all_identifier is None:
            return _ServiceOverride(exists=False, value=None)

        overrides = self._service_overrides.get(catch_all_identifier)

        if overrides is not None and len(overrides) > 0:
            return _ServiceOverride(exists=True, value=overrides[-1])

        return _ServiceOverride(exists=False, value=None)

    def _get_catch_all_service_identifier(
        self, service_identifier: ServiceIdentifier
    ) -> ServiceIdentifier | None:
        if (
            service_identifier.service_key is None
            or service_identifier.service_key == KeyedService.ANY_KEY
        ):
            return None

        return ServiceIdentifier.from_service_type(
            service_type=service_identifier.service_type,
            service_key=KeyedService.ANY_KEY,
        )

    def _add_override(
        self,
        service_identifier: ServiceIdentifier,
        implementation_instance: object | None,
    ) -> None:
        overrides = self._service_overrides.setdefault(service_identifier, [])
        overrides.append(implementation_instance)

    def _remove_override(self, service_identifier: ServiceIdentifier) -> None:
        overrides = self._service_overrides.get(service_identifier)
        assert overrides is not None
        overrides.pop()

        if len(overrides) == 0:
            self._service_overrides.pop(service_identifier)

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
                service_identifier=service_identifier,
                implementation_type=implementation_type,
                parameters=parameters,
                call_site_chain=call_site_chain,
            )
            return ConstructorCallSite(
                cache=cache,
                service_type=service_identifier.service_type,
                constructor_information=constructor_information,
                parameters=parameters,
                parameter_call_sites=parameter_call_sites,
                service_key=service_identifier.service_key,
            )
        finally:
            call_site_chain.remove(service_identifier)

    async def _create_argument_call_sites(  # noqa: C901, PLR0912
        self,
        service_identifier: ServiceIdentifier,
        implementation_type: TypedType,
        parameters: list[ParameterInformation],
        call_site_chain: CallSiteChain,
    ) -> list[ServiceCallSite | None]:
        if len(parameters) == 0:
            return []

        parameter_call_sites: list[ServiceCallSite | None] = []

        for parameter in parameters:
            call_site: ServiceCallSite | None = None
            is_keyed_parameter = False
            parameter_type = parameter.parameter_type

            if parameter.injectable_dependency is not None:
                if service_identifier.service_key is not None and isinstance(
                    parameter.injectable_dependency, ServiceKeyInjectable
                ):
                    # Even though the parameter may be strongly typed, support `object` if `ANY_KEY` is used

                    if service_identifier.service_key == KeyedService.ANY_KEY:
                        parameter_type = TypedType.from_type(object)
                    elif parameter_type.to_type() is not type(
                        service_identifier.service_key
                    ) and parameter_type.to_type() is not type(object):
                        raise InvalidServiceKeyTypeError

                    call_site = ConstantCallSite(
                        service_type=parameter_type,
                        default_value=service_identifier.service_key,
                    )
                elif isinstance(
                    parameter.injectable_dependency, FromKeyedServicesInjectable
                ):
                    service_key: object | None = None

                    match parameter.injectable_dependency.lookup_mode:
                        case ServiceKeyLookupMode.INHERIT_KEY:
                            service_key = service_identifier.service_key
                        case ServiceKeyLookupMode.EXPLICIT_KEY:
                            service_key = parameter.injectable_dependency.key
                        case ServiceKeyLookupMode.NULL_KEY:
                            service_key = None

                    if service_key is not None:
                        call_site = await self.get_call_site_from_service_identifier(
                            ServiceIdentifier.from_service_type(
                                service_type=parameter_type, service_key=service_key
                            ),
                            call_site_chain=call_site_chain,
                        )
                        is_keyed_parameter = True

            if not is_keyed_parameter and call_site is None:
                call_site = await self.get_call_site_from_service_identifier(
                    ServiceIdentifier.from_service_type(parameter_type), call_site_chain
                )

            if call_site is None and parameter.has_default_value:
                if parameter.is_optional:
                    parameter_call_sites.append(None)
                    continue

                call_site = ConstantCallSite(
                    service_type=parameter_type,
                    default_value=parameter.default_value,
                )

            if call_site is None and parameter.is_optional:
                parameter_call_sites.append(None)
                continue

            if call_site is None:
                raise CannotResolveServiceError(
                    parameter_type=parameter_type,
                    implementation_type=implementation_type,
                )

            parameter_call_sites.append(call_site)

        return parameter_call_sites

    def _is_service(self, service_identifier: ServiceIdentifier) -> bool:
        service_type = service_identifier.service_type

        if service_identifier in self._descriptor_lookup:
            return True

        if (
            service_identifier.service_key is not None
            and ServiceIdentifier(
                service_type=service_type, service_key=KeyedService.ANY_KEY
            )
            in self._descriptor_lookup
        ):
            return True

        return (
            service_type == TypedType.from_type(BaseServiceProvider)
            or service_type == TypedType.from_type(ServiceScopeFactory)
            or service_type == TypedType.from_type(ServiceProviderIsService)
            or service_type == TypedType.from_type(ServiceProviderIsKeyedService)
        )

    def _get_common_cache_location(
        self,
        location_1: CallSiteResultCacheLocation,
        location_2: CallSiteResultCacheLocation,
    ) -> CallSiteResultCacheLocation:
        return CallSiteResultCacheLocation(max(location_1.value, location_2.value))
