from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from wirio.configuration.configuration_provider import ConfigurationProvider

if TYPE_CHECKING:
    from wirio.configuration.configuration_builder import ConfigurationBuilder


class ConfigurationSource(ABC):
    """Represent a source of configuration key/values for an application."""

    @abstractmethod
    def build(self, builder: "ConfigurationBuilder") -> ConfigurationProvider: ...
