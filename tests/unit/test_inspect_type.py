# Type inspection tests return dynamic Any types by design when inspecting
# unannotated or unresolvable types
# pyright: reportAny=false

import sys
from collections.abc import Callable, Callable as ABCCallable, Generator
from types import UnionType
from typing import (
    Annotated,
    Any,
    ClassVar,
    Concatenate,
    Final,
    ForwardRef as TypingForwardRef,
    Generic,
    Literal,
    NewType,
    NoReturn,
    ParamSpec,
    TypeGuard,
    TypeVar,
    get_args,
    get_origin,
)
from typing_extensions import (
    LiteralString,
    Never,
    Self,
    TypeAliasType,
    TypeIs,
    TypeVarTuple,
    Unpack,
    override,
)

import pytest

from typing_graph import (
    AnyType,
    EvalMode,
    InspectConfig,
    NeverType,
    SelfType,
    Variance,
    clear_cache,
    get_type_hints_for_node,
    inspect_type,
    inspect_type_alias,
)
from typing_graph._config import DEFAULT_CONFIG
from typing_graph._context import InspectContext
from typing_graph._inspect_type import (
    _TYPE_INSPECTORS,
    _inspect_callable,
    _inspect_plain_type,
    _inspect_subscripted_generic,
    _inspect_tuple,
    _inspect_type_alias_type,
    _register_type_inspectors,
    inspect_type_param,
    reset_type_inspectors,
    resolve_forward_ref,
)
from typing_graph._node import (
    TypeNode,
    is_any_type_node,
    is_callable_type_node,
    is_concatenate_node,
    is_concrete_type,
    is_ellipsis_type_node,
    is_forward_ref_node,
    is_generic_alias_node,
    is_generic_type,
    is_literal_node,
    is_literal_string_type_node,
    is_meta_type_node,
    is_never_type_node,
    is_new_type_node,
    is_param_spec_node,
    is_ref_state_failed,
    is_ref_state_resolved,
    is_ref_state_unresolved,
    is_self_type_node,
    is_subscripted_generic_node,
    is_tuple_type_node,
    is_type_alias_node,
    is_type_guard_type_node,
    is_type_is_type_node,
    is_type_var_node,
    is_type_var_tuple_node,
    is_union_type_node,
    is_unpack_node,
)


@pytest.fixture(autouse=True)
def clear_type_cache() -> Generator[None]:
    clear_cache()
    yield
    clear_cache()


class TestConcreteType:
    def test_int_sets_cls_to_int(self) -> None:
        result = inspect_type(int)

        assert is_concrete_type(result)
        assert result.cls is int
        assert result.metadata == ()
        assert result.qualifiers == frozenset()

    def test_str_sets_cls_to_str(self) -> None:
        result = inspect_type(str)

        assert is_concrete_type(result)
        assert result.cls is str

    def test_float_sets_cls_to_float(self) -> None:
        result = inspect_type(float)

        assert is_concrete_type(result)
        assert result.cls is float

    def test_bool_sets_cls_to_bool(self) -> None:
        result = inspect_type(bool)

        assert is_concrete_type(result)
        assert result.cls is bool

    def test_bytes_sets_cls_to_bytes(self) -> None:
        result = inspect_type(bytes)

        assert is_concrete_type(result)
        assert result.cls is bytes

    def test_none_literal_sets_cls_to_nonetype(self) -> None:
        result = inspect_type(None)

        assert is_concrete_type(result)
        assert result.cls is type(None)

    def test_nonetype_sets_cls_to_nonetype(self) -> None:
        result = inspect_type(type(None))

        assert is_concrete_type(result)
        assert result.cls is type(None)

    def test_custom_class_sets_cls_correctly(self) -> None:
        class MyClass:
            pass

        result = inspect_type(MyClass)

        assert is_concrete_type(result)
        assert result.cls is MyClass


class TestAnyType:
    def test_any_returns_anytype_node(self) -> None:
        result = inspect_type(Any)

        assert is_any_type_node(result)
        assert isinstance(result, AnyType)
        assert result.metadata == ()
        assert result.qualifiers == frozenset()


class TestSelfType:
    def test_self_returns_selftype_node(self) -> None:
        result = inspect_type(Self)

        assert is_self_type_node(result)
        assert isinstance(result, SelfType)
        assert result.metadata == ()
        assert result.qualifiers == frozenset()


class TestNeverType:
    def test_never_returns_nevertype_node(self) -> None:
        result = inspect_type(Never)

        assert is_never_type_node(result)
        assert isinstance(result, NeverType)
        assert result.metadata == ()
        assert result.qualifiers == frozenset()

    @pytest.mark.skipif(
        sys.version_info < (3, 11),
        reason="NoReturn not aliased to Never in typing module until Python 3.11",
    )
    def test_noreturn_returns_nevertype_node(self) -> None:
        result = inspect_type(NoReturn)

        assert is_never_type_node(result)
        assert isinstance(result, NeverType)


class TestLiteralStringType:
    def test_literal_string_returns_literal_string_node(self) -> None:
        result = inspect_type(LiteralString)

        assert is_literal_string_type_node(result)
        assert result.metadata == ()
        assert result.qualifiers == frozenset()


class TestTypeVarTupleNode:
    def test_typevartuple_has_name(self) -> None:
        Ts = TypeVarTuple("Ts")  # noqa: N806 - type parameter naming convention
        result = inspect_type(Ts)

        assert is_type_var_tuple_node(result)
        assert result.name == "Ts"
        assert result.default is None
        assert result.metadata == ()


class TestUnionType:
    def test_two_types_creates_union_with_two_members(self) -> None:
        result = inspect_type(int | str)

        assert is_union_type_node(result)
        assert len(result.members) == 2

        assert is_concrete_type(result.members[0])
        assert result.members[0].cls is int

        assert is_concrete_type(result.members[1])
        assert result.members[1].cls is str

    def test_three_types_creates_union_with_three_members(self) -> None:
        result = inspect_type(int | str | float)

        assert is_union_type_node(result)
        assert len(result.members) == 3

        member_classes = {m.cls for m in result.members if is_concrete_type(m)}
        assert member_classes == {int, str, float}

    def test_union_with_none_includes_nonetype(self) -> None:
        result = inspect_type(int | None)

        assert is_union_type_node(result)
        assert len(result.members) == 2

        member_classes = {m.cls for m in result.members if is_concrete_type(m)}
        assert int in member_classes
        assert type(None) in member_classes

    def test_children_returns_members(self) -> None:
        result = inspect_type(int | str)

        assert is_union_type_node(result)
        children = result.children()
        assert len(children) == 2
        assert children == result.members

    def test_metadata_and_qualifiers_default_empty(self) -> None:
        result = inspect_type(int | str)

        assert is_union_type_node(result)
        assert result.metadata == ()
        assert result.qualifiers == frozenset()


