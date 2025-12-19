from typing import TYPE_CHECKING

import pytest

from aspy_dependency_injection.service_collection import ServiceCollection
from tests.utils.services import (
    DisposeViewer,
    SelfCircularDependencyService,
    ServiceWithAsyncContextManagerAndDependencies,
    ServiceWithAsyncContextManagerAndNoDependencies,
    ServiceWithDependencies,
    ServiceWithNoDependencies,
    ServiceWithSyncContextManagerAndNoDependencies,
)

if TYPE_CHECKING:
    from aspy_dependency_injection.abstractions.service_provider import ServiceProvider


class Father:
    pass


class Child(Father):
    pass


class TestServiceCollection:
    async def test_resolve_transient_service_with_no_dependencies(self) -> None:
        services = ServiceCollection()
        services.add_transient(ServiceWithNoDependencies)

        async with (
            services.build_service_provider() as service_provider,
            service_provider.create_scope() as service_scope,
        ):
            resolved_service = await service_scope.service_provider.get_service(
                ServiceWithNoDependencies
            )

            assert isinstance(resolved_service, ServiceWithNoDependencies)

    @pytest.mark.parametrize(
        argnames=("is_async_implementation_factory"),
        argvalues=[
            (True),
            (False),
        ],
        ids=[
            "async_implementation_factory",
            "sync_implementation_factory",
        ],
    )
    async def test_resolve_transient_service_with_implementation_factory_and_no_dependencies(
        self,
        is_async_implementation_factory: bool,
    ) -> None:
        async def async_implementation_factory(
            _: ServiceProvider,
        ) -> ServiceWithNoDependencies:
            return ServiceWithNoDependencies()

        def sync_implementation_factory(
            _: ServiceProvider,
        ) -> ServiceWithNoDependencies:
            return ServiceWithNoDependencies()

        services = ServiceCollection()

        implementation_factory = (
            async_implementation_factory
            if is_async_implementation_factory
            else sync_implementation_factory
        )
        services.add_transient(ServiceWithNoDependencies, implementation_factory)

        async with (
            services.build_service_provider() as service_provider,
            service_provider.create_scope() as service_scope,
        ):
            resolved_service = await service_scope.service_provider.get_service(
                ServiceWithNoDependencies
            )

            assert isinstance(resolved_service, ServiceWithNoDependencies)

    async def test_resolve_transient_service_with_dependencies(self) -> None:
        services = ServiceCollection()
        services.add_transient(ServiceWithNoDependencies)
        services.add_transient(ServiceWithDependencies)

        async with (
            services.build_service_provider() as service_provider,
            service_provider.create_scope() as service_scope,
        ):
            resolved_service = await service_scope.service_provider.get_service(
                ServiceWithDependencies
            )

            assert isinstance(resolved_service, ServiceWithDependencies)
            assert isinstance(
                resolved_service.service_with_no_dependencies, ServiceWithNoDependencies
            )

    @pytest.mark.parametrize(
        argnames=("service_type"),
        argvalues=[
            (ServiceWithAsyncContextManagerAndNoDependencies),
            (ServiceWithSyncContextManagerAndNoDependencies),
        ],
        ids=[
            "async_context_manager",
            "sync_context_manager",
        ],
    )
    async def test_resolve_and_dispose_transient_service_with_context_manager_and_no_dependencies(
        self, service_type: type[DisposeViewer]
    ) -> None:
        services = ServiceCollection()
        services.add_transient(service_type)

        async with (
            services.build_service_provider() as service_provider,
            service_provider.create_scope() as service_scope,
        ):
            resolved_service = await service_scope.service_provider.get_service(
                service_type
            )

            assert isinstance(resolved_service, service_type)
            assert not resolved_service.is_disposed

        assert resolved_service.is_disposed

    async def test_resolve_and_dispose_transient_service_with_context_manager_and_dependencies(
        self,
    ) -> None:
        services = ServiceCollection()
        services.add_transient(ServiceWithAsyncContextManagerAndNoDependencies)
        services.add_transient(ServiceWithAsyncContextManagerAndDependencies)

        async with (
            services.build_service_provider() as service_provider,
            service_provider.create_scope() as service_scope,
        ):
            resolved_service = await service_scope.service_provider.get_service(
                ServiceWithAsyncContextManagerAndDependencies
            )

            assert isinstance(
                resolved_service, ServiceWithAsyncContextManagerAndDependencies
            )
            assert not resolved_service.is_disposed
            assert isinstance(
                resolved_service.service_with_async_context_manager_and_no_dependencies,
                ServiceWithAsyncContextManagerAndNoDependencies,
            )
            assert not resolved_service.service_with_async_context_manager_and_no_dependencies.is_disposed

        assert resolved_service.is_disposed
        assert resolved_service.service_with_async_context_manager_and_no_dependencies.is_disposed

    async def test_fail_when_resolve_circular_dependency(self) -> None:
        expected_error_message = "A circular dependency was detected for the service of type '<class 'tests.utils.services.SelfCircularDependencyService'>'"
        services = ServiceCollection()
        services.add_transient(SelfCircularDependencyService)

        async with (
            services.build_service_provider() as service_provider,
            service_provider.create_scope() as service_scope,
        ):
            with pytest.raises(RuntimeError, match=expected_error_message):
                await service_scope.service_provider.get_service(
                    SelfCircularDependencyService
                )

    async def test_resolve_same_transient_service_several_times(self) -> None:
        services = ServiceCollection()
        services.add_transient(ServiceWithNoDependencies)

        async with (
            services.build_service_provider() as service_provider,
            service_provider.create_scope() as service_scope,
        ):
            await service_scope.service_provider.get_service(ServiceWithNoDependencies)
            await service_scope.service_provider.get_service(ServiceWithNoDependencies)
