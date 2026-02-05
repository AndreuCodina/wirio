import pytest

from tests.utils.services import ServiceWithNoDependencies
from wirio._service_lookup._call_site_chain import CallSiteChain
from wirio._service_lookup._call_site_factory import CallSiteFactory
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
