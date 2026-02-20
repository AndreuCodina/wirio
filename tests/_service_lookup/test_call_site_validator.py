from tests.utils.services import ServiceWithNoDependencies
from wirio._service_lookup._call_site_validator import CallSiteValidator
from wirio._service_lookup._constructor_call_site import ConstructorCallSite
from wirio._service_lookup._constructor_information import ConstructorInformation
from wirio._service_lookup._result_cache import ResultCache
from wirio._service_lookup._service_identifier import ServiceIdentifier
from wirio._service_lookup._typed_type import TypedType
from wirio.abstractions.service_scope_factory import ServiceScopeFactory
from wirio.service_collection import ServiceCollection
from wirio.service_lifetime import ServiceLifetime


class TestCallSiteValidator:
    async def test_allow_resolving_scope_factory_from_root_when_validating_resolution(
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
