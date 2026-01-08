from fastapi import Depends

from aspy_dependency_injection.injectable import Injectable


def Inject() -> Injectable:  # noqa: N802
    """Inject :func:`Depends` for FastAPI integration."""

    def _dependency() -> Injectable:
        return Injectable()

    _dependency.__is_aspy_depends__ = True  # pyright: ignore[reportFunctionMemberAccess]
    return Depends(_dependency, use_cache=False)
