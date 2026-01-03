from dataclasses import dataclass
from types import UnionType
from typing import Annotated, Union, get_args, get_origin


@dataclass(frozen=True)
class OptionalUnwrapResult:
    unwrapped_type: type
    is_optional: bool


def unwrap_optional_type(annotation: type) -> OptionalUnwrapResult:
    """Return the wrapped type and whether the annotation represents ``T | None``."""
    unwrapped_annotation = annotation
    origin = get_origin(unwrapped_annotation)
    args = get_args(unwrapped_annotation)

    if origin is Annotated:
        unwrapped_annotation = args[0]
        origin = get_origin(unwrapped_annotation)
        args = get_args(unwrapped_annotation)

    if origin in (UnionType, Union):
        non_none_args: list[type] = []
        has_none = False

        for arg in args:
            if arg is type(None):  # noqa: E721
                has_none = True
                continue

            non_none_args.append(arg)

        if has_none and len(non_none_args) == 1:
            return OptionalUnwrapResult(unwrapped_type=non_none_args[0], is_optional=True)

    return OptionalUnwrapResult(unwrapped_type=unwrapped_annotation, is_optional=False)
