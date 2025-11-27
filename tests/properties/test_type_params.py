# pyright: reportAny=false, reportExplicitAny=false

from typing import ParamSpec, TypeVar
from typing_extensions import TypeVarTuple

from hypothesis import HealthCheck, example, given, settings

from typing_graph import Variance, clear_cache, inspect_type
from typing_graph._node import (
    is_concrete_type,
    is_param_spec_node,
    is_type_var_node,
    is_type_var_tuple_node,
    is_unpack_node,
)

from .strategies import (
    paramspec_instances,
    typevar_instances,
    typevartuple_instances,
    unpack_types,
)

# =============================================================================
# TypeVar Property Tests
# =============================================================================


@given(typevar_instances())
@settings(suppress_health_check=[HealthCheck.too_slow], deadline=None)
def test_typevar_is_correctly_recognized(tv: TypeVar) -> None:
    clear_cache()
    node = inspect_type(tv)

    assert is_type_var_node(node), f"Expected TypeVarNode, got {type(node).__name__}"
    assert node.name == tv.__name__


@given(typevar_instances())
@settings(deadline=None)
def test_typevar_variance_correctly_captured(tv: TypeVar) -> None:
    clear_cache()
    node = inspect_type(tv)

    assert is_type_var_node(node)

    # Verify variance mapping matches TypeVar's variance
    if tv.__covariant__:
        assert node.variance == Variance.COVARIANT
    elif tv.__contravariant__:
        assert node.variance == Variance.CONTRAVARIANT
    else:
        assert node.variance == Variance.INVARIANT


@given(typevar_instances())
@settings(deadline=None)
def test_typevar_bound_preserved(tv: TypeVar) -> None:
    clear_cache()
    node = inspect_type(tv)

    assert is_type_var_node(node)

    # Verify bound is correctly captured
    if tv.__bound__ is not None:
        assert node.bound is not None
        assert is_concrete_type(node.bound)
        assert node.bound.cls is tv.__bound__
    else:
        assert node.bound is None


@given(typevar_instances())
@settings(deadline=None)
def test_typevar_constraints_preserved(tv: TypeVar) -> None:
    clear_cache()
    node = inspect_type(tv)

    assert is_type_var_node(node)

    # Verify constraints are correctly captured
    if tv.__constraints__:
        assert len(node.constraints) == len(tv.__constraints__)
        for i, constraint_node in enumerate(node.constraints):
            assert is_concrete_type(constraint_node)
            assert constraint_node.cls is tv.__constraints__[i]
    else:
        assert node.constraints == ()


@given(typevar_instances())
@settings(deadline=None)
def test_typevar_metadata_and_qualifiers_empty(tv: TypeVar) -> None:
    clear_cache()
    node = inspect_type(tv)

    assert is_type_var_node(node)
    assert node.metadata == ()
    assert node.qualifiers == frozenset()


@given(typevar_instances())
@settings(deadline=None)
def test_typevar_children_match_bound_and_constraints(tv: TypeVar) -> None:
    clear_cache()
    node = inspect_type(tv)

    assert is_type_var_node(node)

    children = node.children()
    expected_count = 0

    if tv.__bound__ is not None:
        expected_count += 1

    if tv.__constraints__:
        expected_count += len(tv.__constraints__)

    assert len(children) == expected_count


# Explicit examples for common TypeVar patterns
@example(TypeVar("T"))
@example(TypeVar("T_co", covariant=True))
@example(TypeVar("T_contra", contravariant=True))
@example(TypeVar("T", bound=int))
@example(TypeVar("T", int, str))
@given(typevar_instances())
@settings(deadline=None)
def test_typevar_inspection_is_idempotent(tv: TypeVar) -> None:
    clear_cache()
    node1 = inspect_type(tv)
    node2 = inspect_type(tv)

    # Cache should return same instance
    assert node1 is node2


# =============================================================================
# ParamSpec Property Tests
# =============================================================================


@given(paramspec_instances())
@settings(deadline=None)
def test_paramspec_is_correctly_recognized(ps: ParamSpec) -> None:
    clear_cache()
    node = inspect_type(ps)

    assert is_param_spec_node(node), (
        f"Expected ParamSpecNode, got {type(node).__name__}"
    )
    assert node.name == ps.__name__


