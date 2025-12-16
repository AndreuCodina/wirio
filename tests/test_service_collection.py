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
        services = ServiceCollection()
        services.add_transient(SelfCircularDependencyService)

        async with (
            services.build_service_provider() as service_provider,
            service_provider.create_scope() as service_scope,
        ):
            with pytest.raises(RuntimeError) as error:
                await service_scope.service_provider.get_service(
                    SelfCircularDependencyService
                )
                foo = str(error)
                assert foo != ""
