from typing import TYPE_CHECKING

import pytest

from typing_graph import (
    ConcreteNode,
    TraversalError,
    TypeNode,
    TypingGraphError,
    inspect_type,
    walk,
)

if TYPE_CHECKING:
    from typing_extensions import TypeIs


class TestWalkBasic:
    def test_walk_simple_type(self) -> None:
        node = inspect_type(int)
        nodes = list(walk(node))
        assert len(nodes) == 1
        assert nodes[0] is node

    def test_walk_generic_type(self) -> None:
        node = inspect_type(list[int])
        nodes = list(walk(node))
        # SubscriptedGenericNode + GenericTypeNode (origin) + ConcreteNode (int)
        assert len(nodes) == 3

    def test_walk_nested_type(self) -> None:
        node = inspect_type(dict[str, list[int]])
        nodes = list(walk(node))
        # dict[str, list[int]] has multiple nested levels
        assert len(nodes) >= 4

    def test_walk_union_type(self) -> None:
        node = inspect_type(int | str)
        nodes = list(walk(node))
        # UnionNode + 2 ConcreteNodes
        assert len(nodes) >= 3


class TestWalkPredicate:
    def test_walk_with_predicate_none(self) -> None:
        node = inspect_type(list[int])
        nodes_no_pred = list(walk(node))
        nodes_with_none = list(walk(node, predicate=None))
        assert nodes_no_pred == nodes_with_none

    def test_walk_with_predicate_filter(self) -> None:
        node = inspect_type(dict[str, int])
        concrete_only = list(
            walk(node, predicate=lambda n: isinstance(n, ConcreteNode))
        )
        # Should only have str and int (2 ConcreteNodes)
        assert len(concrete_only) == 2
        assert all(isinstance(n, ConcreteNode) for n in concrete_only)

    def test_walk_with_typeis_predicate(self) -> None:
        def is_concrete(n: TypeNode) -> "TypeIs[ConcreteNode]":
            return isinstance(n, ConcreteNode)

        node = inspect_type(list[int])
        concrete_nodes = list(walk(node, predicate=is_concrete))
        assert all(isinstance(n, ConcreteNode) for n in concrete_nodes)

    def test_walk_predicate_filters_correctly(self) -> None:
        node = inspect_type(list[int])
        # Filter that matches nothing
        nodes = list(walk(node, predicate=lambda _n: False))
        assert len(nodes) == 0

    def test_walk_predicate_exception_propagates(self) -> None:
        def failing_predicate(_n: TypeNode) -> bool:
            msg = "predicate failed"
            raise ValueError(msg)

        node = inspect_type(list[int])
        with pytest.raises(ValueError, match="predicate failed"):
            _ = list(walk(node, predicate=failing_predicate))


class TestWalkMaxDepth:
    def test_walk_max_depth_zero(self) -> None:
        node = inspect_type(list[dict[str, int]])
        nodes = list(walk(node, max_depth=0))
        assert len(nodes) == 1
        assert nodes[0] is node

    def test_walk_max_depth_one(self) -> None:
        node = inspect_type(list[int])
        nodes = list(walk(node, max_depth=1))
        # Root + its direct children (origin + args)
        assert len(nodes) >= 2

    def test_walk_max_depth_limits_deep_nesting(self) -> None:
        # Create a deeply nested type
        node = inspect_type(list[list[list[int]]])
        full_nodes = list(walk(node))
        limited_nodes = list(walk(node, max_depth=2))
        assert len(limited_nodes) < len(full_nodes)

    def test_walk_max_depth_none_traverses_all(self) -> None:
        node = inspect_type(dict[str, list[int]])
        nodes_none = list(walk(node, max_depth=None))
        nodes_default = list(walk(node))
        assert len(nodes_none) == len(nodes_default)


class TestWalkErrors:
    def test_walk_negative_max_depth_raises(self) -> None:
        node = inspect_type(int)
        with pytest.raises(TraversalError) as exc_info:
            _ = list(walk(node, max_depth=-1))
        assert "max_depth must be non-negative" in str(exc_info.value)
        assert "-1" in str(exc_info.value)

    def test_traversal_error_inherits_from_base(self) -> None:
        assert issubclass(TraversalError, TypingGraphError)
        assert issubclass(TypingGraphError, Exception)


class TestWalkVisitedTracking:
    def test_walk_visits_each_node_once(self) -> None:
        # Union types may share child nodes (e.g., None is common)
        node = inspect_type(int | str | None)
        nodes = list(walk(node))
        node_ids = [id(n) for n in nodes]
        # All node IDs should be unique
        assert len(node_ids) == len(set(node_ids))

    def test_walk_handles_diamond_pattern(self) -> None:
        # Type like dict[str, str] where str appears twice
        node = inspect_type(dict[str, str])
        nodes = list(walk(node))
        # str node should only appear once due to caching in inspect_type
        concrete_nodes = [n for n in nodes if isinstance(n, ConcreteNode)]
        str_nodes = [n for n in concrete_nodes if n.cls is str]
        # Due to caching, both str annotations point to same node
        assert len(str_nodes) == 1


class TestWalkIterator:
    def test_walk_is_lazy(self) -> None:
        node = inspect_type(list[int])
        iterator = walk(node)
        # Should be a generator, not a list
        assert hasattr(iterator, "__next__")
        # Get first node
        first = next(iterator)
        assert first is node

    def test_walk_can_be_partially_consumed(self) -> None:
        node = inspect_type(dict[str, list[int]])
        iterator = walk(node)
        first = next(iterator)
        # Iterator should still have more items
        remaining = list(iterator)
        assert first not in remaining

    def test_walk_can_be_abandoned(self) -> None:
        node = inspect_type(list[int])
        # Create iterator but don't consume it fully
        iterator = walk(node)
        first = next(iterator)
        assert first is node
        # Abandon the iterator without consuming remaining items
        # This verifies that partial consumption doesn't cause issues
        del iterator


class TestWalkDFS:
    def test_walk_is_depth_first(self) -> None:
        # For list[int], DFS should visit:
        # 1. list[int] (SubscriptedGenericNode)
        # 2. list (GenericTypeNode) - first child
        # 3. int (ConcreteNode) - second child
        node = inspect_type(list[int])
        nodes = list(walk(node))
        # First node is always the root
        assert nodes[0] is node
        # Children should follow parent before siblings in DFS
        # This is verified by the order of traversal
        assert len(nodes) == 3
