from fastapi import Depends

from aspy_dependency_injection.injectable_type import InjectableType


def Inject() -> InjectableType:  # noqa: N802
    """Inject Depends for FastAPI integration."""

    def _dependency() -> InjectableType:
        return InjectableType()

    return Depends(_dependency, use_cache=False)
