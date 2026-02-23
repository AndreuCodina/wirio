import pytest

from tests.utils.services import (
    ServiceWithAsyncContextManagerAndNoDependencies,
    ServiceWithSyncContextManagerAndNoDependencies,
)
from wirio.exceptions import ObjectDisposedError
from wirio.service_collection import ServiceCollection
from wirio.service_provider_engine_scope import (
    ServiceProviderEngineScope,
)


class TestServiceProviderEngineScope:
    async def test_resolve_scoped_sync_context_manager_service(
        self,
    ) -> None:
        services = ServiceCollection()
        services.add_scoped(ServiceWithSyncContextManagerAndNoDependencies)

        async with (
            services.build_service_provider() as service_provider,
            service_provider.create_scope() as service_scope,
        ):
            assert isinstance(service_scope, ServiceProviderEngineScope)

            resolved_service = await service_scope.get_required_service(
                ServiceWithSyncContextManagerAndNoDependencies
            )

            assert isinstance(
                resolved_service, ServiceWithSyncContextManagerAndNoDependencies
            )

    async def test_resolve_scoped_async_context_manager_service(
        self,
    ) -> None:
        services = ServiceCollection()
        services.add_scoped(ServiceWithAsyncContextManagerAndNoDependencies)

        async with (
            services.build_service_provider() as service_provider,
            service_provider.create_scope() as service_scope,
        ):
            assert isinstance(service_scope, ServiceProviderEngineScope)

            resolved_service = await service_scope.get_required_service(
                ServiceWithAsyncContextManagerAndNoDependencies
            )

            assert isinstance(
                resolved_service, ServiceWithAsyncContextManagerAndNoDependencies
            )

    async def test_fail_when_getting_service_from_disposed_scope(self) -> None:
        services = ServiceCollection()
        services.add_scoped(ServiceWithAsyncContextManagerAndNoDependencies)

        async with services.build_service_provider() as service_provider:
            service_scope = service_provider.create_scope()

            assert isinstance(service_scope, ServiceProviderEngineScope)

            async with service_scope:
                pass

            with pytest.raises(ObjectDisposedError):
                await service_scope.get_required_service(
                    ServiceWithAsyncContextManagerAndNoDependencies
                )

    async def test_fail_when_getting_keyed_service_from_disposed_scope(self) -> None:
        service_key = "key"
        services = ServiceCollection()
        services.add_keyed_scoped(
            service_key, ServiceWithAsyncContextManagerAndNoDependencies
        )

        async with services.build_service_provider() as service_provider:
            service_scope = service_provider.create_scope()

            assert isinstance(service_scope, ServiceProviderEngineScope)

            async with service_scope:
                pass

            with pytest.raises(ObjectDisposedError):
                await service_scope.get_required_keyed_service(
                    service_key, ServiceWithAsyncContextManagerAndNoDependencies
                )

    @pytest.mark.parametrize(
        argnames=("is_async_service"),
        argvalues=[
            True,
            False,
        ],
    )
    async def test_dispose_service_when_capturing_service_after_engine_scope_disposal(
        self, is_async_service: bool
    ) -> None:
        services = ServiceCollection()

        async with services.build_service_provider() as service_provider:
            engine_scope = ServiceProviderEngineScope(
                service_provider=service_provider,
                is_root_scope=False,
            )
            await engine_scope.__aexit__(None, None, None)

            service = (
                await ServiceWithAsyncContextManagerAndNoDependencies().__aenter__()
                if is_async_service
                else ServiceWithSyncContextManagerAndNoDependencies().__enter__()
            )

            with pytest.raises(ObjectDisposedError):
                await engine_scope.capture_disposable(service)

            assert service.is_disposed
