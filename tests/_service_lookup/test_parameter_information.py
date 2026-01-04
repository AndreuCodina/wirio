import inspect
from typing import Annotated, Optional, Union

import pytest

from aspy_dependency_injection._service_lookup._parameter_information import (
    ParameterInformation,
)


class TestParameterInformation:
    @pytest.mark.parametrize(
        argnames=(
            "parameter_name",
            "expected_is_optional",
            "expected_has_default_value",
            "expected_default_value",
        ),
        argvalues=[
            ("annotated", False, True, "default"),
            ("annotated_union_with_none", True, True, "default"),
            ("annotated_union_with_none_and_default_function", False, True, "default"),
            ("string", False, False, None),
            ("string_union_with_none", True, False, None),
            ("string_union_with_none_and_default_to_none", True, True, None),
            ("string_union_with_none_and_default_to_value", True, True, "default"),
            ("union_of_string_with_none_and_default_to_value", True, True, "default"),
            ("optional_string_and_default_to_value", True, True, "default"),
            ("string_and_default_to_value", False, True, "default"),
        ],
    )
    def test_resolve_service_with_no_dependencies(
        self,
        parameter_name: str,
        expected_is_optional: bool,
        expected_has_default_value: bool,
        expected_default_value: object | None,
    ) -> None:
        def get_default() -> str:
            return "default"

        def function(  # noqa: PLR0913
            annotated: Annotated[str, "default"],
            annotated_union_with_none: Annotated[str | None, "default"],
            annotated_union_with_none_and_default_function: Annotated[str, get_default],
            string: str,
            string_union_with_none: str | None,
            string_union_with_none_and_default_to_none: str | None = None,
            string_union_with_none_and_default_to_value: str | None = "default",
            union_of_string_with_none_and_default_to_value: Union[  # noqa: UP007
                str, None
            ] = "default",
            optional_string_and_default_to_value: Optional[str] = "default",  # noqa: UP045
            string_and_default_to_value: str = "default",
        ) -> None:
            pass

        signature = inspect.signature(function)
        parameter = signature.parameters[parameter_name]
        parameter_information = ParameterInformation(parameter)

        assert parameter_information.parameter_type.to_type() is str
        assert parameter_information.is_optional == expected_is_optional
        assert parameter_information.has_default_value == expected_has_default_value
        assert parameter_information.default_value == expected_default_value

    def test_fail_when_union_type_has_several_types_instead_of_only_a_type_with_none(
        self,
    ) -> None:
        def function(value: int | str) -> None:
            pass

        signature = inspect.signature(function)
        parameter = signature.parameters["value"]

        with pytest.raises(RuntimeError) as exception_info:
            ParameterInformation(parameter)

        assert (
            str(exception_info.value)
            == "The parameter 'value' has a Union type without None"
        )

    def test_fail_when_union_type_has_several_types_including_none_instead_of_only_a_type_with_none(
        self,
    ) -> None:
        def function(value: int | str | None) -> None:
            pass

        signature = inspect.signature(function)
        parameter = signature.parameters["value"]

        with pytest.raises(RuntimeError) as exception_info:
            ParameterInformation(parameter)

        assert (
            str(exception_info.value)
            == "The parameter 'value' has a Union type with more than one non-None type"
        )
