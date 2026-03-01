import json
from pathlib import Path
from typing import Any, final, override

from wirio.configuration.configuration_provider import ConfigurationProvider


@final
class JsonConfigurationProvider(ConfigurationProvider):
    def __init__(self, path: Path, optional: bool) -> None:
        super().__init__()
        self._path = path
        self._optional = optional

    @override
    async def load(self) -> None:
        if not self._path.exists():
            if self._optional:
                self._data = {}
                await super().load()
                return

            error_message = f"Configuration file '{self._path}' was not found"
            raise FileNotFoundError(error_message)

        with self._path.open(encoding="utf-8") as file:
            json_data = json.load(file)

        self._data = {
            str(key): self._convert_to_configuration_value(value)
            for key, value in json_data.items()
        }
        await super().load()

    def _convert_to_configuration_value(
        self,
        value: Any,  # noqa: ANN401
    ) -> str | None:
        if value is None:
            return None

        if isinstance(value, str):
            return value

        return str(value)
