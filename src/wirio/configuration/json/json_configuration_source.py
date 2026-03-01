from pathlib import Path
from typing import final, override

from wirio.configuration.configuration_builder import ConfigurationBuilder
from wirio.configuration.configuration_provider import ConfigurationProvider
from wirio.configuration.configuration_source import ConfigurationSource
from wirio.configuration.json.json_configuration_provider import (
    JsonConfigurationProvider,
)


@final
class JsonConfigurationSource(ConfigurationSource):
    def __init__(self, path: Path, optional: bool) -> None:
        self._path = path
        self._optional = optional

    @override
    def build(self, builder: ConfigurationBuilder) -> ConfigurationProvider:
        return JsonConfigurationProvider(path=self._path, optional=self._optional)
