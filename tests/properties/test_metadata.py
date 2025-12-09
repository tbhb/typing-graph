# pyright: reportAny=false, reportExplicitAny=false, reportUnknownVariableType=false, reportUnknownMemberType=false

import operator
from typing import Annotated, Any, ClassVar, Final

from hypothesis import HealthCheck, example, given, settings, strategies as st

from typing_graph import inspect_type
from typing_graph._node import (
    is_concrete_node,
    is_subscripted_generic_node,
    is_tuple_node,
)

from .strategies import annotated_types, nested_annotated_types, primitive_types


def _make_annotated(base_type: Any, *metadata: object) -> Any:
    """Construct an Annotated type in a version-agnostic way.

    Python 3.14 removed direct access to Annotated.__class_getitem__, so we
    use operator.getitem which works across all Python versions.
    """
    # Annotated supports subscripting at runtime but pyright doesn't see it
    return operator.getitem(Annotated, (base_type, *metadata))  # pyright: ignore[reportCallIssue,reportArgumentType]


@given(
    inner_type=st.sampled_from([int, str, float, bool, bytes]),
    metadata=st.lists(
        st.one_of(
            st.text(min_size=1, max_size=20),
            st.integers(-100, 100),
        ),
        min_size=1,
        max_size=3,
    ),
)
@settings(deadline=None)
# Migrated from TestAnnotatedMetadata - single and multiple metadata
@example(inner_type=int, metadata=["metadata"])
@example(inner_type=int, metadata=["meta1", "meta2"])
@example(inner_type=str, metadata=["description"])
@example(inner_type=float, metadata=[42])
@example(inner_type=bool, metadata=["doc", 100])
def test_annotated_metadata_preserved(
    inner_type: type, metadata: list[str | int]
) -> None:
    ann = _make_annotated(inner_type, *metadata)
    node = inspect_type(ann)

    for item in metadata:
        assert item in node.metadata, (
            f"Missing metadata: {item!r}\n"
            f"  Expected: {metadata!r}\n"
            f"  Got: {node.metadata!r}"
        )