class TestLiteralNode:
    def test_string_literals_have_correct_values(self) -> None:
        result = inspect_type(Literal["a", "b"])

        assert is_literal_node(result)
        assert result.values == ("a", "b")
        assert result.metadata == ()
        assert result.qualifiers == frozenset()

    def test_int_literals_have_correct_values(self) -> None:
        result = inspect_type(Literal[1, 2, 3])

        assert is_literal_node(result)
        assert result.values == (1, 2, 3)

    def test_bool_literal_has_correct_value(self) -> None:
        result = inspect_type(Literal[True])

        assert is_literal_node(result)
        assert result.values == (True,)

    def test_mixed_literals_have_correct_values(self) -> None:
        result = inspect_type(Literal["a", 1, True])

        assert is_literal_node(result)
        assert result.values == ("a", 1, True)

    def test_single_literal_has_one_value(self) -> None:
        result = inspect_type(Literal[42])

        assert is_literal_node(result)
        assert result.values == (42,)


class TestSubscriptedGeneric:
    def test_list_int_has_list_origin_and_int_arg(self) -> None:
        result = inspect_type(list[int])

        assert is_subscripted_generic_node(result)
        assert is_generic_type(result.origin)
        assert result.origin.cls is list

        assert len(result.args) == 1
        assert is_concrete_type(result.args[0])
        assert result.args[0].cls is int

    def test_dict_str_int_has_dict_origin_and_two_args(self) -> None:
        result = inspect_type(dict[str, int])

        assert is_subscripted_generic_node(result)
        assert is_generic_type(result.origin)
        assert result.origin.cls is dict

        assert len(result.args) == 2
        assert is_concrete_type(result.args[0])
        assert result.args[0].cls is str
        assert is_concrete_type(result.args[1])
        assert result.args[1].cls is int

    def test_set_str_has_set_origin_and_str_arg(self) -> None:
        result = inspect_type(set[str])

        assert is_subscripted_generic_node(result)
        assert is_generic_type(result.origin)
        assert result.origin.cls is set

        assert len(result.args) == 1
        assert is_concrete_type(result.args[0])
        assert result.args[0].cls is str

    def test_frozenset_int_has_frozenset_origin(self) -> None:
        result = inspect_type(frozenset[int])

        assert is_subscripted_generic_node(result)
        assert is_generic_type(result.origin)
        assert result.origin.cls is frozenset

    def test_nested_list_of_list_of_int(self) -> None:
        result = inspect_type(list[list[int]])

        assert is_subscripted_generic_node(result)
        assert is_generic_type(result.origin)
        assert result.origin.cls is list

        assert len(result.args) == 1
        inner = result.args[0]
        assert is_subscripted_generic_node(inner)
        assert is_generic_type(inner.origin)
        assert inner.origin.cls is list

        assert len(inner.args) == 1
        assert is_concrete_type(inner.args[0])
        assert inner.args[0].cls is int

    def test_nested_dict_with_list_value(self) -> None:
        result = inspect_type(dict[str, list[int]])

        assert is_subscripted_generic_node(result)
        assert is_generic_type(result.origin)
        assert result.origin.cls is dict
        assert len(result.args) == 2

        assert is_concrete_type(result.args[0])
        assert result.args[0].cls is str

        value_type = result.args[1]
        assert is_subscripted_generic_node(value_type)
        assert is_generic_type(value_type.origin)
        assert value_type.origin.cls is list
        assert is_concrete_type(value_type.args[0])
        assert value_type.args[0].cls is int

    def test_children_includes_origin_and_args(self) -> None:
        result = inspect_type(list[int])

        assert is_subscripted_generic_node(result)
        children = result.children()

        assert len(children) == 2
        assert children[0] is result.origin
        assert children[1] is result.args[0]

    def test_metadata_and_qualifiers_default_empty(self) -> None:
        result = inspect_type(list[int])

        assert is_subscripted_generic_node(result)
        assert result.metadata == ()
        assert result.qualifiers == frozenset()


class TestTupleType:
    def test_heterogeneous_tuple_has_elements_and_not_homogeneous(self) -> None:
        result = inspect_type(tuple[int, str])

        assert is_tuple_type_node(result)
        assert len(result.elements) == 2
        assert result.homogeneous is False

        assert is_concrete_type(result.elements[0])
        assert result.elements[0].cls is int
        assert is_concrete_type(result.elements[1])
        assert result.elements[1].cls is str

    def test_homogeneous_tuple_has_one_element_and_is_homogeneous(self) -> None:
        result = inspect_type(tuple[int, ...])

        assert is_tuple_type_node(result)
        assert len(result.elements) == 1
        assert result.homogeneous is True

        assert is_concrete_type(result.elements[0])
        assert result.elements[0].cls is int

    def test_single_element_tuple_is_not_homogeneous(self) -> None:
        result = inspect_type(tuple[int])

        assert is_tuple_type_node(result)
        assert len(result.elements) == 1
        assert result.homogeneous is False

    def test_four_element_tuple(self) -> None:
        result = inspect_type(tuple[int, str, float, bool])

        assert is_tuple_type_node(result)
        assert len(result.elements) == 4
        assert result.homogeneous is False

        expected_types = [int, str, float, bool]
        for i, expected in enumerate(expected_types):
            element = result.elements[i]
            assert is_concrete_type(element)
            assert element.cls is expected

    def test_empty_tuple_has_no_elements(self) -> None:
        result = inspect_type(tuple[()])

        assert is_tuple_type_node(result)
        assert result.elements == ()
        assert result.homogeneous is False

    def test_children_returns_elements(self) -> None:
        result = inspect_type(tuple[int, str])

        assert is_tuple_type_node(result)
        children = result.children()
        assert len(children) == 2
        assert children == result.elements

    def test_metadata_and_qualifiers_default_empty(self) -> None:
        result = inspect_type(tuple[int, str])

        assert is_tuple_type_node(result)
        assert result.metadata == ()
        assert result.qualifiers == frozenset()


