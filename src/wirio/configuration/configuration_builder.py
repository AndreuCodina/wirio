from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wirio.configuration.configuration_source import ConfigurationSource


class ConfigurationBuilder(ABC):
    @property
    @abstractmethod
    def sources(self) -> list["ConfigurationSource"]: ...
