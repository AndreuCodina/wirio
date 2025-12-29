import pytest

from aspy_dependency_injection._service_lookup._typed_type import TypedType


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
        argnames=("type_", "expected_representation"),
        argvalues=[
            (int, "builtins.int"),
            (list[int], "builtins.list[builtins.int]"),
            (CustomClass, "tests._service_lookup.test_typed_type.CustomClass"),
            (
                CustomClassWithGeneric1[int],
                "tests._service_lookup.test_typed_type.CustomClassWithGeneric1[builtins.int]",
            ),
            (
                CustomClassWithGeneric2[CustomClassWithGeneric2[int]],
                "tests._service_lookup.test_typed_type.CustomClassWithGeneric2[tests._service_lookup.test_typed_type.CustomClassWithGeneric2[builtins.int]]",
            ),
            (
                CustomClassWithGenerics1[int, str],
                "tests._service_lookup.test_typed_type.CustomClassWithGenerics1[builtins.int, builtins.str]",
            ),
            (int | str, "typing.Union[builtins.int, builtins.str]"),
            (
                CustomClassWithGenerics2[
                    int | CustomClassWithGeneric1[int | str], CustomClass
                ],
                "tests._service_lookup.test_typed_type.CustomClassWithGenerics2[typing.Union[builtins.int, tests._service_lookup.test_typed_type.CustomClassWithGeneric1[typing.Union[builtins.int, builtins.str]]], tests._service_lookup.test_typed_type.CustomClass]",
            ),
        ],
    )
    def test_represent_types(self, type_: type, expected_representation: str) -> None:
        typed_type = TypedType(type_)

        representation = repr(typed_type)

        assert representation == expected_representation

    @pytest.mark.parametrize(
        argnames=("type_", "expected_representation"),
        argvalues=[
            (int, None),
            (CustomClass, None),
            (
                CustomClassWithGenerics2[
                    int | CustomClassWithGeneric1[int], CustomClass
                ],
                "tests._service_lookup.test_typed_type.CustomClassWithGenerics2[int | tests._service_lookup.test_typed_type.CustomClassWithGeneric1[int], tests._service_lookup.test_typed_type.CustomClass]",
            ),
        ],
    )
    def test_retain_type_information_when_create_instances_of_classes_with_generics(
        self, type_: type, expected_representation: str | None
    ) -> None:
        typed_type = TypedType(type_)
        type_instance = typed_type.invoke(parameter_values=[])

        orig_class = (
            str(getattr(type_instance, "__orig_class__"))  # noqa: B009
            if hasattr(type_instance, "__orig_class__")
            else None
        )

        assert orig_class == expected_representation

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
        ],
    )
    def test_equality_and_hash(
        self, type_1: type, type_2: type, is_equal: bool
    ) -> None:
        typed_type_1 = TypedType(type_1)
        typed_type_2 = TypedType(type_2)

        if is_equal:
            assert typed_type_1 == typed_type_2
            assert hash(typed_type_1) == hash(typed_type_2)
        else:
            assert typed_type_1 != typed_type_2
            assert hash(typed_type_1) != hash(typed_type_2)
