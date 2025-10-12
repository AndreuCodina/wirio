import contextlib
import importlib

from aspy_dependency_injection.types import InjectableType


def Inject() -> InjectableType:  # noqa: N802
    res = InjectableType()

    # Fastapi needs all dependencies to be wrapped with Depends.
    with contextlib.suppress(ModuleNotFoundError):

        def _inner() -> InjectableType:
            return res

        # This will act as a flag so that aspy knows this dependency belongs to it.
        _inner.__is_aspy_depends__ = True  # type: ignore[attr-defined]
        return importlib.import_module("fastapi").Depends(_inner)  # type: ignore[no-any-return]

    return res
