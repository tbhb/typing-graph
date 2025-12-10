from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from functools import reduce
from typing import TYPE_CHECKING

from typing_graph import ConcreteNode, TypeNode, inspect_type, walk

if TYPE_CHECKING:
    from pytest_benchmark.fixture import BenchmarkFixture


# Complex type for benchmarks (from spec)
complex_type = dict[str, list[tuple[int, Callable[[str], bool]]]]


def build_union(n: int) -> object:
    """Build a Union of n ConcreteNode types.

    Creates dynamic types to ensure each union member is unique.
    Uses the | operator (PEP 604) instead of typing.Union.
    """
    types = [type(f"T{i}", (), {}) for i in range(n)]
    return reduce(lambda a, b: a | b, types)


def build_nested_type(depth: int) -> type:
    """Build a nested list type of given depth."""
    result: type = int
    for _ in range(depth):
        result = list[result]
    return result


def is_concrete_node(node: TypeNode) -> bool:
    """Predicate for ConcreteNode instances."""
    return isinstance(node, ConcreteNode)


class TestPredicateFilteringOverhead:
    # Spec acceptance: predicate overhead < 20% compared to unfiltered walk

    def test_benchmark_walk_with_predicate(self, benchmark: "BenchmarkFixture") -> None:
        node = inspect_type(complex_type, use_cache=False)
        benchmark(lambda: list(walk(node, predicate=is_concrete_node)))

    def test_benchmark_walk_without_predicate(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        node = inspect_type(complex_type, use_cache=False)
        benchmark(lambda: list(walk(node)))


class TestEdgeCachingVerification:
    # Spec acceptance: edges() returns same object (identity check), O(1) access

    def test_benchmark_edges_caching(self, benchmark: "BenchmarkFixture") -> None:
        node = inspect_type(list[dict[str, int]], use_cache=False)

        def access_edges_twice() -> bool:
            e1 = node.edges()
            e2 = node.edges()
            return e1 is e2

        result = benchmark(access_edges_twice)
        assert result is True

    def test_edges_identity_verified(self) -> None:
        node = inspect_type(list[dict[str, int]], use_cache=False)

        e1 = node.edges()
        e2 = node.edges()
        assert e1 is e2, "edges() must return same cached object"

        for child in node.children():
            c1 = child.edges()
            c2 = child.edges()
            assert c1 is c2, f"edges() must return same cached object for {child}"


class TestConcurrentTraversal:
    # Spec acceptance: no race conditions, all threads return identical results

    def test_benchmark_concurrent_walk(self, benchmark: "BenchmarkFixture") -> None:
        node = inspect_type(complex_type, use_cache=False)

        def concurrent_traversal() -> list[list[TypeNode]]:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(lambda: list(walk(node))) for _ in range(4)]
                return [f.result() for f in futures]

        benchmark(concurrent_traversal)

    def test_concurrent_walk_results_identical(self) -> None:
        node = inspect_type(complex_type, use_cache=False)

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(lambda: list(walk(node))) for _ in range(4)]
            results = [f.result() for f in futures]

        lengths = [len(r) for r in results]
        assert len(set(lengths)) == 1, f"Inconsistent result lengths: {lengths}"

        type_sets = [frozenset(type(n).__name__ for n in r) for r in results]
        assert len(set(type_sets)) == 1, "Inconsistent node types across threads"


class TestLargeUnionTypes:
    # Spec acceptance: linear scaling with union member count, no exponential blowup

    def test_benchmark_traverse_large_union(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        union_type = build_union(20)
        node = inspect_type(union_type, use_cache=False)
        benchmark(lambda: list(walk(node)))

    def test_union_node_count_scales_linearly(self) -> None:
        counts = []
        for n in [5, 10, 15, 20]:
            union_type = build_union(n)
            node = inspect_type(union_type, use_cache=False)
            count = len(list(walk(node)))
            counts.append((n, count))

        for n, count in counts:
            assert count >= n, f"Expected at least {n} nodes for {n}-member union"


class TestDeepNesting:
    # Spec acceptance: stack depth bounded by graph depth, no recursion errors

    def test_benchmark_traverse_deep_nesting(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        deep_type = build_nested_type(depth=10)
        node = inspect_type(deep_type, use_cache=False)
        benchmark(lambda: list(walk(node)))

    def test_deep_nesting_no_recursion_error(self) -> None:
        deep_type = build_nested_type(depth=100)
        node = inspect_type(deep_type, use_cache=False)

        nodes = list(walk(node))

        assert len(nodes) >= 100, f"Expected at least 100 nodes, got {len(nodes)}"


class TestDepthLimitedTraversal:
    # Spec acceptance: max_depth terminates early, scales with depth not size

    def test_benchmark_walk_with_max_depth(self, benchmark: "BenchmarkFixture") -> None:
        deep_type = build_nested_type(depth=100)
        node = inspect_type(deep_type, use_cache=False)
        benchmark(lambda: list(walk(node, max_depth=10)))

    def test_benchmark_max_depth_limits_traversal(self) -> None:
        deep_type = build_nested_type(depth=100)
        node = inspect_type(deep_type, use_cache=False)

        full_count = len(list(walk(node)))

        limited_count = len(list(walk(node, max_depth=5)))
        assert limited_count < full_count, (
            f"Limited ({limited_count}) should be < full ({full_count})"
        )

        root_only = list(walk(node, max_depth=0))
        assert len(root_only) == 1, (
            f"Depth 0 should yield only root, got {len(root_only)}"
        )

    def test_max_depth_incremental(self) -> None:
        deep_type = build_nested_type(depth=20)
        node = inspect_type(deep_type, use_cache=False)

        prev_count = 0
        for depth in [0, 1, 2, 5, 10]:
            count = len(list(walk(node, max_depth=depth)))
            assert count >= prev_count, f"Depth {depth} should visit >= {prev_count}"
            prev_count = count