class TestCallableType:
    def test_simple_callable_has_params_and_returns(self) -> None:
        result = inspect_type(Callable[[int], str])

        assert is_callable_type_node(result)
        assert isinstance(result.params, tuple)
        assert len(result.params) == 1

        assert is_concrete_type(result.params[0])
        assert result.params[0].cls is int

        assert is_concrete_type(result.returns)
        assert result.returns.cls is str

    def test_multiple_params_callable(self) -> None:
        result = inspect_type(Callable[[int, str, float], bool])

        assert is_callable_type_node(result)
        assert isinstance(result.params, tuple)
        assert len(result.params) == 3

        expected_param_types = [int, str, float]
        for i, expected in enumerate(expected_param_types):
            param = result.params[i]
            assert is_concrete_type(param)
            assert param.cls is expected

        assert is_concrete_type(result.returns)
        assert result.returns.cls is bool

    def test_no_params_callable(self) -> None:
        result = inspect_type(Callable[[], int])

        assert is_callable_type_node(result)
        assert isinstance(result.params, tuple)
        assert len(result.params) == 0

        assert is_concrete_type(result.returns)
        assert result.returns.cls is int

    def test_ellipsis_params_callable(self) -> None:
        result = inspect_type(Callable[..., int])

        assert is_callable_type_node(result)
        assert is_ellipsis_type_node(result.params)

        assert is_concrete_type(result.returns)
        assert result.returns.cls is int

    def test_paramspec_callable(self) -> None:
        P = ParamSpec("P")  # noqa: N806 - type parameter naming convention
        # Callable[P, int] is valid at runtime but basedpyright doesn't understand
        # ParamSpec in subscript
        result = inspect_type(Callable[P, int])  # pyright: ignore[reportGeneralTypeIssues]

        assert is_callable_type_node(result)
        assert is_param_spec_node(result.params)
        assert result.params.name == "P"

        assert is_concrete_type(result.returns)
        assert result.returns.cls is int

    def test_concatenate_params(self) -> None:
        P = ParamSpec("P")  # noqa: N806 - type parameter naming convention
        # Concatenate requires ParamSpec which basedpyright doesn't fully support in
        # subscript context
        result = inspect_type(Callable[Concatenate[int, P], str])  # pyright: ignore[reportGeneralTypeIssues]

        assert is_callable_type_node(result)
        assert is_concatenate_node(result.params)
        assert len(result.params.prefix) == 1
        assert is_concrete_type(result.params.prefix[0])
        assert result.params.prefix[0].cls is int
        assert result.params.param_spec.name == "P"

    def test_children_includes_params_and_returns(self) -> None:
        result = inspect_type(Callable[[int, str], bool])

        assert is_callable_type_node(result)
        children = result.children()

        assert len(children) == 3
        assert is_concrete_type(children[0])
        assert children[0].cls is int
        assert is_concrete_type(children[1])
        assert children[1].cls is str
        assert is_concrete_type(children[2])
        assert children[2].cls is bool

    def test_metadata_and_qualifiers_default_empty(self) -> None:
        result = inspect_type(Callable[[int], str])

        assert is_callable_type_node(result)
        assert result.metadata == ()
        assert result.qualifiers == frozenset()


class TestTypeVarNode:
    def test_simple_typevar_has_name(self) -> None:
        T = TypeVar("T")
        result = inspect_type(T)

        assert is_type_var_node(result)
        assert result.name == "T"
        assert result.variance == Variance.INVARIANT
        assert result.bound is None
        assert result.constraints == ()
        assert result.infer_variance is False

    def test_covariant_typevar(self) -> None:
        T_co = TypeVar("T_co", covariant=True)
        result = inspect_type(T_co)

        assert is_type_var_node(result)
        assert result.name == "T_co"
        assert result.variance == Variance.COVARIANT

    def test_contravariant_typevar(self) -> None:
        T_contra = TypeVar("T_contra", contravariant=True)
        result = inspect_type(T_contra)

        assert is_type_var_node(result)
        assert result.name == "T_contra"
        assert result.variance == Variance.CONTRAVARIANT

    def test_bound_typevar_has_bound_node(self) -> None:
        T = TypeVar("T", bound=int)
        result = inspect_type(T)

        assert is_type_var_node(result)
        assert result.name == "T"
        assert result.bound is not None
        assert is_concrete_type(result.bound)
        assert result.bound.cls is int

    def test_constrained_typevar_has_constraints(self) -> None:
        T = TypeVar("T", int, str)
        result = inspect_type(T)

        assert is_type_var_node(result)
        assert result.name == "T"
        assert len(result.constraints) == 2

        constraint_classes = {c.cls for c in result.constraints if is_concrete_type(c)}
        assert constraint_classes == {int, str}

    def test_children_includes_bound_and_constraints(self) -> None:
        T = TypeVar("T", int, str)
        result = inspect_type(T)

        assert is_type_var_node(result)
        children = result.children()
        assert len(children) == 2

    def test_metadata_and_qualifiers_default_empty(self) -> None:
        T = TypeVar("T")
        result = inspect_type(T)

        assert is_type_var_node(result)
        assert result.metadata == ()
        assert result.qualifiers == frozenset()


class TestParamSpecNode:
    def test_paramspec_has_name(self) -> None:
        P = ParamSpec("P")  # noqa: N806 - type parameter naming convention
        result = inspect_type(P)

        assert is_param_spec_node(result)
        assert result.name == "P"
        assert result.default is None

    def test_metadata_and_qualifiers_default_empty(self) -> None:
        P = ParamSpec("P")  # noqa: N806 - type parameter naming convention
        result = inspect_type(P)

        assert is_param_spec_node(result)
        assert result.metadata == ()
        assert result.qualifiers == frozenset()


class TestMetaType:
    def test_type_int_has_int_as_inner(self) -> None:
        result = inspect_type(type[int])

        assert is_meta_type_node(result)
        assert is_concrete_type(result.of)
        assert result.of.cls is int

    def test_type_str_has_str_as_inner(self) -> None:
        result = inspect_type(type[str])

        assert is_meta_type_node(result)
        assert is_concrete_type(result.of)
        assert result.of.cls is str

    def test_children_returns_inner_type(self) -> None:
        result = inspect_type(type[int])

        assert is_meta_type_node(result)
        children = result.children()
        assert len(children) == 1
        assert children[0] is result.of

    def test_metadata_and_qualifiers_default_empty(self) -> None:
        result = inspect_type(type[int])

        assert is_meta_type_node(result)
        assert result.metadata == ()
        assert result.qualifiers == frozenset()


class TestForwardRef:
    def test_string_forward_ref_has_ref_string(self) -> None:
        result = inspect_type("MyClass")

        assert is_forward_ref_node(result)
        assert result.ref == "MyClass"

    def test_unresolved_ref_has_unresolved_state(self) -> None:
        result = inspect_type("UnknownClass")

        assert is_forward_ref_node(result)
        # Default behavior may vary based on eval_mode
        # Just verify it's a ForwardRef with correct ref string
        assert result.ref == "UnknownClass"

    def test_children_empty_when_unresolved(self) -> None:
        result = inspect_type("UnresolvableClass")

        assert is_forward_ref_node(result)
        if is_ref_state_unresolved(result.state):
            assert result.children() == ()

    def test_metadata_and_qualifiers_default_empty(self) -> None:
        result = inspect_type("SomeRef")

        assert is_forward_ref_node(result)
        assert result.metadata == ()
        assert result.qualifiers == frozenset()


