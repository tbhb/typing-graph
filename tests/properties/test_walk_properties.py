# pyright: reportAny=false, reportExplicitAny=false

from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    ClassVar,
    Final,
    Literal,
)

import pytest
from hypothesis import HealthCheck, example, given, settings

from typing_graph import (
    ConcreteNode,
    TraversalError,
    TypeNode,
    inspect_type,
    walk,
)

from .helpers import measure_depth
from .strategies import extended_type_annotations, type_annotations

if TYPE_CHECKING:
    from typing_extensions import TypeIs


# ruff: noqa: PYI061 - testing Literal[None] vs bare None is intentional


def _count_nodes_manual(node: TypeNode, max_nodes: int = 1000) -> int:
    """Count unique nodes in graph via manual traversal."""
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


class TestWalkUniqueness:
    @given(type_annotations())
    @settings(deadline=None)
    @example(int)
    @example(list[int])
    @example(dict[str, int])
    @example(int | str)
    @example(tuple[int, str, float])
    def test_walk_yields_unique_nodes_by_identity(self, annotation: Any) -> None:
        node = inspect_type(annotation)
        walked = list(walk(node))
        ids = [id(n) for n in walked]
        assert len(ids) == len(set(ids)), "Duplicate nodes in walk"

    @given(type_annotations())
    @settings(deadline=None)
    @example(dict[str, str])  # Same type appears twice
    @example(tuple[int, int, int])  # Same type multiple times
    @example(list[int] | set[int])  # Shared children in union
    def test_walk_handles_diamond_pattern_no_duplicates(self, annotation: Any) -> None:
        node = inspect_type(annotation)
        walked = list(walk(node))

        seen_ids: set[int] = set()
        for walked_node in walked:
            node_id = id(walked_node)
            assert node_id not in seen_ids, f"Diamond caused duplicate: {walked_node!r}"
            seen_ids.add(node_id)


class TestWalkRootBehavior:
    @given(type_annotations())
    @settings(deadline=None)
    @example(int)
    @example(list[int])
    @example(dict[str, list[int]])
    @example(tuple[int, str, float])
    def test_walk_root_always_first(self, annotation: Any) -> None:
        root = inspect_type(annotation)
        walked = list(walk(root))

        assert len(walked) > 0, "walk() should yield at least the root"
        assert walked[0] is root, "Root node should be first"

    @given(type_annotations())
    @settings(deadline=None)
    @example(int)
    @example(list[int])
    @example(dict[str, int])
    def test_walk_root_always_included(self, annotation: Any) -> None:
        root = inspect_type(annotation)
        walked = list(walk(root))
        assert root in walked, "Root must always be in walked nodes"


class TestWalkPredicateSubset:
    @given(type_annotations())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    @example(int)
    @example(list[int])
    @example(dict[str, int])
    @example(int | str | float)
    def test_walk_with_predicate_is_subset(self, annotation: Any) -> None:
        node = inspect_type(annotation)
        all_nodes = list(walk(node))
        filtered_nodes = list(
            walk(node, predicate=lambda n: isinstance(n, ConcreteNode))
        )

        all_ids = {id(n) for n in all_nodes}
        filtered_ids = {id(n) for n in filtered_nodes}

        assert filtered_ids.issubset(all_ids), "Filtered nodes must be subset of all"

    @given(type_annotations())
    @settings(deadline=None)
    @example(int)
    @example(list[int])
    @example(dict[str, int])
    def test_walk_predicate_none_equals_no_predicate(self, annotation: Any) -> None:
        node = inspect_type(annotation)
        nodes_default = list(walk(node))
        nodes_none = list(walk(node, predicate=None))
        assert nodes_default == nodes_none

    @given(type_annotations())
    @settings(deadline=None)
    @example(list[int])
    @example(dict[str, int])
    @example(int | str)
    def test_walk_predicate_false_yields_nothing(self, annotation: Any) -> None:
        node = inspect_type(annotation)
        nodes = list(walk(node, predicate=lambda _n: False))
        assert len(nodes) == 0

    @given(type_annotations())
    @settings(deadline=None)
    @example(int)
    @example(list[int])
    @example(dict[str, int])
    def test_walk_predicate_true_equals_no_predicate(self, annotation: Any) -> None:
        node = inspect_type(annotation)
        nodes_default = list(walk(node))
        nodes_true = list(walk(node, predicate=lambda _n: True))
        assert nodes_default == nodes_true

    @given(type_annotations())
    @settings(deadline=None)
    @example(dict[str, int])
    @example(list[tuple[int, str]])
    @example(int | str | float | bool)
    def test_walk_predicate_filters_correctly(self, annotation: Any) -> None:
        node = inspect_type(annotation)

        def is_concrete(n: TypeNode) -> bool:
            return isinstance(n, ConcreteNode)

        filtered = list(walk(node, predicate=is_concrete))
        assert all(isinstance(n, ConcreteNode) for n in filtered)


