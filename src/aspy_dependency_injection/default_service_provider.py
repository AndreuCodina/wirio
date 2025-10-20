import inspect
from dataclasses import dataclass
from typing import TYPE_CHECKING, Self, final, get_type_hints

from aspy_dependency_injection._concurrent_dictionary import ConcurrentDictionary
from aspy_dependency_injection.abstractions.service_provider import ServiceProvider
from aspy_dependency_injection.service_identifier import ServiceIdentifier
from aspy_dependency_injection.service_lookup.call_site_chain import CallSiteChain
from aspy_dependency_injection.service_lookup.call_site_factory import CallSiteFactory
from aspy_dependency_injection.service_provider_engine_scope import (
    ServiceProviderEngineScope,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import TracebackType

    from aspy_dependency_injection.abstractions.service_scope import ServiceScope
    from aspy_dependency_injection.service_collection import ServiceCollection


@dataclass(frozen=True)
class _ServiceAccessor:
    realized_service: Callable[[ServiceProviderEngineScope], object | None]


@final
class DefaultServiceProvider(ServiceProvider):
    """Provider that resolves services."""

    _services: ServiceCollection
    _root: ServiceProviderEngineScope
    _service_accessors: ConcurrentDictionary[ServiceIdentifier, _ServiceAccessor]

    def __init__(self, services: ServiceCollection) -> None:
        self._services = services
        self._root = ServiceProviderEngineScope(
            service_provider=self, is_root_scope=True
        )
        self._service_accessors = ConcurrentDictionary()
        self._call_site_factory = CallSiteFactory(services)

    def get_service(self, service_type: type) -> object | None:
        return self.get_service_from_service_identifier(
            service_identifier=ServiceIdentifier.from_service_type(service_type),
            service_provider_engine_scope=self._root,
        )

    # # @asynccontextmanager
    def create_scope(self) -> ServiceScope:  # AsyncGenerator[ServiceScope]:
        """Create a new ServiceScope that can be used to resolve scoped services."""
        # async with DefaultServiceScope(service_provider=self) as service_scope:
        #     print("TODO")  # noqa: ERA001
        # yield service_scope
        return ServiceProviderEngineScope(service_provider=self, is_root_scope=False)

    def get_service_from_service_identifier(
        self,
        service_identifier: ServiceIdentifier,
        service_provider_engine_scope: ServiceProviderEngineScope,
    ) -> object | None:
        service_accessor = self._service_accessors.get_or_add(
            key=service_identifier, value_factory=self._create_service_accessor
        )
        return service_accessor.realized_service(service_provider_engine_scope)

    def _create_service_accessor(
        self, service_identifier: ServiceIdentifier
    ) -> _ServiceAccessor:
        call_site = self._call_site_factory.get_call_site(
            service_identifier, CallSiteChain()
        )

        service: object | None = None

        for descriptor in self._services.descriptors:
            if descriptor.service_type == service_identifier.service_type:
                service = self._create_instance(descriptor.service_type)
        return _ServiceAccessor(realized_service=lambda _: service)

    def _create_instance(self, service_type: type) -> object:
        """Recursively create an instance of the service type."""
        is_service_registered = any(
            descriptor.service_type == service_type
            for descriptor in self._services.descriptors
        )
        if not is_service_registered:
            error_message = f"Service {service_type} not registered."
            raise ValueError(error_message)

        init_method = service_type.__init__
        init_signature = inspect.signature(init_method)
        init_type_hints = get_type_hints(init_method)
        parameter_names = init_signature.parameters.keys()
        arguments: dict[str, object] = {}

        for parameter_name in parameter_names:  # init_signature.parameters.items()
            if parameter_name in ["self", "args", "kwargs"]:
                continue

            parameter_type = init_type_hints[parameter_name]
            arguments[parameter_name] = self._create_instance(parameter_type)

        if len(arguments) == 0:
            return service_type()

        return service_type(**arguments)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        await self._root.__aexit__(exc_type, exc_val, exc_tb)