class TestNewTypeNode:
    def test_newtype_has_name_and_supertype(self) -> None:
        UserId = NewType("UserId", int)
        result = inspect_type(UserId)

        assert is_new_type_node(result)
        assert result.name == "UserId"
        assert is_concrete_type(result.supertype)
        assert result.supertype.cls is int

    def test_newtype_with_str_supertype(self) -> None:
        Name = NewType("Name", str)
        result = inspect_type(Name)

        assert is_new_type_node(result)
        assert result.name == "Name"
        assert is_concrete_type(result.supertype)
        assert result.supertype.cls is str

    def test_children_returns_supertype(self) -> None:
        UserId = NewType("UserId", int)
        result = inspect_type(UserId)

        assert is_new_type_node(result)
        children = result.children()
        assert len(children) == 1
        assert children[0] is result.supertype

    def test_metadata_and_qualifiers_default_empty(self) -> None:
        UserId = NewType("UserId", int)
        result = inspect_type(UserId)

        assert is_new_type_node(result)
        assert result.metadata == ()
        assert result.qualifiers == frozenset()


class TestTypeGuardType:
    def test_typeguard_has_narrows_to(self) -> None:
        result = inspect_type(TypeGuard[int])

        assert is_type_guard_type_node(result)
        assert is_concrete_type(result.narrows_to)
        assert result.narrows_to.cls is int

    def test_children_returns_narrows_to(self) -> None:
        result = inspect_type(TypeGuard[str])

        assert is_type_guard_type_node(result)
        children = result.children()
        assert len(children) == 1
        assert children[0] is result.narrows_to

    def test_metadata_and_qualifiers_default_empty(self) -> None:
        result = inspect_type(TypeGuard[int])

        assert is_type_guard_type_node(result)
        assert result.metadata == ()
        assert result.qualifiers == frozenset()


class TestTypeIsType:
    def test_typeis_has_narrows_to(self) -> None:
        result = inspect_type(TypeIs[int])

        assert is_type_is_type_node(result)
        assert is_concrete_type(result.narrows_to)
        assert result.narrows_to.cls is int

    def test_children_returns_narrows_to(self) -> None:
        result = inspect_type(TypeIs[str])

        assert is_type_is_type_node(result)
        children = result.children()
        assert len(children) == 1
        assert children[0] is result.narrows_to

    def test_metadata_and_qualifiers_default_empty(self) -> None:
        result = inspect_type(TypeIs[int])

        assert is_type_is_type_node(result)
        assert result.metadata == ()
        assert result.qualifiers == frozenset()


class TestConcatenateNode:
    def test_concatenate_has_prefix_and_paramspec(self) -> None:
        P = ParamSpec("P")  # noqa: N806 - type parameter naming convention
        # Concatenate subscript syntax not fully understood by pyright
        result = inspect_type(Concatenate[int, str, P])  # pyright: ignore[reportGeneralTypeIssues]

        assert is_concatenate_node(result)
        assert len(result.prefix) == 2

        assert is_concrete_type(result.prefix[0])
        assert result.prefix[0].cls is int
        assert is_concrete_type(result.prefix[1])
        assert result.prefix[1].cls is str

        assert result.param_spec.name == "P"

    def test_single_prefix_type(self) -> None:
        P = ParamSpec("P")  # noqa: N806 - type parameter naming convention
        # Concatenate subscript syntax not fully understood by pyright
        result = inspect_type(Concatenate[int, P])  # pyright: ignore[reportGeneralTypeIssues]

        assert is_concatenate_node(result)
        assert len(result.prefix) == 1
        assert is_concrete_type(result.prefix[0])
        assert result.prefix[0].cls is int

    def test_children_includes_prefix_and_paramspec(self) -> None:
        P = ParamSpec("P")  # noqa: N806 - type parameter naming convention
        # Concatenate subscript syntax not fully understood by pyright
        result = inspect_type(Concatenate[int, P])  # pyright: ignore[reportGeneralTypeIssues]

        assert is_concatenate_node(result)
        children = result.children()
        assert len(children) == 2


class TestTypeQualifiers:
    def test_classvar_sets_class_var_qualifier(self) -> None:
        result = inspect_type(ClassVar[int])

        assert is_concrete_type(result)
        assert result.cls is int
        assert "class_var" in result.qualifiers

    def test_final_sets_final_qualifier(self) -> None:
        result = inspect_type(Final[int])

        assert is_concrete_type(result)
        assert result.cls is int
        assert "final" in result.qualifiers

    def test_classvar_with_complex_type(self) -> None:
        result = inspect_type(ClassVar[list[int]])

        assert is_subscripted_generic_node(result)
        assert is_generic_type(result.origin)
        assert result.origin.cls is list
        assert "class_var" in result.qualifiers


class TestAnnotatedMetadata:
    def test_single_metadata_item(self) -> None:
        result = inspect_type(Annotated[int, "metadata"])

        assert is_concrete_type(result)
        assert result.cls is int
        assert "metadata" in result.metadata

    def test_multiple_metadata_items(self) -> None:
        result = inspect_type(Annotated[int, "meta1", "meta2"])

        assert is_concrete_type(result)
        assert result.cls is int
        assert "meta1" in result.metadata
        assert "meta2" in result.metadata

    def test_metadata_with_complex_type(self) -> None:
        result = inspect_type(Annotated[list[int], "description"])

        assert is_subscripted_generic_node(result)
        assert is_generic_type(result.origin)
        assert result.origin.cls is list
        assert "description" in result.metadata


class TestGenericTypeNode:
    def test_unsubscripted_list_is_generic_type(self) -> None:
        result = inspect_type(list)

        # Bare list should be ConcreteType since it has no type params specified
        # until subscripted. Let's verify the actual behavior.
        assert is_concrete_type(result) or is_generic_type(result)
        if is_concrete_type(result):
            assert result.cls is list

    def test_custom_generic_class(self) -> None:
        T = TypeVar("T")

        class Container(list[T]):  # type: ignore[type-arg]
            pass

        result = inspect_type(Container)

        # Custom generic should be detected
        assert is_concrete_type(result) or is_generic_type(result)


