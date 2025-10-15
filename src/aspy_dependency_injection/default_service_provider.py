import inspect
from dataclasses import dataclass
from typing import TYPE_CHECKING, final, get_type_hints

from aspy_dependency_injection._concurrent_dictionary import ConcurrentDictionary
from aspy_dependency_injection.abstractions.service_provider import ServiceProvider
from aspy_dependency_injection.service_identifier import ServiceIdentifier
from aspy_dependency_injection.service_provider_engine_scope import (
    ServiceProviderEngineScope,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from aspy_dependency_injection.abstractions.service_scope import ServiceScope
    from aspy_dependency_injection.service_collection import ServiceCollection


@final
@dataclass
class _ServiceAccessor:
    realized_service: Callable[[ServiceProviderEngineScope], object | None]


@final
class DefaultServiceProvider(ServiceProvider):
    """Provider that resolves services."""

    _services: ServiceCollection
    _service_accessors: ConcurrentDictionary[ServiceIdentifier, _ServiceAccessor]

    def __init__(self, services: ServiceCollection) -> None:
        self._services = services
        self._service_accessors = ConcurrentDictionary()
        self._root = ServiceProviderEngineScope(self)

    def get_service(self, service_type: type) -> object | None:
        return self.get_service_from_service_identifier(
            ServiceIdentifier.from_service_type(service_type)
        )

    # # @asynccontextmanager
    def create_scope(self) -> ServiceScope:  # AsyncGenerator[ServiceScope]:
        """Create a new ServiceScope that can be used to resolve scoped services."""
        # async with DefaultServiceScope(service_provider=self) as service_scope:
        #     print("TODO")  # noqa: ERA001
        # yield service_scope
        return ServiceProviderEngineScope(service_provider=self)

    def get_service_from_service_identifier(
        self, service_identifier: ServiceIdentifier
    ) -> object | None:
        for descriptor in self._services.descriptors:
            if descriptor.service_type == service_identifier.service_type:
                return self._create_instance(descriptor.service_type)

        return None

    def _create_service_accessor(
        self, service_identifier: ServiceIdentifier
    ) -> _ServiceAccessor:
        return _ServiceAccessor(
            realized_service=lambda service_scope: service_scope.get_service(
                service_identifier.service_type
            )
        )

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
