import pytest

from tests.utils.services import ServiceWithNoDependencies
from wirio.exceptions import NonKeyedDescriptorMisuseError
from wirio.service_collection import ServiceCollection
from wirio.service_descriptor import ServiceDescriptor
from wirio.service_lifetime import ServiceLifetime


class TestServiceDescriptor:
    def test_stringify(self) -> None:
        class _Service:
            pass

        class _ServiceImplementation:
            pass

        def _sync_factory(_: object | None = None) -> _ServiceImplementation:
            return _ServiceImplementation()

        async def _async_factory(_: object | None = None) -> _ServiceImplementation:
            return _ServiceImplementation()

        def _keyed_sync_factory(
            _: object | None, __: object | None = None
        ) -> _ServiceImplementation:
            return _ServiceImplementation()

        async def _keyed_async_factory(
            _: object | None, __: object | None = None
        ) -> _ServiceImplementation:
            return _ServiceImplementation()

        keyed_implementation_type = ServiceDescriptor.from_implementation_type(
            service_type=_Service,
            implementation_type=_ServiceImplementation,
            service_key="key",
            lifetime=ServiceLifetime.SINGLETON,
            auto_activate=False,
        )
        keyed_async_implementation_factory = (
            ServiceDescriptor.from_keyed_async_implementation_factory(
                service_type=_Service,
                implementation_factory=_keyed_async_factory,
                service_key="key",
                lifetime=ServiceLifetime.SINGLETON,
                auto_activate=False,
            )
        )
        keyed_sync_implementation_factory = (
            ServiceDescriptor.from_keyed_sync_implementation_factory(
                service_type=_Service,
                implementation_factory=_keyed_sync_factory,
                service_key="key",
                lifetime=ServiceLifetime.SINGLETON,
                auto_activate=False,
            )
        )
        keyed_implementation_instance = ServiceDescriptor.from_implementation_instance(
            service_type=_Service,
            implementation_instance=_ServiceImplementation(),
            service_key="key",
            lifetime=ServiceLifetime.SINGLETON,
            auto_activate=False,
        )
        non_keyed_implementation_type = ServiceDescriptor.from_implementation_type(
            service_type=_Service,
            implementation_type=_ServiceImplementation,
            service_key=None,
            lifetime=ServiceLifetime.SINGLETON,
            auto_activate=False,
        )
        non_keyed_async_implementation_factory = (
            ServiceDescriptor.from_async_implementation_factory(
                service_type=_Service,
                implementation_factory=_async_factory,
                lifetime=ServiceLifetime.SINGLETON,
                auto_activate=False,
            )
        )
        non_keyed_sync_implementation_factory = (
            ServiceDescriptor.from_sync_implementation_factory(
                service_type=_Service,
                implementation_factory=_sync_factory,
                lifetime=ServiceLifetime.SINGLETON,
                auto_activate=False,
            )
        )
        non_keyed_implementation_instance = _ServiceImplementation()
        non_keyed_implementation_instance = (
            ServiceDescriptor.from_implementation_instance(
                service_type=_Service,
                implementation_instance=non_keyed_implementation_instance,
                service_key=None,
                lifetime=ServiceLifetime.SINGLETON,
                auto_activate=False,
            )
        )

        assert (
            str(keyed_implementation_type)
            == f"service_type: {keyed_implementation_type.service_type}, lifetime: {keyed_implementation_type.lifetime}, service_key: {keyed_implementation_type.service_key}, keyed_implementation_type: {keyed_implementation_type.keyed_implementation_type}"
        )
        assert (
            str(keyed_async_implementation_factory)
            == f"service_type: {keyed_async_implementation_factory.service_type}, lifetime: {keyed_async_implementation_factory.lifetime}, service_key: {keyed_async_implementation_factory.service_key}, keyed_async_implementation_factory: {keyed_async_implementation_factory.keyed_async_implementation_factory}"
        )
        assert (
            str(keyed_sync_implementation_factory)
            == f"service_type: {keyed_sync_implementation_factory.service_type}, lifetime: {keyed_sync_implementation_factory.lifetime}, service_key: {keyed_sync_implementation_factory.service_key}, keyed_sync_implementation_factory: {keyed_sync_implementation_factory.keyed_sync_implementation_factory}"
        )
        assert (
            str(keyed_implementation_instance)
            == f"service_type: {keyed_implementation_instance.service_type}, lifetime: {keyed_implementation_instance.lifetime}, service_key: {keyed_implementation_instance.service_key}, keyed_implementation_instance: {keyed_implementation_instance.keyed_implementation_instance}"
        )
        assert (
            str(non_keyed_implementation_type)
            == f"service_type: {non_keyed_implementation_type.service_type}, lifetime: {non_keyed_implementation_type.lifetime}, implementation_type: {non_keyed_implementation_type.implementation_type}"
        )
        assert (
            str(non_keyed_async_implementation_factory)
            == f"service_type: {non_keyed_async_implementation_factory.service_type}, lifetime: {non_keyed_async_implementation_factory.lifetime}, async_implementation_factory: {non_keyed_async_implementation_factory.async_implementation_factory}"
        )
        assert (
            str(non_keyed_sync_implementation_factory)
            == f"service_type: {non_keyed_sync_implementation_factory.service_type}, lifetime: {non_keyed_sync_implementation_factory.lifetime}, sync_implementation_factory: {non_keyed_sync_implementation_factory.sync_implementation_factory}"
        )
        assert (
            str(non_keyed_implementation_instance)
            == f"service_type: {non_keyed_implementation_instance.service_type}, lifetime: {non_keyed_implementation_instance.lifetime}, implementation_instance: {non_keyed_implementation_instance.implementation_instance}"
        )

    @pytest.mark.parametrize(
        argnames="is_async_implementation_factory",
        argvalues=[
            True,
            False,
        ],
    )
    async def test_return_none_getting_implementation_factory_when_is_keyed_service(
        self, is_async_implementation_factory: bool
    ) -> None:
        async def async_inject_service(_: str | None) -> ServiceWithNoDependencies:
            return ServiceWithNoDependencies()

        def sync_inject_service(_: str | None) -> ServiceWithNoDependencies:
            return ServiceWithNoDependencies()

        services = ServiceCollection()

        if is_async_implementation_factory:
            services.add_keyed_transient("key", async_inject_service)
        else:
            services.add_keyed_transient("key", sync_inject_service)

        service_descriptor = next(iter(services))

        if is_async_implementation_factory:
            assert service_descriptor.async_implementation_factory is None
        else:
            assert service_descriptor.sync_implementation_factory is None

    @pytest.mark.parametrize(
        argnames="is_async_implementation_factory",
        argvalues=[
            True,
            False,
        ],
    )
    async def test_fail_getting_keyed_implementation_factory_when_is_not_keyed_service(
        self, is_async_implementation_factory: bool
    ) -> None:
        async def async_inject_service() -> ServiceWithNoDependencies:
            return ServiceWithNoDependencies()

        def sync_inject_service() -> ServiceWithNoDependencies:
            return ServiceWithNoDependencies()

        services = ServiceCollection()

        if is_async_implementation_factory:
            services.add_transient(async_inject_service)
        else:
            services.add_transient(sync_inject_service)

        service_descriptor = next(iter(services))

        with pytest.raises(NonKeyedDescriptorMisuseError):  # noqa: PT012
            if is_async_implementation_factory:
                assert service_descriptor.async_implementation_factory is not None
                _ = service_descriptor.keyed_async_implementation_factory
            else:
                assert service_descriptor.sync_implementation_factory is not None
                _ = service_descriptor.keyed_sync_implementation_factory

    async def test_fail_getting_keyed_implementation_type_when_is_not_keyed_service(
        self,
    ) -> None:
        services = ServiceCollection()
        services.add_transient(ServiceWithNoDependencies)
        service_descriptor = next(iter(services))

        assert service_descriptor.implementation_type is not None

        with pytest.raises(NonKeyedDescriptorMisuseError):
            _ = service_descriptor.keyed_implementation_type

    async def test_fail_getting_keyed_implementation_instance_when_is_not_keyed_service(
        self,
    ) -> None:
        services = ServiceCollection()
        services.add_singleton(ServiceWithNoDependencies, ServiceWithNoDependencies())
        service_descriptor = next(iter(services))

        assert service_descriptor.implementation_instance is not None

        with pytest.raises(NonKeyedDescriptorMisuseError):
            _ = service_descriptor.keyed_implementation_instance