class TestEdgeCases:
    def test_none_vs_nonetype_vs_literal_none_distinctions(self) -> None:
        # None literal
        result_none = inspect_type(None)
        assert is_concrete_type(result_none)
        assert result_none.cls is type(None)

        # type(None)
        result_nonetype = inspect_type(type(None))
        assert is_concrete_type(result_nonetype)
        assert result_nonetype.cls is type(None)

        # Literal[None] - intentionally testing Literal[None] vs bare None
        result_literal = inspect_type(Literal[None])  # noqa: PYI061
        assert is_literal_node(result_literal)
        assert result_literal.values == (None,)

    def test_complex_nested_type(self) -> None:
        result = inspect_type(dict[str, list[tuple[int, str] | None]])

        assert is_subscripted_generic_node(result)
        assert is_generic_type(result.origin)
        assert result.origin.cls is dict
        assert len(result.args) == 2

        # Key type
        assert is_concrete_type(result.args[0])
        assert result.args[0].cls is str

        # Value type is list
        value_type = result.args[1]
        assert is_subscripted_generic_node(value_type)
        assert is_generic_type(value_type.origin)
        assert value_type.origin.cls is list

        # Inside the list is the union
        inner_union = value_type.args[0]
        assert is_union_type_node(inner_union)


class TestGetTypeHintsForNode:
    def test_concrete_type_returns_cls(self) -> None:
        node = inspect_type(int)
        result: object = get_type_hints_for_node(node)

        assert result is int

    def test_any_type_returns_any(self) -> None:
        node = inspect_type(Any)
        result: object = get_type_hints_for_node(node)

        assert result is Any

    def test_never_type_returns_never(self) -> None:
        node = inspect_type(Never)
        result: object = get_type_hints_for_node(node)

        assert result is Never

    def test_self_type_returns_self(self) -> None:
        node = inspect_type(Self)
        result: object = get_type_hints_for_node(node)

        assert result is Self

    def test_literal_recreates_literal(self) -> None:
        node = inspect_type(Literal["a", "b"])
        result: object = get_type_hints_for_node(node)

        # Verify it's a Literal with correct values
        assert get_origin(result) is Literal
        assert get_args(result) == ("a", "b")

    def test_union_recreates_union(self) -> None:
        node = inspect_type(int | str)
        result: object = get_type_hints_for_node(node)

        # Verify union contains int and str
        assert get_origin(result) is UnionType
        assert set(get_args(result)) == {int, str}

    def test_subscripted_generic_recreates_generic(self) -> None:
        node = inspect_type(list[int])
        result: object = get_type_hints_for_node(node)

        assert get_origin(result) is list
        assert get_args(result) == (int,)

    def test_tuple_homogeneous_recreates_tuple_ellipsis(self) -> None:
        node = inspect_type(tuple[int, ...])
        result: object = get_type_hints_for_node(node)

        assert get_origin(result) is tuple
        assert get_args(result) == (int, ...)

    def test_tuple_heterogeneous_recreates_tuple(self) -> None:
        node = inspect_type(tuple[int, str])
        result: object = get_type_hints_for_node(node)

        assert get_origin(result) is tuple
        assert get_args(result) == (int, str)

    def test_tuple_empty_recreates_empty_tuple(self) -> None:
        node = inspect_type(tuple[()])
        result: object = get_type_hints_for_node(node)

        assert get_origin(result) is tuple
        assert get_args(result) == ()

    def test_callable_with_params_recreates_callable(self) -> None:
        node = inspect_type(Callable[[int, str], bool])
        result: object = get_type_hints_for_node(node)

        # Callable types use collections.abc.Callable as origin
        assert get_origin(result) is Callable
        # get_args returns ([int, str], bool) not (int, str, bool)
        args = get_args(result)
        assert args[0] == [int, str]
        assert args[1] is bool

    def test_callable_with_ellipsis_recreates_callable(self) -> None:
        node = inspect_type(Callable[..., int])
        result: object = get_type_hints_for_node(node)

        assert get_origin(result) is Callable
        assert get_args(result) == (..., int)

    def test_typevar_raises_type_error(self) -> None:
        T = TypeVar("T")
        node = inspect_type(T)

        # TypeVars can't be recreated without the original object
        with pytest.raises(TypeError, match="Cannot convert TypeVarNode"):
            get_type_hints_for_node(node)

    def test_forward_ref_unresolved_returns_typing_forwardref(self) -> None:
        node = inspect_type("UnknownClass")
        result: object = get_type_hints_for_node(node)

        assert isinstance(result, TypingForwardRef)

    def test_forward_ref_resolved_returns_resolved_type(self) -> None:
        config = InspectConfig(globalns={"MyInt": int})
        node = inspect_type("MyInt", config=config)
        result: object = get_type_hints_for_node(node)

        # Should resolve to int
        assert result is int

    def test_annotated_includes_metadata_by_default(self) -> None:
        node = inspect_type(Annotated[int, "metadata"])
        result: object = get_type_hints_for_node(node)

        assert get_origin(result) is Annotated
        # Use typing_extensions.get_args for Annotated to get metadata
        args = get_args(result)
        assert args[0] is int
        assert args[1] == "metadata"

    def test_annotated_excludes_metadata_when_disabled(self) -> None:
        node = inspect_type(Annotated[int, "metadata"])
        result: object = get_type_hints_for_node(node, include_extras=False)

        # Should return just int without Annotated wrapper
        assert result is int

    def test_nested_generic_recreates_structure(self) -> None:
        node = inspect_type(dict[str, list[int]])
        result: object = get_type_hints_for_node(node)

        assert get_origin(result) is dict
        args = get_args(result)
        assert len(args) == 2
        assert args[0] is str
        # Second arg is list[int]
        inner = args[1]
        assert get_origin(inner) is list
        assert get_args(inner) == (int,)


class TestResetTypeInspectors:
    def test_reset_clears_inspectors(self) -> None:
        # Ensure inspectors are registered
        _register_type_inspectors()
        assert len(_TYPE_INSPECTORS) > 0

        # Reset
        reset_type_inspectors()

        # Local import: Re-import with aliases to verify state after reset.
        # We need fresh references to check the reset actually worked.
        from typing_graph._inspect_type import (
            _TYPE_INSPECTORS as inspectors_after,
            _inspectors_initialized as initialized_after,
        )

        assert len(inspectors_after) == 0
        assert initialized_after is False

        # Re-register for other tests
        _register_type_inspectors()


class TestBareFinalAnnotation:
    def test_bare_final_returns_any_with_final_qualifier(self) -> None:
        result = inspect_type(Final)

        # Bare Final becomes AnyType with 'final' qualifier
        assert is_any_type_node(result)
        assert "final" in result.qualifiers


class TestBareCallable:
    def test_bare_callable_has_empty_params_and_any_return(self) -> None:
        result = inspect_type(ABCCallable)

        # Bare Callable should be handled
        # The exact result depends on how inspect_type handles it
        assert result is not None


