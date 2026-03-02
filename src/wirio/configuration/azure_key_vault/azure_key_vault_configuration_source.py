from typing import Final, final, override

from azure.core.credentials_async import AsyncTokenCredential

from wirio.configuration.azure_key_vault.azure_key_vault_configuration_provider import (
    AzureKeyVaultConfigurationProvider,
)
from wirio.configuration.configuration_builder import ConfigurationBuilder
from wirio.configuration.configuration_provider import ConfigurationProvider
from wirio.configuration.configuration_source import ConfigurationSource


@final
class AzureKeyVaultConfigurationSource(ConfigurationSource):
    _url: Final[str]
    _credential: Final[AsyncTokenCredential | None]

    def __init__(
        self,
        url: str,
        credential: AsyncTokenCredential | None = None,
    ) -> None:
        self._url = url
        self._credential = credential

    @override
    def build(self, builder: ConfigurationBuilder) -> ConfigurationProvider:
        return AzureKeyVaultConfigurationProvider(
            url=self._url, credential=self._credential
        )
