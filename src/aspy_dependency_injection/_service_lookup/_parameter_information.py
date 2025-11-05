from inspect import Parameter
from typing import Final


class ParameterInformation:
    _parameter_type: Final[type]

    def __init__(self, parameter: Parameter, type_: type) -> None:
        if parameter.annotation is Parameter.empty:
            error_message = f"The parameter '{parameter.name}' of the class '{type_}' must have a type annotation"
            raise RuntimeError(error_message)

        self._parameter_type = parameter.annotation

    @property
    def parameter_type(self) -> type:
        return self._parameter_type
