import inspect
from typing import TypeVar, get_type_hints

TService = TypeVar("TService", bound=object)


class ServiceCollection:  # extends  : IList<ServiceDescriptor>
    services: list[type]

    def __init__(self) -> None:
        self.services = []

    def add_transient(self, service: type) -> None:
        if service in self.services:
            service_index = self.services.index(service)
            self.services[service_index] = service
            return

        self.services.append(service)

    def add_singleton(self, service: type) -> None:
        pass

    def add_scoped(self, service: type) -> None:
        pass

    def get(self, service: type[TService]) -> TService:
        if service not in self.services:
            error_message = f"Service {service} not registered."
            raise ValueError(error_message)

        return self.create_instance(service)

    def create_instance(self, service: type[TService]) -> TService:
        """Recursively create an instance of cls.

        For type-hinted parameters, it tries to provide a simple default.
        Custom classes are recursively instantiated.
        """
        if service not in self.services:
            error_message = f"Service {service} not registered."
            raise ValueError(error_message)

        init_method = service.__init__
        init_signature = inspect.signature(init_method)
        init_type_hints = get_type_hints(init_method)
        parameter_names = init_signature.parameters.keys()
        arguments: dict[str, TService] = {}

        for parameter_name in parameter_names:  # init_signature.parameters.items()
            if parameter_name in ["self", "args", "kwargs"]:
                continue

            parameter_type = init_type_hints[parameter_name]
            arguments[parameter_name] = self.create_instance(parameter_type)

        if len(arguments) == 0:
            return service()

        return service(**arguments)

    def create_scope(self) -> ServiceCollection:
        return self

    @classmethod
    async def uninitialize(cls) -> None:
        pass
