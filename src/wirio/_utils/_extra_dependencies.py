class ExtraDependencies:
    @staticmethod
    def is_fastapi_installed() -> bool:
        try:
            import fastapi  # pyright: ignore[reportUnusedImport] # noqa: F401, PLC0415
        except ImportError:
            return False

        return True

    @staticmethod
    def import_fastapi() -> None:
        try:
            from fastapi import (  # noqa: PLC0415
                FastAPI,  # pyright: ignore[reportUnusedImport]  # noqa: F401
            )
        except ImportError as error:
            error_message = "FastAPI is not installed. Please, run 'uv add wirio[fastapi]' to install the required dependencies."
            raise ImportError(error_message) from error
