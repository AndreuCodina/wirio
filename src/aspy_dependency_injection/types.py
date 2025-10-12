from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

AnyCallable = Callable[..., Any]


class InjectableType:
    service: type[Any] | None

    """Base type for anything that should be injected using annotation hints."""

    def __init__(self) -> None:
        self.service = None


@dataclass(frozen=True)
class TemplatedString:
    """Wrapper for strings which contain values that must be interpolated by the parameter bag.

    Use this with the special ${param_name} syntax to reference a parameter in a string similar to python f-string.
    Strings in Inject(expr="") calls are automatically wrapped.
    """

    __slots__ = ("value",)

    value: str


ParameterReference = str | TemplatedString


@dataclass(frozen=True)
class ParameterWrapper(InjectableType):
    """Wrapper for parameter values. This indicates to the container registry that this argument is a parameter."""

    __slots__ = ("param",)
    param: ParameterReference


class AnnotatedParameter:
    """Represent an annotated dependency parameter."""

    __slots__ = ("annotation", "is_parameter", "klass", "obj_id", "qualifier_value")

    def __init__(
        self,
        klass: type[Any],
        annotation: InjectableType | None = None,
    ) -> None:
        """Create a new AnnotatedParameter.

        If the annotation is a ContainerProxyQualifier, `qualifier_value` will be set to its value.

        :param klass: The type of the dependency
        :param annotation: Any annotation passed along. Such as Inject(param=...) calls
        """
        self.klass = klass
        self.annotation = annotation
        self.is_parameter = isinstance(self.annotation, ParameterWrapper)
        self.obj_id = self.klass, self.qualifier_value

    def __eq__(self, other: object) -> bool:
        """Check if two things are equal."""
        return (
            isinstance(other, AnnotatedParameter)
            and self.klass == other.klass
            and self.annotation == other.annotation
            and self.is_parameter == other.is_parameter
        )

    def __hash__(self) -> int:
        """Hash things."""
        return hash(
            (self.klass, self.annotation, self.qualifier_value, self.is_parameter)
        )
