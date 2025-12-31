from inspect import Parameter
from typing import Final, final

from aspy_dependency_injection._service_lookup._typed_type import TypedType


@final
class ParameterInformation:
    _parameter_type: Final[TypedType]

    def __init__(self, parameter: Parameter, type_: type) -> None:
        if parameter.annotation is Parameter.empty:
            error_message = f"The parameter '{parameter.name}' of the class '{type_}' must have a type annotation"
            raise RuntimeError(error_message)

        self._parameter_type = TypedType.from_type(parameter.annotation)

    @property
    def parameter_type(self) -> TypedType:
        return self._parameter_type
