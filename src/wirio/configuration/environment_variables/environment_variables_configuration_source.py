from typing import final, override

from wirio.configuration.configuration_builder import ConfigurationBuilder
from wirio.configuration.configuration_provider import ConfigurationProvider
from wirio.configuration.configuration_source import ConfigurationSource
from wirio.configuration.environment_variables.environment_variables_configuration_provider import (
    EnvironmentVariablesConfigurationProvider,
)


@final
class EnvironmentVariablesConfigurationSource(ConfigurationSource):
    @override
    def build(self, builder: ConfigurationBuilder) -> ConfigurationProvider:
        return EnvironmentVariablesConfigurationProvider()
