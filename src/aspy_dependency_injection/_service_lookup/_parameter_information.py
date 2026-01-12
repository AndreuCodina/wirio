import typing
from inspect import Parameter
from types import UnionType
from typing import Annotated, Any, Union, final

from aspy_dependency_injection._service_lookup._typed_type import TypedType


@final
class ParameterInformation:
    _parameter_type: TypedType
    _is_optional: bool
    _has_default_value: bool
    _default_value: object | None

    def __init__(self, parameter: Parameter) -> None:
        if parameter.annotation is Parameter.empty:
            error_message = (
                f"The parameter '{parameter.name}' must have a type annotation"
            )
            raise RuntimeError(error_message)

        self._is_optional = False
        self._has_default_value = False
        self._default_value = None
        origin = typing.get_origin(parameter.annotation)
        args = typing.get_args(parameter.annotation)

        if origin is Annotated:
            parameter_type = args[0]
            self._has_default_value = True

            if callable(args[1]):
                self._default_value = args[1]()
            else:
                self._default_value = args[1]

            origin = typing.get_origin(parameter_type)

            if self._is_origin_a_union(origin):
                args = typing.get_args(parameter_type)
                self._extract_from_union(parameter, args)
            else:
                self._parameter_type = TypedType.from_type(parameter_type)
        elif self._is_origin_a_union(origin):
            self._extract_from_union(parameter, args)
        else:
            self._parameter_type = TypedType.from_type(parameter.annotation)

            if parameter.default is not Parameter.empty:
                self._has_default_value = True
                self._default_value = parameter.default

    @property
    def parameter_type(self) -> TypedType:
        return self._parameter_type

    @property
    def is_optional(self) -> bool:
        return self._is_optional

    @property
    def has_default_value(self) -> bool:
        return self._has_default_value

    @property
    def default_value(self) -> object | None:
        return self._default_value

    def _is_origin_a_union(self, origin: type) -> bool:
        return origin is Union or origin is UnionType

    def _extract_from_union(self, parameter: Parameter, args: tuple[Any, ...]) -> None:
        length_of_a_union_of_a_type_and_none = 2  # Example: int | None

        if len(args) > length_of_a_union_of_a_type_and_none:
            error_message = f"The parameter '{parameter.name}' has a Union type with more than one non-None type"
            raise RuntimeError(error_message)

        if len(args) > 1 and type(None) not in args:
            error_message = (
                f"The parameter '{parameter.name}' has a Union type without None"
            )
            raise RuntimeError(error_message)

        self._parameter_type = TypedType.from_type(
            next(arg for arg in args if arg is not type(None))
        )
        self._is_optional = True

        if parameter.default is not Parameter.empty:
            self._has_default_value = True
            self._default_value = parameter.default
