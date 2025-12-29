import inspect
from typing import TYPE_CHECKING, Final, final

from aspy_dependency_injection._service_lookup._parameter_information import (
    ParameterInformation,
)

if TYPE_CHECKING:
    from aspy_dependency_injection._service_lookup._typed_type import TypedType


@final
class ConstructorInformation:
    _type_: Final[TypedType]

    def __init__(self, type_: TypedType) -> None:
        self._type_ = type_

    def invoke(self, parameter_values: list[object]) -> object:
        return self._type_.invoke(parameter_values)

    def get_parameters(self) -> list[ParameterInformation]:
        init_method = self._type_.origin.__init__
        init_signature = inspect.signature(init_method)
        return [
            ParameterInformation(parameter=parameter, type_=self._type_.origin)
            for name, parameter in init_signature.parameters.items()
            if name not in ["self", "args", "kwargs"]
        ]
