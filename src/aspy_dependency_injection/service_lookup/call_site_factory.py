from threading import RLock
from typing import TYPE_CHECKING, final

from aspy_dependency_injection._concurrent_dictionary import ConcurrentDictionary
from aspy_dependency_injection.service_descriptor import ServiceDescriptor
from aspy_dependency_injection.service_identifier import ServiceIdentifier

if TYPE_CHECKING:
    from aspy_dependency_injection.service_collection import ServiceCollection
    from aspy_dependency_injection.service_lookup.call_site_chain import CallSiteChain
    from aspy_dependency_injection.service_lookup.service_call_site import (
        ServiceCallSite,
    )


@final
class CallSiteFactory:
    _call_site_locks: ConcurrentDictionary[ServiceIdentifier, RLock]
    _descriptor_lookup: dict[ServiceIdentifier, _ServiceDescriptorCacheItem]
    _descriptors: list[ServiceDescriptor]

    def __init__(self, services: ServiceCollection) -> None:
        self._call_site_locks = ConcurrentDictionary[ServiceIdentifier, RLock]()
        self._descriptor_lookup = {}
        self._descriptors = services.descriptors.copy()
        self._populate()

    def _populate(self) -> None:
        for descriptor in self._descriptors:
            cache_key = ServiceIdentifier.from_descriptor(descriptor)
            cache_item = self._descriptor_lookup.get(
                cache_key, _ServiceDescriptorCacheItem()
            )
            self._descriptor_lookup[cache_key] = cache_item.add(descriptor)

    def get_call_site(
        self, service_identifier: ServiceIdentifier, call_site_chain: CallSiteChain
    ) -> ServiceCallSite | None:
        return self._create_call_site(
            service_identifier=service_identifier, call_site_chain=call_site_chain
        )

    def _create_call_site(
        self, service_identifier: ServiceIdentifier, call_site_chain: CallSiteChain
    ) -> ServiceCallSite | None:
        call_site_lock = self._call_site_locks.get_or_add(
            service_identifier, lambda _: RLock()
        )

        with call_site_lock:
            return self._try_create_exact(service_identifier, call_site_chain)

    def _try_create_exact(
        self, service_identifier: ServiceIdentifier, call_site_chain: CallSiteChain
    ) -> ServiceCallSite | None:
        cache_item = self._descriptor_lookup.get(service_identifier, None)

        if cache_item is not None:
            # return self._try_create_exact_internal(
            #     descriptor.Last, serviceIdentifier, call_site_chain, DefaultSlot
            # )
            pass

        return None


class _ServiceDescriptorCacheItem:
    _item: ServiceDescriptor | None
    _items: list[ServiceDescriptor] | None

    def __init__(self) -> None:
        self._item = None
        self._items = None

    def add(self, descriptor: ServiceDescriptor) -> _ServiceDescriptorCacheItem:
        new_cache_item = _ServiceDescriptorCacheItem()

        if self._item is None:
            new_cache_item._item = descriptor
        else:
            new_cache_item._item = self._item
            new_cache_item._items = self._items if self._items is not None else []
            new_cache_item._items.append(descriptor)

        return new_cache_item
