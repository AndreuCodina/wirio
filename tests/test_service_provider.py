from typing import Annotated

import pytest
from pytest_mock import MockerFixture

from tests.utils.services import ServiceWithDependencies, ServiceWithNoDependencies
from wirio.abstractions.keyed_service import KeyedService
from wirio.annotations import FromKeyedServices, ServiceKey
from wirio.exceptions import (
    CannotResolveServiceError,
    DirectScopedResolvedFromRootError,
    ObjectDisposedError,
    ScopedInSingletonError,
    ScopedResolvedFromRootError,
    ServiceProviderNotFullyInitializedError,
)
from wirio.service_collection import ServiceCollection


class TestServiceProvider:
    async def test_resolve_overridden_service(self) -> None:
        services = ServiceCollection()
        services.add_transient(ServiceWithNoDependencies)

        async with services.build_service_provider() as service_provider:
            overridden_instance = ServiceWithNoDependencies()

            resolved_before_override = await service_provider.get_required_service(
                ServiceWithNoDependencies
            )

            assert resolved_before_override is not overridden_instance

            with service_provider.override_service(
                ServiceWithNoDependencies, overridden_instance
            ):
                resolved_service = await service_provider.get_required_service(
                    ServiceWithNoDependencies
                )

                assert resolved_service is overridden_instance

            resolved_after_override = await service_provider.get_required_service(
                ServiceWithNoDependencies
            )

            assert resolved_after_override is not overridden_instance
            assert isinstance(resolved_after_override, ServiceWithNoDependencies)

    async def test_resolve_overridden_but_not_registered_service(self) -> None:
        services = ServiceCollection()

        async with services.build_service_provider() as service_provider:
            overridden_instance = ServiceWithNoDependencies()

            with service_provider.override_service(
                ServiceWithNoDependencies, overridden_instance
            ):
                resolved_service = await service_provider.get_required_service(
                    ServiceWithNoDependencies
                )

                assert resolved_service is overridden_instance

    async def test_resolve_overridden_keyed_service(self) -> None:
        service_key = "key"
        services = ServiceCollection()
        services.add_keyed_transient(service_key, ServiceWithNoDependencies)

        async with services.build_service_provider() as service_provider:
            overridden_instance = ServiceWithNoDependencies()

            resolved_before_override = (
                await service_provider.get_required_keyed_service(
                    service_key, ServiceWithNoDependencies
                )
            )

            assert resolved_before_override is not overridden_instance

            with service_provider.override_keyed_service(
                service_key,
                ServiceWithNoDependencies,
                overridden_instance,
            ):
                resolved_service = await service_provider.get_required_keyed_service(
                    service_key, ServiceWithNoDependencies
                )

                assert resolved_service is overridden_instance

            resolved_after_override = await service_provider.get_required_keyed_service(
                service_key, ServiceWithNoDependencies
            )

            assert resolved_after_override is not overridden_instance
            assert isinstance(resolved_after_override, ServiceWithNoDependencies)

    async def test_resolve_overridden_keyed_service_with_any_key(self) -> None:
        service_key = KeyedService.ANY_KEY
        services = ServiceCollection()
        services.add_keyed_transient("actual_key", ServiceWithNoDependencies)
        async with services.build_service_provider() as service_provider:
            overridden_instance = ServiceWithNoDependencies()

            with service_provider.override_keyed_service(
                service_key,
                ServiceWithNoDependencies,
                overridden_instance,
            ):
                resolved_service = await service_provider.get_required_keyed_service(
                    "actual_key", ServiceWithNoDependencies
                )

                assert resolved_service is overridden_instance

    async def test_get_overridden_service_after_call_site_is_built(
        self, mocker: MockerFixture
    ) -> None:
        class Service:
            def __init__(self, dependency: ServiceWithNoDependencies) -> None:
                self.dependency = dependency

        services = ServiceCollection()
        services.add_transient(ServiceWithNoDependencies)
        services.add_transient(Service)

        async with services.build_service_provider() as service_provider:
            resolved_service = await service_provider.get_required_service(Service)
            assert isinstance(resolved_service.dependency, ServiceWithNoDependencies)
            overridden_instance = mocker.create_autospec(
                ServiceWithNoDependencies, instance=True
            )

            with service_provider.override_service(
                ServiceWithNoDependencies,
                overridden_instance,
            ):
                resolved_service = await service_provider.get_required_service(Service)

                assert resolved_service.dependency is overridden_instance
                assert isinstance(
                    resolved_service.dependency, ServiceWithNoDependencies
                )

            resolved_service = await service_provider.get_required_service(Service)
            assert resolved_service.dependency is not overridden_instance
            assert isinstance(resolved_service.dependency, ServiceWithNoDependencies)

    async def test_resolve_overridden_keyed_service_using_from_keyed_services_annotation(
        self, mocker: MockerFixture
    ) -> None:
        service_key = "key"

        class Service:
            def __init__(
                self,
                dependency: Annotated[
                    ServiceWithNoDependencies, FromKeyedServices("key")
                ],
            ) -> None:
                self.dependency = dependency

        services = ServiceCollection()
        services.add_keyed_transient(service_key, ServiceWithNoDependencies)
        services.add_transient(Service)

        async with services.build_service_provider() as service_provider:
            overridden_instance = mocker.create_autospec(
                ServiceWithNoDependencies, instance=True
            )

            with service_provider.override_keyed_service(
                service_key,
                ServiceWithNoDependencies,
                overridden_instance,
            ):
                resolved_service = await service_provider.get_required_service(Service)

                assert resolved_service.dependency is overridden_instance

    async def test_resolve_last_overridden_service(self) -> None:
        services = ServiceCollection()
        services.add_transient(ServiceWithNoDependencies)

        async with services.build_service_provider() as service_provider:
            first_overridden_instance = ServiceWithNoDependencies()
            second_overridden_instance = ServiceWithNoDependencies()

            with service_provider.override_service(
                ServiceWithNoDependencies, first_overridden_instance
            ):
                with service_provider.override_service(
                    ServiceWithNoDependencies, second_overridden_instance
                ):
                    resolved_service = await service_provider.get_required_service(
                        ServiceWithNoDependencies
                    )

                    assert resolved_service is second_overridden_instance

                resolved_service_after_inner_override = (
                    await service_provider.get_required_service(
                        ServiceWithNoDependencies
                    )
                )

                assert (
                    resolved_service_after_inner_override is first_overridden_instance
                )

            resolved_after_all_overrides = await service_provider.get_required_service(
                ServiceWithNoDependencies
            )

            assert isinstance(resolved_after_all_overrides, ServiceWithNoDependencies)
            assert resolved_after_all_overrides is not first_overridden_instance
            assert resolved_after_all_overrides is not second_overridden_instance

    async def test_resolve_overridden_service_when_service_is_already_cached(
        self,
    ) -> None:
        services = ServiceCollection()
        services.add_singleton(ServiceWithNoDependencies)

        async with services.build_service_provider() as service_provider:
            cached_instance = await service_provider.get_required_service(
                ServiceWithNoDependencies
            )

            overridden_instance = ServiceWithNoDependencies()

            with service_provider.override_service(
                ServiceWithNoDependencies, overridden_instance
            ):
                resolved_service = await service_provider.get_required_service(
                    ServiceWithNoDependencies
                )

                assert resolved_service is overridden_instance

            resolved_after_override = await service_provider.get_required_service(
                ServiceWithNoDependencies
            )

            assert resolved_after_override is cached_instance
            assert isinstance(resolved_after_override, ServiceWithNoDependencies)

    async def test_resolve_none_when_overriding_with_none(self) -> None:
        services = ServiceCollection()
        services.add_transient(ServiceWithNoDependencies)

        async with services.build_service_provider() as service_provider:
            with service_provider.override_service(ServiceWithNoDependencies, None):
                resolved_service = await service_provider.get_service(
                    ServiceWithNoDependencies
                )

                assert resolved_service is None

            resolved_after_override = await service_provider.get_required_service(
                ServiceWithNoDependencies
            )

            assert isinstance(resolved_after_override, ServiceWithNoDependencies)

    async def test_resolve_overridden_service_in_implementation_factory(self) -> None:
        services = ServiceCollection()

        def implementation_factory(
            dependency: ServiceWithNoDependencies,
        ) -> ServiceWithDependencies:
            return ServiceWithDependencies(dependency)

        services.add_transient(ServiceWithNoDependencies)
        services.add_transient(implementation_factory)

        async with services.build_service_provider() as service_provider:
            overridden_instance = ServiceWithNoDependencies()

            with service_provider.override_service(
                ServiceWithNoDependencies, overridden_instance
            ):
                resolved_service = await service_provider.get_required_service(
                    ServiceWithNoDependencies
                )

                assert resolved_service is overridden_instance

    async def test_activate_eagerly_auto_activated_singleton_service(
        self,
    ) -> None:
        expected_instances = 1
        constructed_instances: list[object] = []

        class AutoActivatedService:
            def __init__(self) -> None:
                constructed_instances.append(self)

        services = ServiceCollection()
        services.add_auto_activated_singleton(AutoActivatedService)

        async with services.build_service_provider() as service_provider:
            assert len(constructed_instances) == expected_instances

            resolved_service = await service_provider.get_required_service(
                AutoActivatedService
            )

            assert len(constructed_instances) == expected_instances
            assert resolved_service is constructed_instances[0]

    async def test_activate_auto_activated_keyed_singleton_service(
        self,
    ) -> None:
        captured_keys: list[str] = []

        class AutoActivatedKeyedService:
            def __init__(self, service_key: Annotated[str, ServiceKey()]) -> None:
                assert service_key is not None
                captured_keys.append(service_key)

        service_key = "key"
        services = ServiceCollection()
        services.add_auto_activated_keyed_singleton(
            service_key, AutoActivatedKeyedService
        )

        async with services.build_service_provider() as service_provider:
            assert captured_keys == [service_key]
            resolved_service = await service_provider.get_required_keyed_service(
                service_key,
                AutoActivatedKeyedService,
            )

            assert isinstance(resolved_service, AutoActivatedKeyedService)
            assert captured_keys == [service_key]

    async def test_not_activate_eagerly_non_auto_activated_services(
        self,
    ) -> None:
        constructed_instances: list[object] = []

        class SingletonService:
            def __init__(self) -> None:
                constructed_instances.append(self)

        class ScopedService:
            def __init__(self) -> None:
                constructed_instances.append(self)

        class TransientService:
            def __init__(self) -> None:
                constructed_instances.append(self)

        services = ServiceCollection()
        services.add_singleton(SingletonService)
        services.add_scoped(ScopedService)
        services.add_transient(TransientService)

        async with services.build_service_provider():
            assert len(constructed_instances) == 0

    async def test_fully_initialize_service_provider_if_not_called_with_context_manager(
        self,
    ) -> None:
        services = ServiceCollection()
        services.add_transient(ServiceWithNoDependencies)

        service_provider = services.build_service_provider()

        assert not service_provider.is_fully_initialized

        await service_provider.get_required_service(ServiceWithNoDependencies)
        assert service_provider.is_fully_initialized
        await service_provider.aclose()

    async def test_fail_when_calling_some_methods_before_fully_initialized(
        self,
    ) -> None:
        services = ServiceCollection()
        services.add_transient(ServiceWithNoDependencies)

        service_provider = services.build_service_provider()

        assert not service_provider.is_fully_initialized

        with pytest.raises(ServiceProviderNotFullyInitializedError):
            service_provider.create_scope()

    async def test_service_provider_fully_initialized_when_called_with_context_manager(
        self,
    ) -> None:
        services = ServiceCollection()
        services.add_transient(ServiceWithNoDependencies)

        async with services.build_service_provider() as service_provider:
            assert service_provider.is_fully_initialized

    async def test_create_call_site_validator_when_validate_scopes_is_enabled(
        self,
    ) -> None:
        services = ServiceCollection()
        services.add_transient(ServiceWithNoDependencies)

        async with services.build_service_provider(
            validate_scopes=True
        ) as service_provider:
            assert service_provider.call_site_validator is not None

    async def test_not_create_call_site_validator_when_validate_scopes_is_not_enabled(
        self,
    ) -> None:
        services = ServiceCollection()
        services.add_transient(ServiceWithNoDependencies)

        async with services.build_service_provider(
            validate_scopes=False
        ) as service_provider:
            assert service_provider.call_site_validator is None

    async def test_raise_exception_group_for_invalid_service_when_validate_on_build_is_enabled(
        self,
    ) -> None:
        services = ServiceCollection()
        services.add_transient(ServiceWithDependencies)

        with pytest.raises(ExceptionGroup) as exception_group:
            async with services.build_service_provider(
                validate_scopes=False, validate_on_build=True
            ):
                pass

        assert len(exception_group.value.exceptions) == 1
        assert isinstance(
            exception_group.value.exceptions[0].__cause__, CannotResolveServiceError
        )

    async def test_validate_on_build_can_be_disabled(self) -> None:
        services = ServiceCollection()
        services.add_transient(ServiceWithDependencies)

        async with services.build_service_provider(
            validate_on_build=False
        ) as service_provider:
            with pytest.raises(CannotResolveServiceError):
                await service_provider.get_required_service(ServiceWithDependencies)

    async def test_validate_scopes_can_be_disabled(self) -> None:
        services = ServiceCollection()
        services.add_transient(ServiceWithDependencies)

        async with services.build_service_provider(
            validate_scopes=False, validate_on_build=False
        ) as service_provider:
            with pytest.raises(CannotResolveServiceError):
                await service_provider.get_required_service(ServiceWithDependencies)

    async def test_fail_scope_validation_when_singleton_depends_on_scoped_service(
        self,
    ) -> None:
        class ScopedService:
            pass

        class SingletonDependingOnScoped:
            def __init__(self, dependency: ScopedService) -> None:
                self.dependency = dependency

        services = ServiceCollection()
        services.add_scoped(ScopedService)
        services.add_singleton(SingletonDependingOnScoped)

        with pytest.raises(ExceptionGroup) as exception_group:
            async with services.build_service_provider(
                validate_scopes=True, validate_on_build=True
            ):
                pass

        assert len(exception_group.value.exceptions) == 1
        assert isinstance(
            exception_group.value.exceptions[0].__cause__, ScopedInSingletonError
        )

    async def test_allow_singleton_with_scoped_dependency_when_scoped_validation_disabled(
        self,
    ) -> None:
        class ScopedService:
            pass

        class SingletonDependingOnScoped:
            def __init__(self, dependency: ScopedService) -> None:
                self.dependency = dependency

        services = ServiceCollection()
        services.add_scoped(ScopedService)
        services.add_singleton(SingletonDependingOnScoped)

        async with services.build_service_provider(
            validate_scopes=False, validate_on_build=False
        ) as service_provider:
            resolved_service = await service_provider.get_required_service(
                SingletonDependingOnScoped
            )

            assert isinstance(resolved_service.dependency, ScopedService)

    async def test_fail_resolving_scoped_service_from_root_scope(
        self,
    ) -> None:
        services = ServiceCollection()
        services.add_scoped(ServiceWithNoDependencies)

        async with services.build_service_provider(
            validate_scopes=True
        ) as service_provider:
            with pytest.raises(DirectScopedResolvedFromRootError):
                await service_provider.get_required_service(ServiceWithNoDependencies)

    async def test_fail_resolving_service_with_scoped_dependency_from_root_scope(
        self,
    ) -> None:
        services = ServiceCollection()
        services.add_scoped(ServiceWithNoDependencies)
        services.add_transient(ServiceWithDependencies)

        async with services.build_service_provider(
            validate_scopes=True
        ) as service_provider:
            with pytest.raises(ScopedResolvedFromRootError):
                await service_provider.get_required_service(ServiceWithDependencies)

    async def test_fail_when_resolving_service_after_disposal(self) -> None:
        class Service:
            pass

        class KeyedService:
            pass

        service_key = "key"
        services = ServiceCollection()
        services.add_transient(Service)
        services.add_keyed_transient(service_key, KeyedService)

        async with services.build_service_provider() as service_provider:
            await service_provider.get_required_service(Service)
            await service_provider.get_required_keyed_service(service_key, KeyedService)

        assert service_provider.is_disposed

        with pytest.raises(ObjectDisposedError):
            await service_provider.get_required_service(Service)

        with pytest.raises(ObjectDisposedError):
            await service_provider.get_required_keyed_service(service_key, KeyedService)