class TestWalkTypeIsPredicate:
    @given(type_annotations())
    @settings(deadline=None)
    @example(list[int])
    @example(dict[str, int])
    @example(tuple[int, str])
    def test_walk_typeis_predicate_type_narrowing(self, annotation: Any) -> None:
        def is_concrete(n: TypeNode) -> "TypeIs[ConcreteNode]":
            return isinstance(n, ConcreteNode)

        node = inspect_type(annotation)
        concrete_nodes = list(walk(node, predicate=is_concrete))

        # Type system should narrow to ConcreteNode
        # At runtime, verify all are indeed ConcreteNode
        for n in concrete_nodes:
            assert isinstance(n, ConcreteNode)


class TestWalkDepthLimiting:
    @given(type_annotations())
    @settings(deadline=None)
    @example(int)
    @example(list[int])
    @example(dict[str, int])
    @example(list[dict[str, int]])
    def test_walk_depth_zero_yields_only_root(self, annotation: Any) -> None:
        root = inspect_type(annotation)
        walked = list(walk(root, max_depth=0))

        assert len(walked) == 1, "max_depth=0 should yield only root"
        assert walked[0] is root

    @given(type_annotations())
    @settings(deadline=None)
    @example(list[int])
    @example(dict[str, int])
    @example(tuple[int, str])
    @example(int | str)
    def test_walk_depth_one_yields_root_and_direct_children(
        self, annotation: Any
    ) -> None:
        root = inspect_type(annotation)
        walked = list(walk(root, max_depth=1))

        # Should include root
        assert root in walked

        # Should include direct children
        direct_children = list(root.children())
        for child in direct_children:
            assert child in walked, f"Direct child {child!r} missing from walk"

        # Count nodes: root + unique direct children
        expected_ids = {id(root)}
        for child in direct_children:
            expected_ids.add(id(child))
        assert len(walked) == len(expected_ids)

    @given(type_annotations())
    @settings(deadline=None)
    @example(list[int])
    @example(dict[str, list[int]])
    @example(tuple[int, str, float])
    @example(int | str | float)
    def test_walk_limited_depth_is_subset_of_unlimited(self, annotation: Any) -> None:
        root = inspect_type(annotation)
        unlimited = list(walk(root))
        limited = list(walk(root, max_depth=1))

        unlimited_ids = {id(n) for n in unlimited}
        limited_ids = {id(n) for n in limited}

        assert limited_ids.issubset(unlimited_ids)
        assert len(limited) <= len(unlimited)

    @given(type_annotations())
    @settings(deadline=None)
    @example(list[list[list[int]]])
    @example(dict[str, dict[str, dict[str, int]]])
    def test_walk_increasing_depth_visits_more_or_equal_nodes(
        self, annotation: Any
    ) -> None:
        root = inspect_type(annotation)

        prev_count = 0
        for depth in range(5):
            walked = list(walk(root, max_depth=depth))
            current_count = len(walked)
            assert current_count >= prev_count, (
                f"depth={depth} yielded fewer nodes than depth={depth - 1}"
            )
            prev_count = current_count

    @given(type_annotations())
    @settings(deadline=None)
    @example(int)
    @example(list[int])
    @example(dict[str, int])
    def test_walk_max_depth_none_equals_default(self, annotation: Any) -> None:
        root = inspect_type(annotation)
        default = list(walk(root))
        explicit_none = list(walk(root, max_depth=None))
        assert default == explicit_none


class TestWalkTermination:
    @given(type_annotations())
    @settings(deadline=None)
    @example(int)
    @example(list[int])
    @example(dict[str, int])
    @example(dict[str, list[tuple[int, str] | None]])
    def test_walk_always_terminates(self, annotation: Any) -> None:
        node = inspect_type(annotation)
        max_iterations = 1000

        for count, _ in enumerate(walk(node), start=1):
            assert count <= max_iterations, "walk() did not terminate"

    @given(extended_type_annotations())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_walk_terminates_on_extended_types(self, annotation: Any) -> None:
        try:
            node = inspect_type(annotation)
        except NameError:
            # Some extended types may fail to resolve
            return

        max_iterations = 1000

        for count, _ in enumerate(walk(node), start=1):
            assert count <= max_iterations, "walk() did not terminate"


