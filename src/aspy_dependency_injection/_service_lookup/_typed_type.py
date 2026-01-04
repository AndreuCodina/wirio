import typing
from collections.abc import (
    Hashable,
)
from typing import Final, final, override


@final
class TypedType(Hashable):
    """Version of :class:`type` that takes into account generic parameters."""

    _origin: Final[type]
    _args: Final[tuple[type, ...]]

    def __init__(self, type_: type) -> None:
        origin = typing.get_origin(type_)
        has_no_generics = origin is None

        if has_no_generics:
            self._origin = type_
            self._args = typing.get_args(type_)
            return

        self._origin = origin
        self._args = typing.get_args(type_)

    @classmethod
    def from_type(cls, type_: type) -> TypedType:
        return cls(type_)

    @classmethod
    def from_instance(cls, instance: object) -> TypedType:
        instance_type = getattr(instance, "__orig_class__", None)

        if instance_type is None:
            error_message = "The instance does not retain type hint information because it has no generics"
            raise ValueError(error_message)

        return cls(instance_type)

    def to_type(self) -> type:
        return self._origin

    def invoke(self, parameter_values: list[object]) -> object:
        has_parameters = len(parameter_values) > 0
        has_generics = len(self._args) > 0

        if not has_parameters:
            if not has_generics:
                return self._origin()

            return self._origin[*self._args]()  # pyright: ignore[reportIndexIssue, reportUnknownVariableType]

        if not has_generics:
            return self._origin(*parameter_values)

        return self._origin[*self._args](*parameter_values)  # pyright: ignore[reportIndexIssue, reportUnknownVariableType]

    def __repr__(self) -> str:
        return self.create_representation(self._origin, self._args)

    def create_representation(self, origin: type, args: tuple[type, ...]) -> str:
        args_representation = ""

        if len(args) > 0:
            for arg in args:
                arg_origin = typing.get_origin(arg)
                arg_args = typing.get_args(arg)
                has_generics = arg_origin is not None

                if has_generics:
                    args_representation += self.create_representation(
                        arg_origin, arg_args
                    )
                else:
                    args_representation += f"{arg.__module__}.{arg.__qualname__}"

                if arg != args[-1]:
                    args_representation += ", "

        if len(args_representation) > 0:
            args_representation = f"[{args_representation}]"

        return f"{origin.__module__}.{origin.__qualname__}{args_representation}"

    @override
    def __hash__(self) -> int:
        return hash(self._origin) ^ hash(self._args)

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, TypedType):
            return NotImplemented

        return self._origin == value._origin and self._args == value._args
