"""Graph traversal functions for typing-graph.

This module provides the walk() iterator for depth-first traversal of type graphs,
along with the exception hierarchy for traversal errors.
"""

from collections import deque
from typing import TYPE_CHECKING, overload

from ._exceptions import TraversalError

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from typing_extensions import TypeIs

    from ._node import TypeNode, TypeNodeT


@overload
def walk(  # pragma: no cover
    node: "TypeNode",
    *,
    predicate: "Callable[[TypeNode], TypeIs[TypeNodeT]]",
    max_depth: int | None = None,
) -> "Iterator[TypeNodeT]": ...


@overload
def walk(  # pragma: no cover
    node: "TypeNode",
    *,
    predicate: "Callable[[TypeNode], bool] | None" = None,
    max_depth: int | None = None,
) -> "Iterator[TypeNode]": ...


def walk(
    node: "TypeNode",
    *,
    predicate: "Callable[[TypeNode], bool] | None" = None,
    max_depth: int | None = None,
) -> "Iterator[TypeNode]":
    """Traverse the type graph depth-first, yielding unique nodes.

    This function uses an iterative stack to prevent recursion depth errors.
    Each node is visited exactly once (by object identity).

    Args:
        node: The root node to start traversal from.
        predicate: Optional filter function. If provided, only nodes for which
            predicate(node) returns True are yielded. When using a TypeIs
            predicate, the return type is narrowed accordingly.
        max_depth: Maximum traversal depth. If None, no limit is imposed.
            When depth exceeds this limit, traversal stops descending
            into that branch but continues with other branches.
            Depth 0 yields only the root node.

    Yields:
        TypeNode instances matching the predicate (or all nodes if no predicate).

    Raises:
        TraversalError: If max_depth is negative.

    Note:
        The predicate and max_depth parameters are keyword-only to prevent
        accidental positional usage and to allow future parameters to be
        added without breaking changes.

    Examples:
        Basic traversal of all nodes:

        >>> from typing_graph import inspect_type
        >>> from typing_graph import walk
        >>> node = inspect_type(list[int])
        >>> len(list(walk(node)))
        3

        Filtered traversal with type narrowing:

        >>> from typing_graph import inspect_type, walk, ConcreteNode, TypeNode
        >>> from typing_extensions import TypeIs
        >>> def is_concrete(n: TypeNode) -> TypeIs[ConcreteNode]:
        ...     return isinstance(n, ConcreteNode)
        >>> node = inspect_type(dict[str, int])
        >>> concrete_nodes = list(walk(node, predicate=is_concrete))
        >>> all(isinstance(n, ConcreteNode) for n in concrete_nodes)
        True

        Depth-limited traversal:

        >>> from typing_graph import inspect_type, walk
        >>> node = inspect_type(list[dict[str, int]])
        >>> # Depth 0 yields only the root
        >>> len(list(walk(node, max_depth=0)))
        1
    """
    # Validate max_depth
    if max_depth is not None and max_depth < 0:
        msg = f"max_depth must be non-negative, got {max_depth}"
        raise TraversalError(msg)

    visited: set[int] = set()

    # Initialize stack with (node, depth) tuples
    stack: deque[tuple[TypeNode, int]] = deque([(node, 0)])

    while stack:
        current, depth = stack.pop()
        node_id = id(current)

        # Skip already visited nodes
        if node_id in visited:
            continue
        visited.add(node_id)

        # Yield if predicate matches (or no predicate)
        if predicate is None or predicate(current):
            yield current

        # Push children if within depth limit
        if max_depth is None or depth < max_depth:
            # Push children in reverse order for DFS ordering
            children = list(current.children())
            for child in reversed(children):
                stack.append((child, depth + 1))