@given(annotated_types(primitive_types()))
@settings(
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
@example(Annotated[int, "single"])
@example(Annotated[str, "a", "b"])
@example(Annotated[float, 42, "text", True])
def test_annotated_metadata_count_matches(annotation: object) -> None:
    node = inspect_type(annotation)

    # The metadata tuple should have at least the items we added
    assert len(node.metadata) >= 1, (
        f"Expected at least 1 metadata item, got {node.metadata}"
    )


@given(nested_annotated_types(primitive_types()))
@settings(
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
@example(Annotated[Annotated[int, "inner"], "outer"])
@example(Annotated[Annotated[str, "a"], "b", "c"])
def test_nested_annotated_flattens_correctly(annotation: object) -> None:
    node = inspect_type(annotation)

    # Python flattens nested Annotated types - all metadata should be present
    # Annotated[Annotated[T, a], b] becomes Annotated[T, a, b]
    assert len(node.metadata) >= 2, (
        f"Expected at least 2 metadata items from nested Annotated, got {node.metadata}"
    )


@given(inner_type=primitive_types())
@settings(deadline=None)
# Migrated from TestTypeQualifiers
@example(inner_type=int)
@example(inner_type=str)
@example(inner_type=float)
@example(inner_type=bool)
@example(inner_type=bytes)
def test_classvar_qualifier_extracted(inner_type: type) -> None:
    ann = ClassVar[inner_type]
    node = inspect_type(ann)

    assert "class_var" in node.qualifiers, (
        f"ClassVar[{inner_type}] should have 'class_var' qualifier\n"
        f"  Got qualifiers: {node.qualifiers}"
    )


@given(inner_type=primitive_types())
@settings(deadline=None)
# Migrated from TestTypeQualifiers
@example(inner_type=int)
@example(inner_type=str)
@example(inner_type=float)
@example(inner_type=bool)
@example(inner_type=bytes)
def test_final_qualifier_extracted(inner_type: type) -> None:
    ann = Final[inner_type]
    node = inspect_type(ann)

    assert "final" in node.qualifiers, (
        f"Final[{inner_type}] should have 'final' qualifier\n"
        f"  Got qualifiers: {node.qualifiers}"
    )


@given(inner_type=primitive_types())
@settings(deadline=None)
@example(inner_type=int)
@example(inner_type=str)
def test_classvar_unwraps_to_inner_type(inner_type: type) -> None:
    ann = ClassVar[inner_type]
    node = inspect_type(ann)

    # ClassVar should unwrap to inner type with qualifier set
    assert is_concrete_node(node), f"Expected ConcreteNode, got {type(node)}"
    assert node.cls is inner_type, f"Expected inner type {inner_type}, got {node.cls}"
    # Qualifier should be preserved after unwrapping
    assert "class_var" in node.qualifiers, (
        f"Qualifier 'class_var' should be preserved after unwrapping "
        f"ClassVar[{inner_type}]"
    )


@given(inner_type=primitive_types())
@settings(deadline=None)
@example(inner_type=int)
@example(inner_type=str)
def test_final_unwraps_to_inner_type(inner_type: type) -> None:
    ann = Final[inner_type]
    node = inspect_type(ann)

    # Final should unwrap to inner type with qualifier set
    assert is_concrete_node(node), f"Expected ConcreteNode, got {type(node)}"
    assert node.cls is inner_type, f"Expected inner type {inner_type}, got {node.cls}"
    # Qualifier should be preserved after unwrapping
    assert "final" in node.qualifiers, (
        f"Qualifier 'final' should be preserved after unwrapping Final[{inner_type}]"
    )


@given(
    include_classvar=st.booleans(),
    include_final=st.booleans(),
)
@settings(deadline=None)
@example(include_classvar=True, include_final=True)
@example(include_classvar=True, include_final=False)
@example(include_classvar=False, include_final=True)
def test_qualifier_combinations(include_classvar: bool, include_final: bool) -> None:
    # Note: ClassVar and Final cannot be directly combined in standard Python,
    # but we can test them separately and verify qualifier isolation
    inner_type = int

    if include_classvar:
        classvar_node = inspect_type(ClassVar[inner_type])
        assert "class_var" in classvar_node.qualifiers
        assert "final" not in classvar_node.qualifiers

    if include_final:
        final_node = inspect_type(Final[inner_type])
        assert "final" in final_node.qualifiers
        assert "class_var" not in final_node.qualifiers


# Migrated from TestTypeQualifiers.test_classvar_with_complex_type
@given(
    inner_type=st.sampled_from([list[int], dict[str, int], set[str], tuple[int, ...]]),
)
@settings(deadline=None)
@example(inner_type=list[int])
@example(inner_type=dict[str, int])
@example(inner_type=set[str])
@example(inner_type=tuple[int, ...])
def test_classvar_with_complex_type(inner_type: object) -> None:
    ann = ClassVar[inner_type]
    node = inspect_type(ann)

    assert "class_var" in node.qualifiers, (
        f"ClassVar[{inner_type}] should have 'class_var' qualifier"
    )
    # For complex types, the node should be a SubscriptedGenericNode or TupleNode
    # (tuple[int, ...] produces TupleType, not SubscriptedGeneric)
    assert is_subscripted_generic_node(node) or is_tuple_node(node), (
        f"Expected SubscriptedGenericNode or TupleNode for ClassVar[{inner_type}], "
        f"got {type(node)}"
    )


# Migrated from TestAnnotatedMetadata.test_metadata_with_complex_type
@given(
    inner_type=st.sampled_from([list[int], dict[str, int], set[str], tuple[int, ...]]),
    metadata=st.text(min_size=1, max_size=20),
)
@settings(deadline=None)
@example(inner_type=list[int], metadata="description")
@example(inner_type=dict[str, int], metadata="doc")
@example(inner_type=tuple[int, ...], metadata="info")
def test_metadata_with_complex_type(inner_type: object, metadata: str) -> None:
    ann = _make_annotated(inner_type, metadata)
    node = inspect_type(ann)

    assert metadata in node.metadata, (
        f"Missing metadata for Annotated[{inner_type}, {metadata!r}]"
    )
    # For complex types, the node should be a SubscriptedGenericNode or TupleNode
    # (tuple[int, ...] produces TupleNode, not SubscriptedGenericNode)
    assert is_subscripted_generic_node(node) or is_tuple_node(node), (
        f"Expected SubscriptedGenericNode or TupleNode for "
        f"Annotated[{inner_type}, ...], got {type(node)}"
    )


def test_classvar_annotated_preserves_qualifier() -> None:
    # Kills mutation: qualifier merge | -> ^ at _inspect_type.py:665
    from typing_graph import cache_clear

    cache_clear()
    ann = ClassVar[_make_annotated(int, "meta")]
    node = inspect_type(ann)

    # ClassVar qualifier must be present (would fail with XOR if both have it)
    assert "class_var" in node.qualifiers, (
        f"ClassVar qualifier lost in ClassVar[Annotated[int, 'meta']]\n"
        f"  Got qualifiers: {node.qualifiers}"
    )
    # Metadata should also be preserved
    assert "meta" in node.metadata


def test_final_annotated_preserves_qualifier() -> None:
    from typing_graph import cache_clear

    cache_clear()
    ann = Final[_make_annotated(str, "description")]
    node = inspect_type(ann)

    # Final qualifier must be present
    assert "final" in node.qualifiers, (
        f"Final qualifier lost in Final[Annotated[str, 'description']]\n"
        f"  Got qualifiers: {node.qualifiers}"
    )
    # Metadata should also be preserved
    assert "description" in node.metadata


def test_annotated_classvar_preserves_qualifier() -> None:
    from typing_graph import cache_clear

    cache_clear()
    ann = _make_annotated(ClassVar[int], "meta")
    node = inspect_type(ann)

    # ClassVar qualifier must be present
    assert "class_var" in node.qualifiers, (
        f"ClassVar qualifier lost in Annotated[ClassVar[int], 'meta']\n"
        f"  Got qualifiers: {node.qualifiers}"
    )
    # Metadata should also be preserved
    assert "meta" in node.metadata
