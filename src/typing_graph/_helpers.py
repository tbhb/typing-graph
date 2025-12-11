"""Helper functions for working with TypeNode instances."""

import typing

from ._node import (
    GenericTypeNode,
    TypeNode,
    is_concrete_node,
    is_subscripted_generic_node,
    is_union_type_node,
)


def is_union_node(node: TypeNode) -> bool:
    """Check if a node represents any union type.

    Returns ``True`` for both union representations:

    - ``UnionNode`` (from ``types.UnionType``, e.g., ``int | str``)
    - ``SubscriptedGeneric`` with ``origin.cls=typing.Union``
      (e.g., ``Literal['a'] | Literal['b']``)

    This function works consistently regardless of the ``normalize_unions``
    configuration setting. When normalization is enabled (the default),
    unions become ``UnionNode``; when disabled, ``typing.Union`` becomes
    ``SubscriptedGenericNode``. This function detects both.

    Args:
        node: A TypeNode to check.

    Returns:
        ``True`` if the node represents a union type, ``False`` otherwise.

    Examples:
        >>> from typing import Literal
        >>> from typing_graph import inspect_type, is_union_node
        >>>
        >>> is_union_node(inspect_type(int | str))
        True
        >>> is_union_node(inspect_type(Literal["a"] | Literal["b"]))
        True
        >>> is_union_node(inspect_type(list[int]))
        False

    Note:
        Use [get_union_members][typing_graph.get_union_members] to extract the
        member types. Use [is_union_type_node][typing_graph.is_union_type_node]
        if you only want to match ``UnionNode`` (not ``typing.Union``).
    """
    if is_union_type_node(node):
        return True

    if is_subscripted_generic_node(node):
        origin = node.origin
        # Checking identity against typing.Union for runtime introspection,
        # not using it as a type annotation, so the deprecation doesn't apply.
        if isinstance(origin, GenericTypeNode) and origin.cls is typing.Union:  # pyright: ignore[reportDeprecated]
            return True

    return False


def get_union_members(node: TypeNode) -> tuple[TypeNode, ...] | None:
    """Extract union members from either union representation.

    Python has two runtime representations for union types:

    - ``types.UnionType`` (PEP 604 ``|`` with concrete types) → ``UnionNode``
    - ``typing.Union`` (``Union[...]`` or ``|`` with typing special forms) →
      ``SubscriptedGeneric`` with ``origin.cls=typing.Union``

    This function handles both, returning the member types as a tuple.

    This function works consistently regardless of the ``normalize_unions``
    configuration setting, providing uniform access to union members whether
    the union is represented as ``UnionNode`` or ``SubscriptedGenericNode``.

    Args:
        node: A TypeNode to extract union members from.

    Returns:
        A tuple of member TypeNodes if ``node`` represents a union type,
        or ``None`` if ``node`` is not a union.

    Examples:
        >>> from typing import Literal
        >>> from typing_graph import inspect_type, get_union_members
        >>>
        >>> # types.UnionType (PEP 604 with concrete types)
        >>> node1 = inspect_type(int | str)
        >>> members1 = get_union_members(node1)
        >>> len(members1)
        2
        >>>
        >>> # typing.Union (from Literal | Literal)
        >>> node2 = inspect_type(Literal["a"] | Literal["b"])
        >>> members2 = get_union_members(node2)
        >>> len(members2)
        2

    Note:
        Use [is_union_node][typing_graph.is_union_node] to check if a node is
        a union before calling this function.
    """
    if not is_union_node(node):
        return None

    if is_union_type_node(node):
        return node.members

    # Must be SubscriptedGeneric with typing.Union origin (checked by is_union)
    if is_subscripted_generic_node(node):
        return node.args

    return None  # pragma: no cover


def is_optional_node(node: TypeNode) -> bool:
    """Check if a node represents an optional type (union containing None).

    Returns ``True`` for any union that includes ``None`` as a member:

    - ``int | None`` (PEP 604 syntax)
    - ``Union[int, None]`` (typing.Union)
    - ``Optional[int]`` (equivalent to Union[int, None])

    This function works consistently regardless of the ``normalize_unions``
    configuration setting.

    Args:
        node: A TypeNode to check.

    Returns:
        ``True`` if the node is a union containing ``None``, ``False`` otherwise.

    Examples:
        >>> from typing import Optional, Union
        >>> from typing_graph import inspect_type, is_optional_node
        >>>
        >>> is_optional_node(inspect_type(int | None))
        True
        >>> is_optional_node(inspect_type(Optional[str]))
        True
        >>> is_optional_node(inspect_type(int | str))
        False
        >>> is_optional_node(inspect_type(int))
        False

    Note:
        Use [unwrap_optional][typing_graph.unwrap_optional] to extract the
        non-None type(s) from an optional.
    """
    members = get_union_members(node)
    if members is None:
        return False

    return any(is_concrete_node(m) and m.cls is type(None) for m in members)


def unwrap_optional(node: TypeNode) -> tuple[TypeNode, ...] | None:
    """Extract non-None types from an optional union.

    Given an optional type (a union containing ``None``), returns a tuple of
    the non-None member types. Returns ``None`` if the node is not an optional.

    This function works consistently regardless of the ``normalize_unions``
    configuration setting.

    Args:
        node: A TypeNode to unwrap.

    Returns:
        A tuple of non-None member TypeNodes if ``node`` is an optional,
        or ``None`` if ``node`` is not an optional.

    Examples:
        >>> from typing import Optional
        >>> from typing_graph import inspect_type, unwrap_optional, is_concrete_node
        >>>
        >>> node = inspect_type(int | None)
        >>> unwrapped = unwrap_optional(node)
        >>> len(unwrapped)
        1
        >>> is_concrete_node(unwrapped[0]) and unwrapped[0].cls is int
        True
        >>>
        >>> # Multiple non-None types
        >>> node2 = inspect_type(int | str | None)
        >>> unwrapped2 = unwrap_optional(node2)
        >>> len(unwrapped2)
        2
        >>>
        >>> # Not an optional
        >>> unwrap_optional(inspect_type(int | str)) is None
        True

    Note:
        Use [is_optional_node][typing_graph.is_optional_node] to check if a
        node is optional before calling this function.
    """
    if not is_optional_node(node):
        return None

    members = get_union_members(node)
    if members is None:  # pragma: no cover
        return None

    return tuple(
        m for m in members if not (is_concrete_node(m) and m.cls is type(None))
    )
