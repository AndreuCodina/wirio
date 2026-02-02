from collections.abc import Sequence
from inspect import Parameter
from typing import Any

from wirio.annotations import Injectable


class ParamUtils:
    @classmethod
    def get_injectable_dependency(cls, parameter: Parameter) -> Injectable | None:
        if not hasattr(parameter.annotation, "__metadata__"):
            return None

        metadata = cls._get_metadata(parameter)

        if metadata is None:
            return None

        metadata_item = metadata[0]

        if isinstance(metadata_item, Injectable):
            return metadata_item

        if hasattr(metadata_item, "dependency") and hasattr(
            metadata_item.dependency, "__is_wirio_depends__"
        ):
            dependency = metadata_item.dependency()  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType, reportAttributeAccessIssue]

            if isinstance(dependency, Injectable):
                return dependency

        return None

    @classmethod
    def _get_metadata(cls, parameter: Parameter) -> Sequence[Any] | None:
        if not hasattr(parameter.annotation, "__metadata__"):
            return None

        return parameter.annotation.__metadata__
