# pyright: reportAny=false, reportExplicitAny=false

from collections import deque
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    ClassVar,
    Final,
    Literal,
    ParamSpec,
    TypeVar,
)
from typing_extensions import TypeVarTuple

from hypothesis import HealthCheck, example, given, settings

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

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


def _walk(
    node: TypeNode,
    *,
    predicate: "Callable[[TypeNode], bool] | None" = None,
    max_depth: int | None = None,
) -> "Iterator[TypeNode]":
    """Local implementation of walk() following the graph-traversal specification.

    This function matches the spec in .internal/specs/graph-traversal.md.
    It will be replaced by the public walk() function when implemented.
    """
    if max_depth is not None and max_depth < 0:
        msg = f"max_depth must be non-negative, got {max_depth}"
        raise ValueError(msg)

    visited: set[int] = set()
    stack: deque[tuple[TypeNode, int]] = deque([(node, 0)])

    while stack:
        current, depth = stack.pop()
        node_id = id(current)

        if node_id in visited:
            continue
        visited.add(node_id)

        if predicate is None or predicate(current):
            yield current

        if max_depth is None or depth < max_depth:
            # Push children in reverse order for DFS ordering
            children = list(current.children())
            for child in reversed(children):
                stack.append((child, depth + 1))


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


@example(None)
@example(type(None))
@example(Literal[None])
@given(type_annotations())
@settings(deadline=None)
def test_none_variants_all_produce_valid_nodes(annotation: Any) -> None:
    cache_clear()
    node = inspect_type(annotation)
    assert isinstance(node, TypeNode)


@given(type_annotations())
@settings(suppress_health_check=[HealthCheck.too_slow], deadline=None)
@example(int)
@example(str)
@example(list[int])
@example(dict[str, int])
@example(tuple[int, str, float])
@example(int | str | float)
@example(dict[str, list[tuple[int, str] | None]])
def test_walk_visits_all_unique_nodes(annotation: Any) -> None:
    node = inspect_type(annotation)
    walked_nodes = list(_walk(node))
    count_via_manual = _count_nodes(node, max_nodes=1000)

    # walk() should yield exactly count_nodes unique nodes
    assert len(walked_nodes) == count_via_manual

    # All yielded nodes should be unique (by identity)
    node_ids = [id(n) for n in walked_nodes]
    assert len(node_ids) == len(set(node_ids))


@given(type_annotations())
@settings(deadline=None)
@example(int)
@example(list[int])
@example(dict[str, list[int]])
@example(tuple[int, str, float])
def test_walk_always_includes_root_node(annotation: Any) -> None:
    root = inspect_type(annotation)
    walked_nodes = list(_walk(root))

    # Root node must always be visited
    assert root in walked_nodes
    # Root node should be first in DFS traversal
    assert walked_nodes[0] is root


@given(type_annotations())
@settings(suppress_health_check=[HealthCheck.too_slow], deadline=None)
@example(int)
@example(list[int])
@example(dict[str, int])
@example(tuple[int, str])
def test_walk_yields_no_duplicates(annotation: Any) -> None:
    node = inspect_type(annotation)
    walked_nodes = list(_walk(node))

    # No node should appear more than once (by identity)
    seen_ids: set[int] = set()
    for walked_node in walked_nodes:
        node_id = id(walked_node)
        assert node_id not in seen_ids, f"Duplicate node: {walked_node!r}"
        seen_ids.add(node_id)


@given(type_annotations())
@settings(deadline=None)
@example(int)
@example(list[int])
@example(dict[str, int])
def test_walk_depth_zero_yields_only_root(annotation: Any) -> None:
    root = inspect_type(annotation)
    walked_nodes = list(_walk(root, max_depth=0))

    # Depth 0 should yield only the root
    assert len(walked_nodes) == 1
    assert walked_nodes[0] is root


@given(type_annotations())
@settings(deadline=None)
@example(list[int])
@example(dict[str, int])
@example(tuple[int, str])
@example(int | str)
def test_walk_depth_limiting_reduces_or_equals_full_traversal(annotation: Any) -> None:
    root = inspect_type(annotation)
    full_count = len(list(_walk(root)))
    limited_count = len(list(_walk(root, max_depth=1)))

    # Limited depth should visit fewer or equal nodes
    assert limited_count <= full_count


@given(type_annotations())
@settings(deadline=None)
@example(int)
@example(list[int])
@example(dict[str, int])
def test_walk_terminates_on_all_inputs(annotation: Any) -> None:
    node = inspect_type(annotation)
    # Ensure walk terminates within reasonable bounds
    for count, _ in enumerate(_walk(node), start=1):
        assert count < 1000, "walk() did not terminate within expected bounds"