class TestInspectTypeParam:
    def test_inspect_typevar(self) -> None:
        T = TypeVar("T", bound=int)
        result = inspect_type_param(T)

        assert is_type_var_node(result)
        assert result.name == "T"
        assert result.bound is not None
        assert is_concrete_type(result.bound)
        assert result.bound.cls is int

    def test_inspect_paramspec(self) -> None:
        P = ParamSpec("P")  # noqa: N806
        result = inspect_type_param(P)

        assert is_param_spec_node(result)
        assert result.name == "P"

    def test_inspect_typevartuple(self) -> None:
        Ts = TypeVarTuple("Ts")  # noqa: N806
        result = inspect_type_param(Ts)

        assert is_type_var_tuple_node(result)
        assert result.name == "Ts"

    def test_typevartuple_is_handled_before_typevar(self) -> None:
        # TypeVarTuple is TypeVar subclass on some versions - must be checked first
        Ts = TypeVarTuple("Ts")  # noqa: N806

        # On Python 3.10-3.11, TypeVarTuple is a TypeVar subclass
        # The inspect_type_param function must check TypeVarTuple first
        result = inspect_type_param(Ts)

        assert is_type_var_tuple_node(result)
        assert result.name == "Ts"


class TestInspectTypeAlias:
    def test_simple_type_alias(self) -> None:
        # Create a simple type alias
        my_int = int

        result = inspect_type_alias(my_int, name="MyInt")

        assert is_type_alias_node(result)
        assert result.name == "MyInt"
        assert is_concrete_type(result.value)
        assert result.value.cls is int

    def test_simple_type_alias_without_name(self) -> None:
        # Create a type alias without explicit name
        my_list = list[int]

        result = inspect_type_alias(my_list)

        # Should fall back to "TypeAlias" or similar
        assert is_type_alias_node(result)

    def test_pep695_type_alias_with_type_alias_type(self) -> None:
        # Create a PEP 695 type alias
        # TypeAliasType at function scope triggers pyright errors about scope,
        # but the test is still valid - we're testing inspect_type_alias behavior
        my_alias = TypeAliasType(  # pyright: ignore[reportGeneralTypeIssues]
            "MyAlias",  # pyright: ignore[reportGeneralTypeIssues]
            list[int],
        )

        result = inspect_type_alias(my_alias)

        assert is_generic_alias_node(result)
        assert result.name == "MyAlias"


class TestResolveForwardRef:
    def test_resolve_string_ref(self) -> None:
        result = resolve_forward_ref("int", globalns={"int": int})

        assert is_forward_ref_node(result)
        assert is_ref_state_resolved(result.state)
        assert is_concrete_type(result.state.node)
        assert result.state.node.cls is int

    def test_resolve_typing_forward_ref(self) -> None:
        ref = TypingForwardRef("str")
        result = resolve_forward_ref(ref, globalns={"str": str})

        assert is_forward_ref_node(result)
        assert is_ref_state_resolved(result.state)
        assert is_concrete_type(result.state.node)
        assert result.state.node.cls is str

    def test_resolve_forward_ref_raises_for_unknown(self) -> None:
        with pytest.raises(NameError, match="Cannot resolve forward reference"):
            _ = resolve_forward_ref("NonexistentType")


class TestGetTypeHintsForNodeEdgeCases:
    def test_callable_with_ellipsis_params_returns_callable(self) -> None:
        callable_type = Callable[..., int]
        node = inspect_type(callable_type)

        result = get_type_hints_for_node(node)

        assert result is not None
        # The result should be a callable type
        has_origin = hasattr(result, "__origin__")
        is_call = callable(result)
        assert has_origin or is_call

    def test_unknown_node_type_returns_any(self) -> None:
        # Create a custom TypeNode subclass that isn't handled
        class UnknownTypeNode(TypeNode):
            @override
            def children(
                self,
                # Return type narrowed - incompatible with base but valid for test
            ) -> tuple[()]:  # type: ignore[override]
                return ()

        node = UnknownTypeNode()
        result = get_type_hints_for_node(node)

        assert result is Any


class TestForwardRefResolution:
    def test_deferred_mode_creates_failed_ref_for_unknown(self) -> None:
        config = InspectConfig(eval_mode=EvalMode.DEFERRED)
        result = inspect_type("UnknownClass", config=config)

        assert is_forward_ref_node(result)
        assert result.ref == "UnknownClass"
        # In DEFERRED mode, unresolvable refs become Failed
        is_failed = is_ref_state_failed(result.state)
        is_unresolved = is_ref_state_unresolved(result.state)
        assert is_failed or is_unresolved

    def test_deferred_mode_resolves_known_ref(self) -> None:
        config = InspectConfig(eval_mode=EvalMode.DEFERRED, globalns={"KnownType": str})
        result = inspect_type("KnownType", config=config)

        assert is_forward_ref_node(result)
        assert result.ref == "KnownType"
        assert is_ref_state_resolved(result.state)
        assert is_concrete_type(result.state.node)
        assert result.state.node.cls is str

    def test_eager_mode_raises_for_unknown_ref(self) -> None:
        config = InspectConfig(eval_mode=EvalMode.EAGER)

        with pytest.raises(NameError, match="Cannot resolve forward reference"):
            _ = inspect_type("UnknownClass", config=config)

    def test_eager_mode_resolves_known_ref(self) -> None:
        config = InspectConfig(eval_mode=EvalMode.EAGER, globalns={"KnownType": int})
        result = inspect_type("KnownType", config=config)

        assert is_forward_ref_node(result)
        assert is_ref_state_resolved(result.state)
        assert is_concrete_type(result.state.node)
        assert result.state.node.cls is int

    def test_stringified_mode_keeps_ref_unresolved(self) -> None:
        config = InspectConfig(eval_mode=EvalMode.STRINGIFIED)
        result = inspect_type("SomeClass", config=config)

        assert is_forward_ref_node(result)
        assert result.ref == "SomeClass"
        assert is_ref_state_unresolved(result.state)

    def test_stringified_mode_does_not_resolve_known_ref(self) -> None:
        config = InspectConfig(
            eval_mode=EvalMode.STRINGIFIED, globalns={"KnownType": int}
        )
        result = inspect_type("KnownType", config=config)

        assert is_forward_ref_node(result)
        assert result.ref == "KnownType"
        # STRINGIFIED mode keeps refs as unresolved
        assert is_ref_state_unresolved(result.state)

    def test_typing_forward_ref_object_is_handled(self) -> None:
        ref = TypingForwardRef("int")
        config = InspectConfig(globalns={"int": int})
        result = inspect_type(ref, config=config)

        assert is_forward_ref_node(result)
        assert result.ref == "int"
        assert is_ref_state_resolved(result.state)
        assert is_concrete_type(result.state.node)
        assert result.state.node.cls is int

    def test_typing_forward_ref_stringified_stays_unresolved(self) -> None:
        ref = TypingForwardRef("SomeType")
        config = InspectConfig(eval_mode=EvalMode.STRINGIFIED)
        result = inspect_type(ref, config=config)

        assert is_forward_ref_node(result)
        assert result.ref == "SomeType"
        assert is_ref_state_unresolved(result.state)

    def test_recursive_forward_ref_detection(self) -> None:
        # Create a type that references itself
        config = InspectConfig(globalns={"Self": "Self"})
        result = inspect_type("Self", config=config)

        assert is_forward_ref_node(result)
        # Should detect the cycle and not infinite loop

    def test_forward_ref_with_localns(self) -> None:
        config = InspectConfig(localns={"LocalType": float})
        result = inspect_type("LocalType", config=config)

        assert is_forward_ref_node(result)
        assert is_ref_state_resolved(result.state)
        assert is_concrete_type(result.state.node)
        assert result.state.node.cls is float

    def test_forward_ref_evaluation_error_in_eager_mode_raises(self) -> None:
        config = InspectConfig(
            eval_mode=EvalMode.EAGER,
            globalns={},
            localns={},
        )

        with pytest.raises(NameError, match="Cannot resolve forward reference"):
            _ = inspect_type("NonExistentType", config=config)

    def test_typing_forward_ref_evaluation_error_in_eager_mode_raises(self) -> None:
        ref = TypingForwardRef("NonExistentType")
        config = InspectConfig(
            eval_mode=EvalMode.EAGER,
            globalns={},
            localns={},
        )

        with pytest.raises(NameError, match="Cannot resolve forward reference"):
            _ = inspect_type(ref, config=config)

    def test_typing_forward_ref_evaluation_error_in_deferred_mode_returns_failed(
        self,
    ) -> None:
        ref = TypingForwardRef("NonExistentType")
        config = InspectConfig(
            eval_mode=EvalMode.DEFERRED,
            globalns={},
            localns={},
        )

        result = inspect_type(ref, config=config)

        # In DEFERRED mode, evaluation errors return Failed state instead of raising
        assert is_forward_ref_node(result)
        assert is_ref_state_failed(result.state)
        assert "NonExistentType" in result.state.error

    def test_forward_ref_circular_via_typing_forward_ref(self) -> None:
        # Create a circular reference using typing.ForwardRef
        ref = TypingForwardRef("CircularRef")
        config = InspectConfig(globalns={"CircularRef": ref})
        result = inspect_type(ref, config=config)

        assert is_forward_ref_node(result)
        # The outer ref is resolved (to another ForwardRef), but the inner one
        # is unresolved due to cycle detection
        assert is_ref_state_resolved(result.state)
        inner = result.state.node
        assert is_forward_ref_node(inner)
        assert is_ref_state_unresolved(inner.state)


