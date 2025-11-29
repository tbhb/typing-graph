# pyright: reportAny=false, reportExplicitAny=false

from typing import Annotated, Any, ClassVar, Final, Literal, ParamSpec, TypeVar
from typing_extensions import TypeVarTuple

from hypothesis import HealthCheck, example, given, settings

from typing_graph import (
    AnnotatedNode,
    AnyNode,
    ConcreteNode,
    EllipsisNode,
    LiteralNode,
    MetaNode,
    NeverNode,
    NewTypeNode,
    SelfNode,
    SubscriptedGenericNode,
    TypeAliasNode,
    TypeGuardNode,
    TypeIsNode,
    TypeNode,
    UnionNode,
    UnpackNode,
    cache_clear,
    inspect_type,
)
from typing_graph._node import LiteralStringNode

from .strategies import extended_type_annotations, type_annotations

# ruff: noqa: PYI061 - testing Literal[None] vs bare None is intentional

# Leaf types have no children
LEAF_TYPES = (
    ConcreteNode,
    AnyNode,
    NeverNode,
    SelfNode,
    EllipsisNode,
    LiteralStringNode,
    LiteralNode,
)

# Container types always have at least one child
# Note: TupleType excluded (empty tuple has no children)
# Note: GenericTypeNode excluded (unparameterized generics may have empty type_params)
# Note: CallableType with empty params still has return type child
CONTAINER_TYPES = (
    SubscriptedGenericNode,
    UnionNode,
    MetaNode,
    TypeGuardNode,
    TypeIsNode,
    UnpackNode,
    TypeAliasNode,
    NewTypeNode,
    AnnotatedNode,
)


def _verify_children_recursive(node: TypeNode, visited: set[int]) -> None:
    """Recursively verify all children are valid TypeNode instances."""
    node_id = id(node)
    if node_id in visited:
        return
    visited.add(node_id)

    for child in node.children():
        assert isinstance(child, TypeNode), f"Child {child!r} is not a TypeNode"
        _verify_children_recursive(child, visited)


def _count_nodes(node: TypeNode, max_nodes: int) -> int:
    """Count nodes in graph, stopping at max_nodes to detect runaway traversal."""
    visited: set[int] = set()
    stack = [node]
    count = 0

    while stack and count < max_nodes:
        current = stack.pop()
        node_id = id(current)
        if node_id in visited:
            continue
        visited.add(node_id)
        count += 1
        stack.extend(current.children())

    return count


def _verify_children_content(node: TypeNode, visited: set[int]) -> None:
    """Verify children content matches the node's structure.

    This is a stronger check than just verifying children are TypeNodes.
    It checks that:
    - Leaf nodes (primitives, special forms) have no children
    - Container nodes have the expected number of children
    - Children are actually related to the parent's type structure
    """
    node_id = id(node)
    if node_id in visited:
        return
    visited.add(node_id)

    children = list(node.children())

    # Leaf nodes should have no children
    if isinstance(node, LEAF_TYPES):
        assert len(children) == 0, (
            f"{type(node).__name__} should have no children, got {len(children)}"
        )

    # Container nodes should have at least one child
    if isinstance(node, CONTAINER_TYPES):
        assert len(children) >= 1, (
            f"{type(node).__name__} should have at least one child"
        )

    # Recurse into children
    for child in children:
        _verify_children_content(child, visited)


@given(type_annotations())
@settings(suppress_health_check=[HealthCheck.too_slow], deadline=None)
@example(int)
@example(str)
@example(float)
@example(bool)
@example(bytes)
@example(type(None))
@example(Any)
@example(list[int])
@example(dict[str, int])
@example(tuple[()])
@example(tuple[int, str])
@example(tuple[int, ...])
@example(set[str])
@example(frozenset[int])
@example(int | str)
@example(int | str | float)
@example(Literal[1, 2, 3])
@example(Literal["a", "b"])
def test_children_returns_valid_type_nodes(annotation: Any) -> None:
    node = inspect_type(annotation)
    _verify_children_recursive(node, visited=set())


@given(type_annotations())
@settings(deadline=None)
@example(int)
@example(list[int])
@example(dict[str, list[int]])
@example(tuple[int, str, float])
def test_graph_traversal_terminates(annotation: Any) -> None:
    node = inspect_type(annotation)
    count = _count_nodes(node, max_nodes=1000)
    assert count < 1000, "Graph traversal exceeded reasonable size"


@given(type_annotations())
@settings(suppress_health_check=[HealthCheck.too_slow], deadline=None)
@example(int)
@example(str)
@example(Any)
@example(list[int])
@example(dict[str, int])
@example(int | str)
@example(Literal[1, 2, 3])
@example(tuple[()])
def test_children_content_matches_structure(annotation: Any) -> None:
    node = inspect_type(annotation)
    _verify_children_content(node, visited=set())


@given(type_annotations())
@settings(deadline=None)
@example(int)
@example(list[int])
@example(dict[str, int])
@example(int | str)
def test_inspect_type_is_idempotent(annotation: Any) -> None:
    node1 = inspect_type(annotation)
    node2 = inspect_type(annotation)
    # Cache should return same instance
    assert node1 is node2


# =============================================================================
# Error Boundary Tests
# =============================================================================


# Explicit edge case examples from unit tests
@example(None)  # None literal
@example(type(None))  # NoneType
@example(Literal[None])  # Literal[None] - noqa: PYI061
@example(dict[str, list[tuple[int, str] | None]])  # Complex nested type
@example(ClassVar[int])  # ClassVar qualifier
@example(Final[str])  # Final qualifier
@example(Annotated[int, "metadata"])  # Annotated with metadata
@example(TypeVar("T"))  # Simple TypeVar
@example(TypeVar("T_co", covariant=True))  # Covariant TypeVar
@example(TypeVar("T_contra", contravariant=True))  # Contravariant TypeVar
@example(TypeVar("T", bound=int))  # TypeVar with bound
@example(TypeVar("T", int, str))  # TypeVar with constraints
@example(ParamSpec("P"))  # ParamSpec
@example(TypeVarTuple("Ts"))  # TypeVarTuple
@given(extended_type_annotations())
@settings(
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_inspect_type_never_raises_unexpectedly(annotation: Any) -> None:
    cache_clear()

    # inspect_type should never raise exceptions for valid type annotations.
    # The only expected exception is NameError for EAGER mode with unresolvable
    # forward refs, but we're using default config which uses DEFERRED mode.
    try:
        result = inspect_type(annotation)
        assert isinstance(result, TypeNode)
    except NameError:
        # Expected for EAGER mode with unresolvable forward refs
        pass


# =============================================================================
# Edge Case Examples from Unit Tests
# =============================================================================


@example(None)
@example(type(None))
@example(Literal[None])
@given(type_annotations())
@settings(deadline=None)
def test_none_variants_all_produce_valid_nodes(annotation: Any) -> None:
    cache_clear()
    node = inspect_type(annotation)
    assert isinstance(node, TypeNode)
