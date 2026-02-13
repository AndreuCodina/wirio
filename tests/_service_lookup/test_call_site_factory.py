from collections.abc import Sequence

import pytest

from tests.utils.services import ServiceWithGeneric, ServiceWithNoDependencies
from wirio._service_lookup._call_site_chain import CallSiteChain
from wirio._service_lookup._call_site_factory import (
    CallSiteFactory,
    ServiceDescriptorCacheItem,
)
from wirio._service_lookup._constant_call_site import ConstantCallSite
from wirio._service_lookup._sequence_call_site import SequenceCallSite
from wirio._service_lookup._service_identifier import ServiceIdentifier
from wirio._service_lookup._typed_type import TypedType
from wirio._service_lookup.call_site_result_cache_location import (
    CallSiteResultCacheLocation,
)
from wirio.abstractions.keyed_service import KeyedService
from wirio.exceptions import ServiceDescriptorDoesNotExistError
from wirio.service_descriptor import ServiceDescriptor
from wirio.service_lifetime import ServiceLifetime


class TestCallSiteFactory:
    async def test_fail_when_service_descriptor_instance_does_not_exist(self) -> None:
        existing_descriptor = ServiceDescriptor.from_implementation_type(
            service_type=ServiceWithNoDependencies,
            implementation_type=ServiceWithNoDependencies,
            service_key=None,
            lifetime=ServiceLifetime.SINGLETON,
            auto_activate=False,
        )
        call_site_factory = CallSiteFactory([existing_descriptor])
        missing_descriptor = ServiceDescriptor.from_implementation_type(
            service_type=ServiceWithNoDependencies,
            implementation_type=ServiceWithNoDependencies,
            service_key=None,
            lifetime=ServiceLifetime.SINGLETON,
            auto_activate=False,
        )

        with pytest.raises(ServiceDescriptorDoesNotExistError):
            await call_site_factory.get_call_site_from_service_descriptor(
                missing_descriptor,
                CallSiteChain(),
            )

    async def test_return_overridden_call_site_when_override_exists(self) -> None:
        service_identifier = ServiceIdentifier.from_service_type(
            service_type=TypedType.from_type(ServiceWithNoDependencies)
        )
        call_site_factory = CallSiteFactory([])
        override_instance = ServiceWithNoDependencies()
        call_site_chain = CallSiteChain()

        with call_site_factory.override_service(
            service_identifier=service_identifier,
            implementation_instance=override_instance,
        ):
            call_site = await call_site_factory.get_call_site_from_service_identifier(
                service_identifier=service_identifier,
                call_site_chain=call_site_chain,
            )

        assert isinstance(call_site, ConstantCallSite)
        assert call_site.default_value is override_instance

    async def test_return_none_when_descriptor_not_registered(self) -> None:
        missing_descriptor = ServiceDescriptor.from_implementation_type(
            service_type=ServiceWithNoDependencies,
            implementation_type=ServiceWithNoDependencies,
            service_key=None,
            lifetime=ServiceLifetime.SINGLETON,
            auto_activate=False,
        )
        call_site_factory = CallSiteFactory([])

        call_site = await call_site_factory.get_call_site_from_service_descriptor(
            missing_descriptor,
            CallSiteChain(),
        )

        assert call_site is None

    async def test_return_none_when_sequence_item_type_is_not_registered(
        self,
    ) -> None:
        call_site_factory = CallSiteFactory([])
        service_identifier = ServiceIdentifier.from_service_type(
            service_type=TypedType.from_type(ServiceWithNoDependencies)
        )

        call_site = await call_site_factory.try_create_sequence(
            service_identifier=service_identifier,
            call_site_chain=CallSiteChain(),
        )

        assert call_site is None

    async def test_create_sequence_from_cached_descriptors(
        self,
    ) -> None:
        singleton_descriptor = ServiceDescriptor.from_implementation_type(
            service_type=ServiceWithNoDependencies,
            implementation_type=ServiceWithNoDependencies,
            service_key=None,
            lifetime=ServiceLifetime.SINGLETON,
            auto_activate=False,
        )
        scoped_descriptor = ServiceDescriptor.from_implementation_type(
            service_type=ServiceWithNoDependencies,
            implementation_type=ServiceWithNoDependencies,
            service_key=None,
            lifetime=ServiceLifetime.SCOPED,
            auto_activate=False,
        )
        call_site_factory = CallSiteFactory([singleton_descriptor, scoped_descriptor])
        sequence_identifier = ServiceIdentifier.from_service_type(
            service_type=TypedType.from_type(Sequence[ServiceWithNoDependencies])
        )

        sequence_call_site = await call_site_factory.try_create_sequence(
            service_identifier=sequence_identifier,
            call_site_chain=CallSiteChain(),
        )

        assert isinstance(sequence_call_site, SequenceCallSite)
        assert sequence_call_site.cache.location is CallSiteResultCacheLocation.SCOPE
        assert [
            service_call_site.cache.key.slot
            for service_call_site in sequence_call_site.service_call_sites
        ] == [1, 0]
        assert [
            service_call_site.cache.location
            for service_call_site in sequence_call_site.service_call_sites
        ] == [
            CallSiteResultCacheLocation.ROOT,
            CallSiteResultCacheLocation.SCOPE,
        ]

    async def test_reuse_cached_sequence_call_site(self) -> None:
        descriptor = ServiceDescriptor.from_implementation_type(
            service_type=ServiceWithNoDependencies,
            implementation_type=ServiceWithNoDependencies,
            service_key=None,
            lifetime=ServiceLifetime.SINGLETON,
            auto_activate=False,
        )
        call_site_factory = CallSiteFactory([descriptor])
        sequence_identifier = ServiceIdentifier.from_service_type(
            service_type=TypedType.from_type(Sequence[ServiceWithNoDependencies])
        )

        first_call_site = await call_site_factory.try_create_sequence(
            service_identifier=sequence_identifier,
            call_site_chain=CallSiteChain(),
        )
        second_call_site = await call_site_factory.try_create_sequence(
            service_identifier=sequence_identifier,
            call_site_chain=CallSiteChain(),
        )

        assert isinstance(first_call_site, SequenceCallSite)
        assert first_call_site is second_call_site

    async def test_collect_generic_services_sequence(self) -> None:
        expected_call_sites = 2
        unkeyed_first_descriptor = ServiceDescriptor.from_implementation_type(
            service_type=ServiceWithGeneric[int],
            implementation_type=ServiceWithGeneric[int],
            service_key=None,
            lifetime=ServiceLifetime.SINGLETON,
            auto_activate=False,
        )
        unkeyed_second_descriptor = ServiceDescriptor.from_implementation_type(
            service_type=ServiceWithGeneric[int],
            implementation_type=ServiceWithGeneric[int],
            service_key=None,
            lifetime=ServiceLifetime.SCOPED,
            auto_activate=False,
        )
        keyed_descriptor = ServiceDescriptor.from_implementation_type(
            service_type=ServiceWithGeneric[int],
            implementation_type=ServiceWithGeneric[int],
            service_key="extra",
            lifetime=ServiceLifetime.SINGLETON,
            auto_activate=False,
        )
        call_site_factory = CallSiteFactory(
            [unkeyed_first_descriptor, unkeyed_second_descriptor, keyed_descriptor]
        )
        sequence_identifier = ServiceIdentifier.from_service_type(
            service_type=TypedType.from_type(Sequence[ServiceWithGeneric[int]])
        )

        sequence_call_site = await call_site_factory.try_create_sequence(
            service_identifier=sequence_identifier,
            call_site_chain=CallSiteChain(),
        )

        assert isinstance(sequence_call_site, SequenceCallSite)
        assert len(sequence_call_site.service_call_sites) == expected_call_sites
        assert sequence_call_site.cache.location is CallSiteResultCacheLocation.SCOPE
        assert [
            service_call_site.cache.key.slot
            for service_call_site in sequence_call_site.service_call_sites
        ] == [1, 0]
        assert all(
            service_call_site.cache.key.service_identifier.service_key is None
            for service_call_site in sequence_call_site.service_call_sites
        )

        unkeyed_instances = [
            service_call_site.cache.key.service_identifier.service_type
            for service_call_site in sequence_call_site.service_call_sites
        ]
        assert all(
            instance == TypedType.from_type(ServiceWithGeneric[int])
            for instance in unkeyed_instances
        )

    async def test_collect_keyed_services_for_any_key_sequence(self) -> None:
        expected_call_sites = 3
        any_descriptor = ServiceDescriptor.from_implementation_type(
            service_type=ServiceWithNoDependencies,
            implementation_type=ServiceWithNoDependencies,
            service_key=KeyedService.ANY_KEY,
            lifetime=ServiceLifetime.SINGLETON,
            auto_activate=False,
        )
        keyed_first_descriptor = ServiceDescriptor.from_implementation_type(
            service_type=ServiceWithNoDependencies,
            implementation_type=ServiceWithNoDependencies,
            service_key="key_1",
            lifetime=ServiceLifetime.SINGLETON,
            auto_activate=False,
        )
        keyed_second_descriptor = ServiceDescriptor.from_implementation_type(
            service_type=ServiceWithNoDependencies,
            implementation_type=ServiceWithNoDependencies,
            service_key="key_1",
            lifetime=ServiceLifetime.SCOPED,
            auto_activate=False,
        )
        transient_descriptor = ServiceDescriptor.from_implementation_type(
            service_type=ServiceWithNoDependencies,
            implementation_type=ServiceWithNoDependencies,
            service_key="key_2",
            lifetime=ServiceLifetime.TRANSIENT,
            auto_activate=False,
        )
        call_site_factory = CallSiteFactory(
            [
                any_descriptor,
                keyed_first_descriptor,
                keyed_second_descriptor,
                transient_descriptor,
            ]
        )
        sequence_identifier = ServiceIdentifier.from_service_type(
            service_type=TypedType.from_type(Sequence[ServiceWithNoDependencies]),
            service_key=KeyedService.ANY_KEY,
        )

        sequence_call_site = await call_site_factory.try_create_sequence(
            service_identifier=sequence_identifier,
            call_site_chain=CallSiteChain(),
        )

        assert isinstance(sequence_call_site, SequenceCallSite)
        assert len(sequence_call_site.service_call_sites) == expected_call_sites
        assert sequence_call_site.cache.location is CallSiteResultCacheLocation.NONE
        assert [
            service_call_site.cache.key.service_identifier.service_key
            for service_call_site in sequence_call_site.service_call_sites
        ] == ["key_1", "key_1", "key_2"]
        assert [
            service_call_site.cache.key.slot
            for service_call_site in sequence_call_site.service_call_sites
        ] == [1, 0, 0]

    def test_return_zero_length_when_descriptor_cache_item(self) -> None:
        cache_item = ServiceDescriptorCacheItem()

        assert len(cache_item) == 0
