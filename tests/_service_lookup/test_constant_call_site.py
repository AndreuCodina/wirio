import pytest

from wirio._service_lookup._constant_call_site import (
    ConstantCallSite,
)
from wirio._service_lookup._typed_type import TypedType


class TestConstantCallSite:
    def test_assign_assignable_value_to_service_type(self) -> None:
        class Parent:
            pass

        class Child(Parent):
            pass

        service_type = TypedType.from_type(Parent)

        ConstantCallSite(service_type=service_type, default_value=Child())

    def test_fail_when_assigning_not_assignable_value_to_service_type(self) -> None:
        class Parent:
            pass

        class NotChild:
            pass

        expected_error_message = "Constant value of type '<class 'tests._service_lookup.test_constant_call_site.TestConstantCallSite.test_fail_when_assigning_not_assignable_value_to_service_type.<locals>.NotChild'>' can't be converted to service type '<class 'tests._service_lookup.test_constant_call_site.TestConstantCallSite.test_fail_when_assigning_not_assignable_value_to_service_type.<locals>.Parent'>'"
        service_type = TypedType.from_type(Parent)

        with pytest.raises(TypeError) as exception_info:
            ConstantCallSite(service_type=service_type, default_value=NotChild())

        assert str(exception_info.value) == expected_error_message
