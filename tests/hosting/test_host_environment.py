import os

from pytest_mock import MockerFixture

from wirio.hosting._environment_variable import EnvironmentVariable
from wirio.hosting.environment import Environment
from wirio.hosting.host_environment import HostEnvironment


class TestHostEnvironment:
    def test_return_default_environment_name_when_environment_variable_is_not_set(
        self, mocker: MockerFixture
    ) -> None:
        expected_default_environment_name = Environment.LOCAL.value
        mocker.patch.dict(os.environ, {}, clear=True)

        environment = HostEnvironment(content_root_path="")

        assert environment.environment_name == expected_default_environment_name

    def test_return_updated_environment_name_when_environment_variable_is_set(
        self, mocker: MockerFixture
    ) -> None:
        expected_environment_name = "current_environment"
        mocker.patch.dict(
            os.environ,
            {EnvironmentVariable.WIRIO_ENVIRONMENT.value: expected_environment_name},
        )

        environment = HostEnvironment(content_root_path="")

        assert environment.environment_name == expected_environment_name

    def test_check_environment_equality(self, mocker: MockerFixture) -> None:
        expected_environment_name = "current_environment"
        not_expected_environment_name = "not_current_environment"
        mocker.patch.dict(
            os.environ,
            {EnvironmentVariable.WIRIO_ENVIRONMENT.value: expected_environment_name},
        )

        environment = HostEnvironment(content_root_path="")

        assert environment.is_environment(expected_environment_name)
        assert not environment.is_environment(not_expected_environment_name)

    def test_return_if_the_current_environment_is_the_requested_one(
        self, mocker: MockerFixture
    ) -> None:
        mocker.patch.dict(
            os.environ,
            {EnvironmentVariable.WIRIO_ENVIRONMENT.value: Environment.LOCAL.value},
        )
        environment = HostEnvironment(content_root_path="")
        assert environment.is_local()

        mocker.patch.dict(
            os.environ,
            {
                EnvironmentVariable.WIRIO_ENVIRONMENT.value: Environment.DEVELOPMENT.value
            },
        )
        environment = HostEnvironment(content_root_path="")
        assert environment.is_development()

        mocker.patch.dict(
            os.environ,
            {EnvironmentVariable.WIRIO_ENVIRONMENT.value: Environment.STAGING.value},
        )
        environment = HostEnvironment(content_root_path="")
        assert environment.is_staging()

        mocker.patch.dict(
            os.environ,
            {EnvironmentVariable.WIRIO_ENVIRONMENT.value: Environment.PRODUCTION.value},
        )
        environment = HostEnvironment(content_root_path="")
        assert environment.is_production()
