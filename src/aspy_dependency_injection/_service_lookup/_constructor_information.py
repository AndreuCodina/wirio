import inspect
import typing
from typing import Final, final

from aspy_dependency_injection._service_lookup._parameter_information import (
    ParameterInformation,
)
from aspy_dependency_injection._service_lookup._typed_type import TypedType


@final
class ConstructorInformation:
    _type_: Final[TypedType]

    def __init__(self, type_: TypedType) -> None:
        self._type_ = type_

    def invoke(self, parameter_values: list[object]) -> object:
        return self._type_.invoke(parameter_values)

    def get_parameters(self) -> list[ParameterInformation]:
        init_method = self._type_.to_type().__init__
        init_signature = inspect.signature(init_method)
        init_type_hints = typing.get_type_hints(init_method, include_extras=True)  # pyright: ignore[reportUnusedVariable]
        parameter_informations: list[ParameterInformation] = []

        for parameter_name, parameter in init_signature.parameters.items():
            if parameter_name in ["self", "args", "kwargs"]:
                continue

            parameter_to_use = parameter.replace(
                annotation=init_type_hints[parameter_name]
            )
            parameter_information = ParameterInformation(parameter_to_use)
            parameter_informations.append(parameter_information)

        return parameter_informations
