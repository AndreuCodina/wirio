from aspy_dependency_injection.service_collection import ServiceCollection
from tests.utils.services import (
    ServiceWithAsyncContextManagerAndNoDependencies,
    ServiceWithDependencies,
    ServiceWithNoDependencies,
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

    async def test_resolve_transient_service_with_async_context_manager_and_no_dependencies(
        self,
    ) -> None:
        services = ServiceCollection()
        services.add_transient(ServiceWithAsyncContextManagerAndNoDependencies)

        async with (
            services.build_service_provider() as service_provider,
            service_provider.create_scope() as service_scope,
        ):
            resolved_service = await service_scope.service_provider.get_service(
                ServiceWithAsyncContextManagerAndNoDependencies
            )

            assert isinstance(
                resolved_service, ServiceWithAsyncContextManagerAndNoDependencies
            )
