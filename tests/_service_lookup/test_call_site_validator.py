from collections.abc import AsyncGenerator, Generator, Sequence

from tests.utils.services import ServiceWithNoDependencies
from wirio._service_lookup._async_factory_call_site import AsyncFactoryCallSite
from wirio._service_lookup._async_generator_factory_call_site import (
    AsyncGeneratorFactoryCallSite,
)
from wirio._service_lookup._call_site_validator import CallSiteValidator
from wirio._service_lookup._constant_call_site import ConstantCallSite
from wirio._service_lookup._constructor_call_site import ConstructorCallSite
from wirio._service_lookup._constructor_information import ConstructorInformation
from wirio._service_lookup._result_cache import ResultCache
from wirio._service_lookup._sequence_call_site import SequenceCallSite
from wirio._service_lookup._service_call_site import ServiceCallSite
from wirio._service_lookup._service_identifier import ServiceIdentifier
from wirio._service_lookup._service_provider_call_site import ServiceProviderCallSite
from wirio._service_lookup._sync_factory_call_site import SyncFactoryCallSite
from wirio._service_lookup._sync_generator_factory_call_site import (
    SyncGeneratorFactoryCallSite,
)
from wirio._service_lookup._typed_type import TypedType
from wirio.abstractions.service_scope_factory import ServiceScopeFactory
from wirio.service_collection import ServiceCollection
from wirio.service_lifetime import ServiceLifetime


class TestCallSiteValidator:
    async def test_not_fail_when_resolving_scope_factory_from_root_when_validating_resolution(
        self,
    ) -> None:
        service_type = TypedType.from_type(ServiceScopeFactory)
        call_site = ConstructorCallSite(
            cache=ResultCache.from_lifetime(
                lifetime=ServiceLifetime.SCOPED,
                service_identifier=ServiceIdentifier.from_service_type(service_type),
                slot=0,
            ),
            service_type=service_type,
            constructor_information=ConstructorInformation(
                TypedType.from_type(ServiceWithNoDependencies)
            ),
            parameters=[],
            parameter_call_sites=[],
        )
        validator = CallSiteValidator()

        await validator.validate_call_site(call_site)
        services = ServiceCollection()

        async with services.build_service_provider() as service_provider:
            root_scope = service_provider.root
            validator.validate_resolution(call_site, root_scope, root_scope)

    async def test_not_fail_when_resolving_sequence_from_root_when_no_scoped_dependencies(
        self,
    ) -> None:
        item_type = TypedType.from_type(ServiceWithNoDependencies)
        singleton_call_site = ConstructorCallSite(
            cache=ResultCache.from_lifetime(
                lifetime=ServiceLifetime.SINGLETON,
                service_identifier=ServiceIdentifier.from_service_type(item_type),
                slot=0,
            ),
            service_type=item_type,
            constructor_information=ConstructorInformation(item_type),
            parameters=[],
            parameter_call_sites=[],
        )
        sequence_type = TypedType.from_type(Sequence[ServiceWithNoDependencies])
        sequence_call_site = SequenceCallSite(
            result_cache=ResultCache.none(sequence_type),
            item_type=item_type,
            service_call_sites=[singleton_call_site],
            service_key=None,
        )
        validator = CallSiteValidator()
        await validator.validate_call_site(sequence_call_site)
        services = ServiceCollection()

        async with services.build_service_provider() as service_provider:
            root_scope = service_provider.root
            validator.validate_resolution(sequence_call_site, root_scope, root_scope)

    async def test_not_fail_when_resolving_constant_from_root(self) -> None:
        service_type = TypedType.from_type(ServiceWithNoDependencies)
        call_site = ConstantCallSite(
            service_type=service_type,
            default_value=ServiceWithNoDependencies(),
        )

        await self._assert_not_fail_when_resolving_from_root(call_site)

    async def test_not_fail_when_resolving_sync_factory_from_root(self) -> None:
        service_type = TypedType.from_type(ServiceWithNoDependencies)

        def implementation_factory() -> object:
            return ServiceWithNoDependencies()

        call_site = SyncFactoryCallSite.from_implementation_factory(
            cache=ResultCache.none(service_type=service_type),
            service_type=service_type,
            implementation_factory=implementation_factory,
        )

        await self._assert_not_fail_when_resolving_from_root(call_site)

    async def test_not_fail_when_resolving_async_factory_from_root(self) -> None:
        service_type = TypedType.from_type(ServiceWithNoDependencies)

        async def implementation_factory() -> object:
            return ServiceWithNoDependencies()

        call_site = AsyncFactoryCallSite.from_implementation_factory(
            cache=ResultCache.none(service_type=service_type),
            service_type=service_type,
            implementation_factory=implementation_factory,
        )

        await self._assert_not_fail_when_resolving_from_root(call_site)

    async def test_not_fail_when_resolving_sync_generator_factory_from_root(
        self,
    ) -> None:
        service_type = TypedType.from_type(ServiceWithNoDependencies)

        def implementation_factory() -> Generator[object]:
            yield ServiceWithNoDependencies()

        call_site = SyncGeneratorFactoryCallSite.from_implementation_factory(
            cache=ResultCache.none(service_type=service_type),
            service_type=service_type,
            implementation_factory=implementation_factory,
        )

        await self._assert_not_fail_when_resolving_from_root(call_site)

    async def test_not_fail_when_resolving_async_generator_factory_from_root(
        self,
    ) -> None:
        service_type = TypedType.from_type(ServiceWithNoDependencies)

        async def implementation_factory() -> AsyncGenerator[object]:
            yield ServiceWithNoDependencies()

        call_site = AsyncGeneratorFactoryCallSite.from_implementation_factory(
            cache=ResultCache.none(service_type=service_type),
            service_type=service_type,
            implementation_factory=implementation_factory,
        )

        await self._assert_not_fail_when_resolving_from_root(call_site)

    async def test_not_fail_when_resolving_service_provider_from_root(self) -> None:
        call_site = ServiceProviderCallSite()

        await self._assert_not_fail_when_resolving_from_root(call_site)

    async def test_not_fail_when_validating_resolution_from_non_root_scope(
        self,
    ) -> None:
        call_site = ServiceProviderCallSite()
        validator = CallSiteValidator()
        services = ServiceCollection()

        async with services.build_service_provider() as service_provider:
            root_scope = service_provider.root

            async with service_provider.create_scope() as service_scope:
                validator.validate_resolution(call_site, service_scope, root_scope)

    async def _assert_not_fail_when_resolving_from_root(
        self, call_site: ServiceCallSite
    ) -> None:
        validator = CallSiteValidator()

        await validator.validate_call_site(call_site)
        services = ServiceCollection()

        async with services.build_service_provider() as service_provider:
            root_scope = service_provider.root
            validator.validate_resolution(call_site, root_scope, root_scope)
