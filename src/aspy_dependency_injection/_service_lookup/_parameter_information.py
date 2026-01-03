from inspect import Parameter
from typing import Final, final

from aspy_dependency_injection._service_lookup._optional_service import (
    unwrap_optional_type,
)
from aspy_dependency_injection._service_lookup._typed_type import TypedType


@final
class ParameterInformation:
    _parameter_type: Final[TypedType]
    _is_optional: Final[bool]
    _has_default: Final[bool]
    _default_value: Final[object | None]

    def __init__(self, parameter: Parameter, type_: type) -> None:
        if parameter.annotation is Parameter.empty:
            error_message = f"The parameter '{parameter.name}' of the class '{type_}' must have a type annotation"
            raise RuntimeError(error_message)

        unwrap_result = unwrap_optional_type(parameter.annotation)
        self._parameter_type = TypedType.from_type(unwrap_result.unwrapped_type)
        self._is_optional = unwrap_result.is_optional
        self._has_default = parameter.default is not Parameter.empty
        self._default_value = parameter.default if self._has_default else None

    @property
    def parameter_type(self) -> TypedType:
        return self._parameter_type

    @property
    def is_optional(self) -> bool:
        return self._is_optional

    @property
    def has_default(self) -> bool:
        return self._has_default

    @property
    def default_value(self) -> object | None:
        return self._default_value