class TestWalkNodeConsistency:
    @given(type_annotations())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    @example(int)
    @example(list[int])
    @example(dict[str, int])
    @example(tuple[int, str])
    @example(int | str)
    def test_walk_yields_only_type_nodes(self, annotation: Any) -> None:
        node = inspect_type(annotation)
        for walked_node in walk(node):
            assert isinstance(walked_node, TypeNode), (
                f"Non-TypeNode yielded: {type(walked_node)}"
            )

    @given(type_annotations())
    @settings(deadline=None)
    @example(int)
    @example(list[int])
    @example(dict[str, int])
    def test_walk_count_matches_manual_count(self, annotation: Any) -> None:
        node = inspect_type(annotation)
        walked_count = len(list(walk(node)))
        manual_count = _count_nodes_manual(node)

        assert walked_count == manual_count, (
            f"walk() yielded {walked_count} but manual count is {manual_count}"
        )


class TestWalkErrors:
    @given(type_annotations())
    @settings(deadline=None)
    @example(int)
    @example(list[int])
    def test_walk_negative_max_depth_raises_traversal_error(
        self, annotation: Any
    ) -> None:
        node = inspect_type(annotation)
        with pytest.raises(TraversalError) as exc_info:
            _ = list(walk(node, max_depth=-1))
        assert "max_depth must be non-negative" in str(exc_info.value)

    @given(type_annotations())
    @settings(deadline=None)
    @example(int)
    @example(list[int])
    def test_walk_very_negative_max_depth_raises(self, annotation: Any) -> None:
        node = inspect_type(annotation)
        with pytest.raises(TraversalError):
            _ = list(walk(node, max_depth=-100))


class TestWalkEdgeConsistency:
    @given(type_annotations())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    @example(int)
    @example(list[int])
    @example(dict[str, int])
    @example(tuple[int, str])
    def test_walk_children_equals_edge_targets(self, annotation: Any) -> None:
        node = inspect_type(annotation)

        for walked_node in walk(node):
            children = list(walked_node.children())
            edge_targets = [conn.target for conn in walked_node.edges()]
            assert children == edge_targets, (
                f"children() != edge targets for {walked_node!r}"
            )


class TestWalkDeterminism:
    @given(type_annotations())
    @settings(deadline=None)
    @example(int)
    @example(list[int])
    @example(dict[str, int])
    @example(int | str | float)
    def test_walk_is_deterministic(self, annotation: Any) -> None:
        node = inspect_type(annotation)

        walk1 = list(walk(node))
        walk2 = list(walk(node))
        walk3 = list(walk(node))

        assert walk1 == walk2 == walk3, "walk() should be deterministic"

    @given(type_annotations())
    @settings(deadline=None)
    @example(list[int])
    @example(dict[str, int])
    @example(tuple[int, str])
    def test_walk_order_is_consistent(self, annotation: Any) -> None:
        node = inspect_type(annotation)

        ids1 = [id(n) for n in walk(node)]
        ids2 = [id(n) for n in walk(node)]

        assert ids1 == ids2, "walk() order should be consistent"


class TestWalkDepthProperties:
    @given(type_annotations())
    @settings(deadline=None)
    @example(list[list[list[int]]])
    @example(dict[str, dict[str, int]])
    def test_walk_depth_limit_respects_graph_depth(self, annotation: Any) -> None:
        root = inspect_type(annotation)
        max_graph_depth = measure_depth(root)

        # Walking with unlimited depth should visit all nodes
        unlimited = list(walk(root))

        # Walking with depth >= max should also visit all nodes
        at_max = list(walk(root, max_depth=max_graph_depth))
        beyond_max = list(walk(root, max_depth=max_graph_depth + 10))

        assert len(at_max) == len(unlimited)
        assert len(beyond_max) == len(unlimited)

    @given(type_annotations())
    @settings(deadline=None)
    @example(list[int])
    @example(dict[str, int])
    def test_walk_depth_zero_only_visits_root_level(self, annotation: Any) -> None:
        root = inspect_type(annotation)
        walked = list(walk(root, max_depth=0))

        # Only root should be visited
        assert len(walked) == 1
        assert walked[0] is root

        # No children should be in the walked list
        for child in root.children():
            assert child not in walked


