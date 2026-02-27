import os
from typing import final, override

from wirio.configuration.configuration_provider import ConfigurationProvider


@final
class EnvironmentVariablesConfigurationProvider(ConfigurationProvider):
    @override
    async def load(self) -> None:
        self._data = dict(os.environ)
        await super().load()