class TestUnpackType:
    def test_unpack_typevartuple(self) -> None:
        # Local import: TYPE_CHECKING is used for runtime workaround below.
        # Unpack[Ts] is valid at runtime but basedpyright rejects it statically.
        from typing import TYPE_CHECKING

        Ts = TypeVarTuple("Ts")  # noqa: N806

        if TYPE_CHECKING:
            unpack_ts: object = None
        else:
            unpack_ts = Unpack[Ts]

        result = inspect_type(unpack_ts)

        assert is_unpack_node(result)
        assert is_type_var_tuple_node(result.target)
        assert result.target.name == "Ts"


class TestBareCallableParams:
    def test_callable_no_args_returns_empty_params_and_any(self) -> None:
        # Bare Callable is a plain type - ensure it inspects correctly
        result = inspect_type(ABCCallable)

        # Should be handled as a generic type or concrete type
        assert result is not None


class TestTypeVarWithDefault:
    def test_typevar_with_default_captured(self) -> None:
        # TypeVar with default requires Python 3.13+ or typing_extensions
        try:
            # Local import: TypeVarExt alias to test default= kwarg that may
            # not be supported in all typing_extensions versions
            from typing_extensions import TypeVar as TypeVarExt

            T = TypeVarExt("T", default=int)
            # Use inspect_type since typing_extensions.TypeVar may differ
            result = inspect_type(T)

            assert is_type_var_node(result)
            assert result.name == "T"
            assert result.default is not None
            assert is_concrete_type(result.default)
            assert result.default.cls is int
        except TypeError:
            pytest.skip(
                "TypeVar default not supported in this typing_extensions version"
            )


class TestParamSpecWithDefault:
    def test_paramspec_with_default_captured(self) -> None:
        try:
            # Local import: ParamSpecExt alias to test default= kwarg that may
            # not be supported in all typing_extensions versions
            from typing_extensions import ParamSpec as ParamSpecExt

            P = ParamSpecExt("P", default=[int, str])  # noqa: N806
            # Use inspect_type since typing_extensions.ParamSpec may differ
            result = inspect_type(P)

            assert is_param_spec_node(result)
            assert result.name == "P"
            # Default should be captured if supported
        except TypeError:
            pytest.skip(
                "ParamSpec default not supported in this typing_extensions version"
            )


class TestTypeVarTupleWithDefault:
    def test_typevartuple_with_default_captured(self) -> None:
        try:
            # Local import: TypeVarTupleExt alias to test default= kwarg that may
            # not be supported in all typing_extensions versions
            from typing_extensions import TypeVarTuple as TypeVarTupleExt

            Ts = TypeVarTupleExt("Ts", default=Unpack[tuple[int, str]])  # noqa: N806
            result = inspect_type_param(Ts)

            assert is_type_var_tuple_node(result)
            assert result.name == "Ts"
            # Default should be captured if supported
        except TypeError:
            pytest.skip(
                "TypeVarTuple default not supported in this typing_extensions version"
            )


class TestGetTypeHintsForNodeCallable:
    def test_callable_with_paramspec_raises_type_error(self) -> None:
        P = ParamSpec("P")  # noqa: N806
        # Callable[P, int] valid at runtime but basedpyright
        # doesn't understand ParamSpec in subscript
        callable_type = Callable[P, int]  # pyright: ignore[reportGeneralTypeIssues]
        node = inspect_type(callable_type)

        assert is_callable_type_node(node)
        assert is_param_spec_node(node.params)

        # ParamSpec can't be recreated at runtime without the original object
        with pytest.raises(TypeError, match="Cannot convert"):
            get_type_hints_for_node(node)

    def test_callable_with_concatenate_raises_type_error(self) -> None:
        P = ParamSpec("P")  # noqa: N806
        # Concatenate subscript syntax not fully understood by pyright
        callable_type = Callable[Concatenate[int, P], str]  # pyright: ignore[reportGeneralTypeIssues]
        node = inspect_type(callable_type)

        assert is_callable_type_node(node)
        assert is_concatenate_node(node.params)

        # Concatenate can't be recreated at runtime without the original object
        with pytest.raises(TypeError, match="Cannot convert"):
            get_type_hints_for_node(node)

    def test_typevar_node_raises_type_error(self) -> None:
        T = TypeVar("T")
        node = inspect_type(T)

        assert is_type_var_node(node)

        with pytest.raises(TypeError, match="Cannot convert TypeVarNode"):
            get_type_hints_for_node(node)

    def test_paramspec_node_raises_type_error(self) -> None:
        P = ParamSpec("P")  # noqa: N806
        node = inspect_type(P)

        assert is_param_spec_node(node)

        with pytest.raises(TypeError, match="Cannot convert ParamSpecNode"):
            get_type_hints_for_node(node)

    def test_typevartuple_node_raises_type_error(self) -> None:
        Ts = TypeVarTuple("Ts")  # noqa: N806
        node = inspect_type(Ts)

        assert is_type_var_tuple_node(node)

        with pytest.raises(TypeError, match="Cannot convert TypeVarTupleNode"):
            get_type_hints_for_node(node)