class TestWalkCombinedParameters:
    @given(type_annotations())
    @settings(deadline=None)
    @example(list[int])
    @example(dict[str, int])
    @example(tuple[int, str])
    def test_walk_predicate_and_depth_combined(self, annotation: Any) -> None:
        root = inspect_type(annotation)

        def is_concrete(n: TypeNode) -> bool:
            return isinstance(n, ConcreteNode)

        # Test combining predicate with depth limit
        filtered_limited = list(walk(root, predicate=is_concrete, max_depth=1))
        all_limited = list(walk(root, max_depth=1))
        all_filtered = list(walk(root, predicate=is_concrete))

        # filtered_limited should be subset of both
        filtered_limited_ids = {id(n) for n in filtered_limited}
        all_limited_ids = {id(n) for n in all_limited}
        all_filtered_ids = {id(n) for n in all_filtered}

        assert filtered_limited_ids.issubset(all_limited_ids)
        assert filtered_limited_ids.issubset(all_filtered_ids)

    @given(type_annotations())
    @settings(deadline=None)
    @example(list[int])
    @example(dict[str, int])
    def test_walk_all_parameters_combined(self, annotation: Any) -> None:
        root = inspect_type(annotation)

        result = list(
            walk(
                root,
                predicate=lambda _n: True,
                max_depth=10,
            )
        )

        # Should be equivalent to default walk (predicate always true, depth high)
        default = list(walk(root))
        assert result == default


class TestWalkExplicitExamples:
    @example(None)
    @example(type(None))
    @example(Literal[None])
    @example(ClassVar[int])
    @example(Final[str])
    @example(Annotated[int, "metadata"])
    @example(Annotated[list[int], "outer", "metadata"])
    @given(extended_type_annotations())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_walk_handles_all_annotation_forms(self, annotation: Any) -> None:
        try:
            node = inspect_type(annotation)
        except NameError:
            return

        walked = list(walk(node))

        # Basic invariants
        assert len(walked) >= 1
        assert walked[0] is node
        assert all(isinstance(n, TypeNode) for n in walked)

        # No duplicates
        ids = [id(n) for n in walked]
        assert len(ids) == len(set(ids))


class TestWalkThreadSafety:
    @given(type_annotations())
    @settings(deadline=None)
    @example(dict[str, list[int]])
    @example(tuple[int, str, float])
    @example(int | str | float | None)
    def test_walk_concurrent_on_same_graph(self, annotation: Any) -> None:
        import threading

        node = inspect_type(annotation)
        results: list[list[TypeNode]] = []
        errors: list[BaseException] = []
        lock = threading.Lock()

        def walk_graph() -> None:
            try:
                walked = list(walk(node))
                with lock:
                    results.append(walked)
            except BaseException as e:  # noqa: BLE001 - need to catch any thread exception
                with lock:
                    errors.append(e)

        threads = [threading.Thread(target=walk_graph) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Concurrent walk raised errors: {errors}"
        assert len(results) == 4

        # All results should have the same nodes (by identity)
        first_ids = [id(n) for n in results[0]]
        for result in results[1:]:
            result_ids = [id(n) for n in result]
            assert result_ids == first_ids, "Different results"

    @given(type_annotations())
    @settings(deadline=None, max_examples=50)
    @example(dict[str, list[int]])
    @example(tuple[int, str, float])
    @example(int | str | float | None)
    def test_walk_concurrent_high_thread_count(self, annotation: Any) -> None:
        import threading

        node = inspect_type(annotation)
        results: list[list[TypeNode]] = []
        errors: list[BaseException] = []
        lock = threading.Lock()

        def walk_graph() -> None:
            try:
                walked = list(walk(node))
                with lock:
                    results.append(walked)
            except BaseException as e:  # noqa: BLE001 - need to catch any thread exception
                with lock:
                    errors.append(e)

        threads = [threading.Thread(target=walk_graph) for _ in range(16)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Concurrent walk raised errors: {errors}"
        assert len(results) == 16

        first_ids = [id(n) for n in results[0]]
        for result in results[1:]:
            result_ids = [id(n) for n in result]
            assert result_ids == first_ids, "Different results"


class TestChildrenThreadSafety:
    @given(type_annotations())
    @settings(deadline=None)
    @example(dict[str, list[int]])
    @example(tuple[int, str, float])
    def test_children_concurrent_access(self, annotation: Any) -> None:
        import threading

        node = inspect_type(annotation)
        all_nodes = list(walk(node))
        errors: list[BaseException] = []
        results_per_thread: list[list[tuple[int, int]]] = []
        lock = threading.Lock()

        def access_children() -> None:
            try:
                thread_results: list[tuple[int, int]] = []
                for n in all_nodes:
                    for _ in range(100):
                        children = n.children()
                        thread_results.append((id(n), len(children)))
                with lock:
                    results_per_thread.append(thread_results)
            except BaseException as e:  # noqa: BLE001 - need to catch any thread exception
                with lock:
                    errors.append(e)

        threads = [threading.Thread(target=access_children) for _ in range(16)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Concurrent children() raised errors: {errors}"
        assert len(results_per_thread) == 16

        first_result = results_per_thread[0]
        for result in results_per_thread[1:]:
            assert result == first_result, "Children results differ across threads"
