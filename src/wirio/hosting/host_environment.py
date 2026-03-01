import os
from typing import Final, final

from wirio.hosting._environment_variable import EnvironmentVariable
from wirio.hosting.environment import Environment


@final
class HostEnvironment:
    """Provide information about the hosting environment an application is running in."""

    _environment_name: Final[str]
    _content_root_path: Final[str]

    def __init__(self, content_root_path: str) -> None:
        self._environment_name = self._get_current_environment_name()
        self._content_root_path = content_root_path

    @property
    def environment_name(self) -> str:
        """Environment name."""
        return self._environment_name

    @property
    def content_root_path(self) -> str:
        """Absolute path to the directory that contains the application content files."""
        return self._content_root_path

    def is_environment(self, environment_name: str) -> bool:
        """Compare the current host environment name against the specified value."""
        return self._environment_name == environment_name

    def is_local(self) -> bool:
        """Check if the current host environment name is `local`."""
        return self.is_environment(Environment.LOCAL.value)

    def is_development(self) -> bool:
        """Check if the current host environment name is `development`."""
        return self.is_environment(Environment.DEVELOPMENT.value)

    def is_staging(self) -> bool:
        """Check if the current host environment name is `staging`."""
        return self.is_environment(Environment.STAGING.value)

    def is_production(self) -> bool:
        """Check if the current host environment name is `production`."""
        return self.is_environment(Environment.PRODUCTION.value)

    def _get_current_environment_name(self) -> str:
        return os.getenv(
            EnvironmentVariable.WIRIO_ENVIRONMENT.value, Environment.LOCAL.value
        )