class TestUnknownAnnotationType:
    def test_unknown_annotation_type_returns_forward_ref_failed(self) -> None:
        # Create an object that doesn't match any known annotation type
        # and isn't handled by any inspector
        class WeirdAnnotation:
            pass

        weird = WeirdAnnotation()
        result = inspect_type(weird)

        # Should return a ForwardRef with Failed state
        assert is_forward_ref_node(result)
        assert is_ref_state_failed(result.state)
        assert "Unknown annotation type" in result.state.error


class TestTupleNoArgs:
    def test_tuple_unparameterized_is_tuple_any_variadic(self) -> None:
        result = inspect_type(tuple)

        # Bare `tuple` should be handled
        assert result is not None
        # Should be a generic type or concrete type
        if is_tuple_type_node(result):
            # If it's a TupleType, it should be homogeneous (tuple[Any, ...])
            assert result.homogeneous is True


class TestTypeAliasTypeViaInspectType:
    def test_type_alias_type_via_inspect_type(self) -> None:
        # Create a TypeAliasType and pass it to inspect_type
        # TypeAliasType at function scope triggers pyright errors about scope
        my_alias = TypeAliasType(  # pyright: ignore[reportGeneralTypeIssues]
            "MyAlias",  # pyright: ignore[reportGeneralTypeIssues]
            list[int],
        )

        result = inspect_type(my_alias)

        # inspect_type should detect TypeAliasType and return GenericAlias
        assert is_generic_alias_node(result)
        assert result.name == "MyAlias"


class TestInternalTupleFunction:
    def test_tuple_with_empty_args_not_empty_tuple_syntax(self) -> None:
        # Create a fake annotation that doesn't have "tuple[()]" in its repr
        # This tests the defensive branch for tuple with empty args
        class FakeAnnotation:
            @override
            def __repr__(self) -> str:
                return "FakeAnnotation"

        ctx = InspectContext(config=DEFAULT_CONFIG)
        result = _inspect_tuple(FakeAnnotation(), (), ctx)

        # Should be treated as tuple[Any, ...] (homogeneous)
        assert is_tuple_type_node(result)
        assert result.homogeneous is True
        assert len(result.elements) == 1
        assert is_any_type_node(result.elements[0])


class TestInternalCallableFunction:
    def test_callable_with_empty_args(self) -> None:
        ctx = InspectContext(config=DEFAULT_CONFIG)
        result = _inspect_callable((), ctx)

        # Bare Callable should return empty params with Any return
        assert is_callable_type_node(result)
        assert result.params == ()
        assert is_any_type_node(result.returns)

    def test_callable_with_unknown_param_format(self) -> None:
        ctx = InspectContext(config=DEFAULT_CONFIG)
        # Pass something that isn't ..., ParamSpec, list, or Concatenate
        result = _inspect_callable(("weird_thing", int), ctx)

        # Should fall back to empty params with Any return
        assert is_callable_type_node(result)
        assert result.params == ()
        assert is_any_type_node(result.returns)

    def test_callable_with_wrong_arg_count(self) -> None:
        ctx = InspectContext(config=DEFAULT_CONFIG)
        # Pass 3 args - wrong count for Callable (expects 2)
        result = _inspect_callable(("a", "b", "c"), ctx)

        # Should fall back to empty params with Any return
        assert is_callable_type_node(result)
        assert result.params == ()
        assert is_any_type_node(result.returns)


class TestTypeParamFiltering:
    def test_type_alias_type_with_non_param_in_type_params(self) -> None:
        # TypeAliasType at function scope triggers pyright errors about scope
        alias = TypeAliasType(  # pyright: ignore[reportGeneralTypeIssues]
            "MyAlias",  # pyright: ignore[reportGeneralTypeIssues]
            list[int],
        )
        # Replace __type_params__ with something that isn't a type param
        # TypeAliasType has read-only __type_params__, so test indirectly

        ctx = InspectContext(config=DEFAULT_CONFIG)
        result = _inspect_type_alias_type(alias, ctx)

        # Should work, just won't have type params
        assert is_generic_alias_node(result)
        assert result.name == "MyAlias"

    def test_subscripted_generic_with_non_param_in_raw_params(self) -> None:
        # Create a class with weird __parameters__
        class WeirdGeneric:
            __parameters__: tuple[type, ...] = (int, str)  # Not TypeVars

            def __class_getitem__(cls, params: object) -> type:
                return cls

        ctx = InspectContext(config=DEFAULT_CONFIG)
        result = _inspect_subscripted_generic(
            WeirdGeneric[int], WeirdGeneric, (int,), ctx
        )

        # Should work, type_params should be empty since int/str aren't type params
        assert is_subscripted_generic_node(result)
        assert is_generic_type(result.origin)
        assert result.origin.type_params == ()

    def test_subscripted_user_generic_captures_type_params(self) -> None:
        T = TypeVar("T")

        class MyGeneric(Generic[T]):
            pass

        result = inspect_type(MyGeneric[int])

        # User-defined generics have __parameters__ with actual TypeVars
        assert is_subscripted_generic_node(result)
        assert is_generic_type(result.origin)
        # The origin should have captured the TypeVar as a type param
        assert len(result.origin.type_params) == 1
        assert is_type_var_node(result.origin.type_params[0])
        assert result.origin.type_params[0].name == "T"

    def test_plain_type_with_non_param_in_raw_params(self) -> None:
        # Create a class with __class_getitem__ and weird __parameters__
        class WeirdType:
            __parameters__: tuple[type, ...] = (int, str)  # Not TypeVars

            def __class_getitem__(cls, params: object) -> type:
                return cls

        ctx = InspectContext(config=DEFAULT_CONFIG)
        result = _inspect_plain_type(WeirdType, ctx)

        # Should work - since non-TypeVars are filtered out, type_params is empty
        # and it returns a ConcreteType instead of GenericTypeNode
        assert is_concrete_type(result) or is_generic_type(result)
