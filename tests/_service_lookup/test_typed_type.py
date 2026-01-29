import sys

import pytest

from wirio._service_lookup._typed_type import TypedType


class CustomClass:
    pass


class CustomClassWithGeneric1[T]:
    pass


class CustomClassWithGeneric2[T]:
    pass


class CustomClassWithGenerics1[T1, T2]:
    pass


class CustomClassWithGenerics2[T1, T2]:
    pass


class CustomClassWithOptionalGeneric1[T = None]:
    pass


class CustomClassWithOptionalGeneric2[T = None]:
    pass


class TestTypedType:
    @pytest.mark.parametrize(
        argnames=(
            "type_",
            "expected_representation_python_less_than_3_14",
            "expected_representation_python_greater_than_or_equal_3_14",
        ),
        argvalues=[
            (int, "builtins.int", "builtins.int"),
            (list[int], "builtins.list[builtins.int]", "builtins.list[builtins.int]"),
            (
                CustomClass,
                "tests._service_lookup.test_typed_type.CustomClass",
                "tests._service_lookup.test_typed_type.CustomClass",
            ),
            (
                CustomClassWithGeneric1[int],
                "tests._service_lookup.test_typed_type.CustomClassWithGeneric1[builtins.int]",
                "tests._service_lookup.test_typed_type.CustomClassWithGeneric1[builtins.int]",
            ),
            (
                CustomClassWithGeneric2[CustomClassWithGeneric2[int]],
                "tests._service_lookup.test_typed_type.CustomClassWithGeneric2[tests._service_lookup.test_typed_type.CustomClassWithGeneric2[builtins.int]]",
                "tests._service_lookup.test_typed_type.CustomClassWithGeneric2[tests._service_lookup.test_typed_type.CustomClassWithGeneric2[builtins.int]]",
            ),
            (
                CustomClassWithGenerics1[int, str],
                "tests._service_lookup.test_typed_type.CustomClassWithGenerics1[builtins.int, builtins.str]",
                "tests._service_lookup.test_typed_type.CustomClassWithGenerics1[builtins.int, builtins.str]",
            ),
            (
                int | str,
                "types.UnionType[builtins.int, builtins.str]",
                "typing.Union[builtins.int, builtins.str]",
            ),
            (
                CustomClassWithGenerics2[
                    int | CustomClassWithGeneric1[int | str],
                    CustomClassWithGeneric1[CustomClassWithGeneric1[str]],
                ],
                "tests._service_lookup.test_typed_type.CustomClassWithGenerics2[typing.Union[builtins.int, tests._service_lookup.test_typed_type.CustomClassWithGeneric1[types.UnionType[builtins.int, builtins.str]]], tests._service_lookup.test_typed_type.CustomClassWithGeneric1[tests._service_lookup.test_typed_type.CustomClassWithGeneric1[builtins.str]]]",
                "tests._service_lookup.test_typed_type.CustomClassWithGenerics2[typing.Union[builtins.int, tests._service_lookup.test_typed_type.CustomClassWithGeneric1[typing.Union[builtins.int, builtins.str]]], tests._service_lookup.test_typed_type.CustomClassWithGeneric1[tests._service_lookup.test_typed_type.CustomClassWithGeneric1[builtins.str]]]",
            ),
        ],
    )
    def test_represent_types(
        self,
        type_: type,
        expected_representation_python_less_than_3_14: str,
        expected_representation_python_greater_than_or_equal_3_14: str,
    ) -> None:
        typed_type = TypedType.from_type(type_)

        representation = repr(typed_type)

        if sys.version_info >= (3, 14):
            assert (
                representation
                == expected_representation_python_greater_than_or_equal_3_14
            )
        if sys.version_info < (3, 14):
            assert representation == expected_representation_python_less_than_3_14

    @pytest.mark.parametrize(
        argnames=(
            "type_",
            "expected_representation_python_less_than_3_14",
            "expected_representation_python_greater_than_or_equal_3_14",
        ),
        argvalues=[
            (int, None, None),
            (CustomClass, None, None),
            (
                CustomClassWithGenerics2[
                    int | CustomClassWithGeneric1[int], CustomClass
                ],
                "tests._service_lookup.test_typed_type.CustomClassWithGenerics2[typing.Union[int, tests._service_lookup.test_typed_type.CustomClassWithGeneric1[int]], tests._service_lookup.test_typed_type.CustomClass]",
                "tests._service_lookup.test_typed_type.CustomClassWithGenerics2[int | tests._service_lookup.test_typed_type.CustomClassWithGeneric1[int], tests._service_lookup.test_typed_type.CustomClass]",
            ),
        ],
    )
    def test_retain_type_information_when_creating_instances_of_classes_with_generics(
        self,
        type_: type,
        expected_representation_python_less_than_3_14: str | None,
        expected_representation_python_greater_than_or_equal_3_14: str | None,
    ) -> None:
        typed_type = TypedType.from_type(type_)
        type_instance = typed_type.invoke(parameter_values=[])

        orig_class = (
            str(getattr(type_instance, "__orig_class__"))  # noqa: B009
            if hasattr(type_instance, "__orig_class__")
            else None
        )

        if sys.version_info >= (3, 14):
            assert (
                orig_class == expected_representation_python_greater_than_or_equal_3_14
            )
        if sys.version_info < (3, 14):
            assert orig_class == expected_representation_python_less_than_3_14

    @pytest.mark.parametrize(
        argnames=("type_1", "type_2", "is_equal"),
        argvalues=[
            (int, int, True),
            (int, str, False),
            (CustomClassWithOptionalGeneric1, CustomClassWithOptionalGeneric1, True),
            (
                CustomClassWithOptionalGeneric1[int],
                CustomClassWithOptionalGeneric1[str],
                False,
            ),
            (
                CustomClassWithOptionalGeneric2[int],
                CustomClassWithOptionalGeneric2,
                False,
            ),
            (
                CustomClassWithGenerics1[int, str],
                CustomClassWithGenerics1[str, int],
                False,
            ),
        ],
    )
    def test_equality_and_hash(
        self, type_1: type, type_2: type, is_equal: bool
    ) -> None:
        typed_type_1 = TypedType.from_type(type_1)
        typed_type_2 = TypedType.from_type(type_2)

        if is_equal:
            assert typed_type_1 == typed_type_2
            assert hash(typed_type_1) == hash(typed_type_2)
        else:
            assert typed_type_1 != typed_type_2
            assert hash(typed_type_1) != hash(typed_type_2)

    def test_extract_type_hints_from_instance(self) -> None:
        expected_typed_type = TypedType.from_type(CustomClassWithGenerics2[int, str])

        typed_type = TypedType.from_instance(CustomClassWithGenerics2[int, str]())

        assert typed_type == expected_typed_type
        assert repr(typed_type) == repr(expected_typed_type)

    @pytest.mark.parametrize(
        argnames=("type_"),
        argvalues=[int, CustomClass],
    )
    def test_fail_when_creating_from_instance_without_type_information(
        self, type_: type
    ) -> None:
        with pytest.raises(
            ValueError,
            match="The instance does not retain type hint information because it has no generics",
        ):
            TypedType.from_instance(type_())
