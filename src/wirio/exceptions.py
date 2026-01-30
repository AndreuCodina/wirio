from typing import final

from wirio._service_lookup._typed_type import TypedType


class WirioError(Exception):
    """Base exception for Wirio Dependency Injection."""


@final
class ObjectDisposedError(WirioError):
    """The exception that is thrown when an operation is performed on a disposed object."""

    def __init__(self) -> None:
        super().__init__("BaseServiceProvider")


@final
class NonKeyedDescriptorMisuseError(WirioError):
    """The exception that is thrown when a service descriptor is not keyed."""

    def __init__(self) -> None:
        message = "This service descriptor is not keyed"
        super().__init__(message)


@final
class InvalidServiceDescriptorError(WirioError):
    """The exception that is thrown when a service descriptor is invalid."""

    def __init__(self) -> None:
        super().__init__("Invalid service descriptor")


@final
class InvalidServiceKeyTypeError(WirioError):
    """The exception that is thrown when the type of the key used for lookup doesn't match the type in the constructor parameter with the ServiceKey annotation metadata."""

    def __init__(self) -> None:
        super().__init__(
            "The type of the key used for lookup doesn't match the type in the constructor parameter with the ServiceKey annotation metadata"
        )


@final
class CannotResolveServiceError(WirioError):
    """The exception that is thrown when a service cannot be resolved."""

    def __init__(
        self, parameter_type: TypedType, implementation_type: TypedType
    ) -> None:
        message = f"Unable to resolve service for type '{parameter_type}' while attempting to activate '{implementation_type}'"
        super().__init__(message)


@final
class CannotResolveParameterServiceFromImplementationFactoryError(WirioError):
    """The exception that is thrown when a service for a parameter of an implementation factory cannot be resolved."""

    def __init__(self, parameter_type: TypedType) -> None:
        message = f"Unable to resolve service for type '{parameter_type}' while attempting to invoke an implementation factory"
        super().__init__(message)


@final
class CannotResolveServiceFromEndpointError(WirioError):
    """The exception that is thrown when a service for a parameter of an endpoint cannot be resolved."""

    def __init__(self, parameter_type: TypedType) -> None:
        message = f"Unable to resolve service for type '{parameter_type}' while attempting to invoke endpoint"
        super().__init__(message)


@final
class NoServiceRegisteredError(WirioError):
    """The exception that is thrown when no service is registered for a given type."""

    def __init__(self, service_type: TypedType) -> None:
        message = f"No service for type '{service_type}' has been registered"
        super().__init__(message)


@final
class NoKeyedServiceRegisteredError(WirioError):
    """The exception that is thrown when no keyed service is registered for a given type and key."""

    def __init__(self, service_type: TypedType, service_key_type: type) -> None:
        message = f"No keyed service for type '{service_type}' using key type '{service_key_type}' has been registered"
        super().__init__(message)


@final
class KeyedServiceAnyKeyUsedToResolveServiceError(WirioError):
    """The exception that is thrown when KeyedService.AnyKey is used to resolve a single service."""

    def __init__(self) -> None:
        message = "KeyedService.ANY_KEY cannot be used to resolve a single service"
        super().__init__(message)


@final
class CircularDependencyError(WirioError):
    """The exception that is thrown when a circular dependency is detected."""

    def __init__(self, service_type: TypedType) -> None:
        message = f"A circular dependency was detected for the service of type '{service_type}'"
        super().__init__(message)


@final
class NoSingletonServiceRegisteredError(WirioError):
    """The exception that is thrown when no singleton service is registered for a given type."""

    def __init__(self, service_type: TypedType) -> None:
        message = f"No singleton service for type '{service_type}' has been registered"
        super().__init__(message)


@final
class NoKeyedSingletonServiceRegisteredError(WirioError):
    """The exception that is thrown when no keyed singleton service is registered for a given type and key."""

    def __init__(self, service_type: TypedType, service_key_type: type) -> None:
        message = f"No keyed singleton service for type '{service_type}' using key type '{service_key_type}' has been registered"
        super().__init__(message)


@final
class ServiceProviderNotFullyInitializedError(WirioError):
    def __init__(self, method_name: str) -> None:
        message = f"The service provider must be fully initialized before calling '{method_name}'. Use 'async with' or '__aenter__'"
        super().__init__(message)
