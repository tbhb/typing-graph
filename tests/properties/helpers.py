# pyright: reportAny=false, reportExplicitAny=false
# ruff: noqa: TC001 - import used at runtime for isinstance checks

from typing_graph import TypeNode
from typing_graph._node import (
    CallableNode,
    ConcatenateNode,
    ConcreteNode,
    ForwardRefNode,
    GenericAliasNode,
    GenericTypeNode,
    LiteralNode,
    MetaNode,
    NewTypeNode,
    ParamSpecNode,
    SubscriptedGenericNode,
    TupleNode,
    TypeAliasNode,
    TypeGuardNode,
    TypeIsNode,
    TypeVarNode,
    TypeVarTupleNode,
    UnionNode,
    UnpackNode,
    is_ellipsis_node,
)


def nodes_structurally_equal(  # noqa: PLR0911 - many early returns are clearer
    n1: TypeNode,
    n2: TypeNode,
    visited: set[tuple[int, int]] | None = None,
) -> bool:
    """Check if two TypeNode instances are structurally equivalent.

    Two nodes are structurally equivalent if they:
    - Have the same concrete type
    - Have the same metadata tuple
    - Have the same qualifiers frozenset
    - Have the same type-specific attributes (cls, name, values, etc.)
    - Have structurally equivalent children in the same order

    This comparison ignores object identity (id) and only compares structure.
    Source locations are not compared as they may differ based on context.
    """
    if visited is None:
        visited = set()

    key = (id(n1), id(n2))
    if key in visited:
        return True
    visited.add(key)

    # Must be same node type
    if type(n1) is not type(n2):
        return False

    # Must have same metadata
    if n1.metadata != n2.metadata:
        return False

    # Must have same qualifiers
    if n1.qualifiers != n2.qualifiers:
        return False

    # Check type-specific attributes
    if not _check_type_specific_attributes(n1, n2, visited):
        return False

    # Must have same number of children
    c1, c2 = list(n1.children()), list(n2.children())
    if len(c1) != len(c2):
        return False

    # All children must be structurally equal
    return all(
        nodes_structurally_equal(x, y, visited) for x, y in zip(c1, c2, strict=True)
    )


def _check_type_specific_attributes(  # noqa: PLR0911, PLR0912, PLR0915 - exhaustive type dispatch
    n1: TypeNode,
    n2: TypeNode,
    visited: set[tuple[int, int]],
) -> bool:
    """Check type-specific attributes for structural equality."""
    # ConcreteNode and GenericTypeNode have .cls
    if isinstance(n1, ConcreteNode):
        assert isinstance(n2, ConcreteNode)
        if n1.cls is not n2.cls:
            return False

    elif isinstance(n1, GenericTypeNode):
        assert isinstance(n2, GenericTypeNode)
        if n1.cls is not n2.cls:
            return False
        # Check type_params
        if len(n1.type_params) != len(n2.type_params):
            return False
        for tp1, tp2 in zip(n1.type_params, n2.type_params, strict=True):
            if not nodes_structurally_equal(tp1, tp2, visited):
                return False

    elif isinstance(n1, TypeVarNode):
        assert isinstance(n2, TypeVarNode)
        if n1.name != n2.name:
            return False
        if n1.variance != n2.variance:
            return False
        if n1.infer_variance != n2.infer_variance:
            return False
        # bound and constraints are checked via children()

    elif isinstance(n1, ParamSpecNode):
        assert isinstance(n2, ParamSpecNode)
        if n1.name != n2.name:
            return False

    elif isinstance(n1, TypeVarTupleNode):
        assert isinstance(n2, TypeVarTupleNode)
        if n1.name != n2.name:
            return False

    elif isinstance(n1, LiteralNode):
        assert isinstance(n2, LiteralNode)
        if n1.values != n2.values:
            return False

    elif isinstance(n1, TupleNode):
        assert isinstance(n2, TupleNode)
        if n1.homogeneous != n2.homogeneous:
            return False
        # elements are checked via children()

    elif isinstance(n1, ForwardRefNode):
        assert isinstance(n2, ForwardRefNode)
        if n1.ref != n2.ref:
            return False
        # state comparison is complex - check type of state
        if type(n1.state) is not type(n2.state):
            return False

    elif isinstance(n1, NewTypeNode):
        assert isinstance(n2, NewTypeNode)
        if n1.name != n2.name:
            return False
        # supertype is checked via children()

    elif isinstance(n1, TypeAliasNode):
        assert isinstance(n2, TypeAliasNode)
        if n1.name != n2.name:
            return False
        # value is checked via children()

    elif isinstance(n1, GenericAliasNode):
        assert isinstance(n2, GenericAliasNode)
        if n1.name != n2.name:
            return False
        # type_params and value are checked via children()

    elif isinstance(n1, ConcatenateNode):
        assert isinstance(n2, ConcatenateNode)
        # prefix and param_spec are checked via children()

    elif isinstance(n1, CallableNode):
        assert isinstance(n2, CallableNode)
        # Check params type
        if type(n1.params) is not type(n2.params):
            return False
        if isinstance(n1.params, tuple) and isinstance(n2.params, tuple):
            if len(n1.params) != len(n2.params):
                return False
        elif is_ellipsis_node(n1.params) and is_ellipsis_node(n2.params):
            pass  # Both ellipsis
        # params and returns are checked via children()

    elif isinstance(n1, SubscriptedGenericNode):
        assert isinstance(n2, SubscriptedGenericNode)
        # origin and args are checked via children()

    elif isinstance(n1, UnionNode):
        assert isinstance(n2, UnionNode)
        # members are checked via children()

    elif isinstance(n1, MetaNode):
        assert isinstance(n2, MetaNode)
        # of is checked via children()

    elif isinstance(n1, TypeGuardNode):
        assert isinstance(n2, TypeGuardNode)
        # narrows_to is checked via children()

    elif isinstance(n1, TypeIsNode):
        assert isinstance(n2, TypeIsNode)
        # narrows_to is checked via children()

    elif isinstance(n1, UnpackNode):
        assert isinstance(n2, UnpackNode)
        # target is checked via children()

    # Base case: no additional attributes to check
    return True


def measure_depth(
    node: TypeNode,
    current_depth: int = 0,
    visited: set[int] | None = None,
) -> int:
    """Measure the maximum depth of a TypeNode graph.

    Traverses the graph using depth-first search, tracking the deepest level
    reached. Handles cycles by tracking visited node IDs.

    Args:
        node: The TypeNode to measure depth from.
        current_depth: Current depth level (used in recursion).
        visited: Set of visited node IDs (used for cycle detection).

    Returns:
        The maximum depth of the graph from this node.
    """
    if visited is None:
        visited = set()

    node_id = id(node)
    if node_id in visited:
        return current_depth
    visited.add(node_id)

    children = list(node.children())
    if not children:
        return current_depth

    return max(measure_depth(c, current_depth + 1, visited) for c in children)
