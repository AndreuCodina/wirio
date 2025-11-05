import inspect
from typing import Final, final

from aspy_dependency_injection._service_lookup._parameter_information import (
    ParameterInformation,
)


@final
class ConstructorInformation:
    type_: Final[type]

    def __init__(self, type_: type) -> None:
        self.type_ = type_

    def invoke(self, parameter_values: list[object] | None = None) -> object:
        if parameter_values is None:
            return self.type_()

        return self.type_(*parameter_values)

    def get_parameters(self) -> list[ParameterInformation]:
        init_method = self.type_.__init__
        init_signature = inspect.signature(init_method)
        return [
            ParameterInformation(parameter, self.type_)
            for name, parameter in init_signature.parameters.items()
            if name not in ["self", "args", "kwargs"]
        ]