@given(paramspec_instances())
@settings(deadline=None)
def test_paramspec_metadata_and_qualifiers_empty(ps: ParamSpec) -> None:
    clear_cache()
    node = inspect_type(ps)

    assert is_param_spec_node(node)
    assert node.metadata == ()
    assert node.qualifiers == frozenset()


@given(paramspec_instances())
@settings(deadline=None)
def test_paramspec_children_empty(ps: ParamSpec) -> None:
    clear_cache()
    node = inspect_type(ps)

    assert is_param_spec_node(node)
    assert node.children() == ()


# Explicit examples for ParamSpec
@example(ParamSpec("P"))
@given(paramspec_instances())
@settings(deadline=None)
def test_paramspec_inspection_is_idempotent(ps: ParamSpec) -> None:
    clear_cache()
    node1 = inspect_type(ps)
    node2 = inspect_type(ps)

    # Cache should return same instance
    assert node1 is node2


# =============================================================================
# TypeVarTuple Property Tests
# =============================================================================


@given(typevartuple_instances())
@settings(deadline=None)
def test_typevartuple_is_correctly_recognized(tvt: TypeVarTuple) -> None:
    clear_cache()
    node = inspect_type(tvt)

    assert is_type_var_tuple_node(node), (
        f"Expected TypeVarTupleNode, got {type(node).__name__}"
    )
    assert node.name == tvt.__name__


@given(typevartuple_instances())
@settings(deadline=None)
def test_typevartuple_metadata_and_qualifiers_empty(tvt: TypeVarTuple) -> None:
    clear_cache()
    node = inspect_type(tvt)

    assert is_type_var_tuple_node(node)
    assert node.metadata == ()
    assert node.qualifiers == frozenset()


@given(typevartuple_instances())
@settings(deadline=None)
def test_typevartuple_children_empty(tvt: TypeVarTuple) -> None:
    clear_cache()
    node = inspect_type(tvt)

    assert is_type_var_tuple_node(node)
    assert node.children() == ()


# Explicit examples for TypeVarTuple
@example(TypeVarTuple("Ts"))
@given(typevartuple_instances())
@settings(deadline=None)
def test_typevartuple_inspection_is_idempotent(tvt: TypeVarTuple) -> None:
    clear_cache()
    node1 = inspect_type(tvt)
    node2 = inspect_type(tvt)

    # Cache should return same instance
    assert node1 is node2


# =============================================================================
# Unpack Property Tests
# =============================================================================


@given(unpack_types())
@settings(deadline=None)
def test_unpack_is_correctly_recognized(unpack_type: object) -> None:
    clear_cache()
    node = inspect_type(unpack_type)

    assert is_unpack_node(node), f"Expected UnpackNode, got {type(node).__name__}"


@given(unpack_types())
@settings(deadline=None)
def test_unpack_target_is_typevartuple(unpack_type: object) -> None:
    clear_cache()
    node = inspect_type(unpack_type)

    assert is_unpack_node(node)
    assert is_type_var_tuple_node(node.target)


@given(unpack_types())
@settings(deadline=None)
def test_unpack_children_contains_target(unpack_type: object) -> None:
    clear_cache()
    node = inspect_type(unpack_type)

    assert is_unpack_node(node)
    children = node.children()
    assert len(children) == 1
    assert children[0] is node.target


@given(unpack_types())
@settings(deadline=None)
def test_unpack_metadata_and_qualifiers_empty(unpack_type: object) -> None:
    clear_cache()
    node = inspect_type(unpack_type)

    assert is_unpack_node(node)
    assert node.metadata == ()
    assert node.qualifiers == frozenset()


# =============================================================================
# TypeVar Property Tests - Additional Assertions
# =============================================================================


@given(typevar_instances())
@settings(deadline=None)
def test_typevar_infer_variance_is_boolean(tv: TypeVar) -> None:
    clear_cache()
    node = inspect_type(tv)

    assert is_type_var_node(node)
    assert isinstance(node.infer_variance, bool)
    # Standard TypeVar from typing module should have infer_variance=False
    # unless explicitly created with __infer_variance__=True
    if not getattr(tv, "__infer_variance__", False):
        assert node.infer_variance is False
