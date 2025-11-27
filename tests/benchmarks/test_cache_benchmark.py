from typing import TYPE_CHECKING

import pytest

from typing_graph import TypeNode, clear_cache, inspect_type
from typing_graph._inspect_type import _type_cache
from typing_graph._node import is_concrete_type, is_subscripted_generic_node

from .conftest import (
    build_nested_list,
    build_union,
)

if TYPE_CHECKING:
    from pytest_benchmark.fixture import BenchmarkFixture


class TestColdCacheBenchmarks:
    @pytest.fixture(autouse=True)
    def clear_cache_for_each_test(self) -> None:
        clear_cache()

    def test_benchmark_cold_cache_simple_type(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        def inspect_with_cold_cache() -> TypeNode:
            clear_cache()
            return inspect_type(int)

        result = benchmark(inspect_with_cold_cache)

        assert is_concrete_type(result)

    def test_benchmark_cold_cache_generic_type(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        def inspect_with_cold_cache() -> TypeNode:
            clear_cache()
            return inspect_type(list[int])

        result = benchmark(inspect_with_cold_cache)

        assert is_subscripted_generic_node(result)

    def test_benchmark_cold_cache_complex_type(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        complex_type = dict[str, list[tuple[int, str] | None]]

        def inspect_with_cold_cache() -> TypeNode:
            clear_cache()
            return inspect_type(complex_type)

        result = benchmark(inspect_with_cold_cache)

        assert is_subscripted_generic_node(result)


class TestWarmCacheBenchmarks:
    @pytest.fixture(autouse=True)
    def setup_warm_cache(self) -> None:
        clear_cache()
        # Pre-warm cache with common types
        for t in [int, str, float, bool, bytes, list, dict, set, tuple]:
            inspect_type(t)
        for t in [list[int], dict[str, int], set[str], tuple[int, ...]]:
            inspect_type(t)

    def test_benchmark_warm_cache_simple_type(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        # Ensure int is in cache
        inspect_type(int)

        result = benchmark(inspect_type, int)

        assert is_concrete_type(result)

    def test_benchmark_warm_cache_generic_type(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        # Ensure list[int] is in cache
        inspect_type(list[int])

        result = benchmark(inspect_type, list[int])

        assert is_subscripted_generic_node(result)

    def test_benchmark_warm_cache_repeated_inspection(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        # Inspect the same type multiple times
        complex_type = dict[str, list[int]]
        inspect_type(complex_type)

        result = benchmark(inspect_type, complex_type)

        assert is_subscripted_generic_node(result)


class TestCacheHitRateBenchmarks:
    @pytest.fixture(autouse=True)
    def clear_cache_for_each_test(self) -> None:
        clear_cache()

    def test_benchmark_100_percent_hit_rate(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        # Pre-populate cache
        types_to_inspect = [int, str, float, bool, bytes]
        for t in types_to_inspect:
            inspect_type(t)

        def inspect_cached_types() -> list[TypeNode]:
            return [inspect_type(t) for t in types_to_inspect]

        results = benchmark(inspect_cached_types)

        assert len(results) == 5
        assert all(is_concrete_type(r) for r in results)

    def test_benchmark_0_percent_hit_rate(self, benchmark: "BenchmarkFixture") -> None:
        def inspect_uncached_types() -> list[TypeNode]:
            clear_cache()
            types_to_inspect = [int, str, float, bool, bytes]
            return [inspect_type(t, use_cache=False) for t in types_to_inspect]

        results = benchmark(inspect_uncached_types)

        assert len(results) == 5
        assert all(is_concrete_type(r) for r in results)

    def test_benchmark_50_percent_hit_rate(self, benchmark: "BenchmarkFixture") -> None:
        # Pre-populate half the types
        cached_types = [int, str, float]
        for t in cached_types:
            inspect_type(t)

        def inspect_mixed_types() -> list[TypeNode]:
            # Half cached, half uncached
            all_types = [int, str, float, bool, bytes, list]
            return [inspect_type(t) for t in all_types]

        results = benchmark(inspect_mixed_types)

        assert len(results) == 6


class TestCacheDisabledBenchmarks:
    @pytest.fixture(autouse=True)
    def clear_cache_for_each_test(self) -> None:
        clear_cache()

    def test_benchmark_no_cache_simple_type(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        result = benchmark(inspect_type, int, use_cache=False)

        assert is_concrete_type(result)

    def test_benchmark_no_cache_generic_type(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        result = benchmark(inspect_type, list[int], use_cache=False)

        assert is_subscripted_generic_node(result)

    def test_benchmark_no_cache_complex_type(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        complex_type = dict[str, list[tuple[int, str] | None]]

        result = benchmark(inspect_type, complex_type, use_cache=False)

        assert is_subscripted_generic_node(result)

    def test_benchmark_no_cache_repeated_inspection(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        def inspect_repeatedly() -> list[TypeNode]:
            return [inspect_type(int, use_cache=False) for _ in range(10)]

        results = benchmark(inspect_repeatedly)

        assert len(results) == 10
        # Without cache, each result should be a different object
        assert len({id(r) for r in results}) == 10


class TestCacheVsNoCacheComparison:
    @pytest.fixture(autouse=True)
    def clear_cache_for_each_test(self) -> None:
        clear_cache()

    def test_benchmark_cached_nested_type(self, benchmark: "BenchmarkFixture") -> None:
        nested_type = build_nested_list(5)
        # Pre-warm cache
        inspect_type(nested_type)

        result = benchmark(inspect_type, nested_type)

        assert is_subscripted_generic_node(result)

    def test_benchmark_uncached_nested_type(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        nested_type = build_nested_list(5)

        result = benchmark(inspect_type, nested_type, use_cache=False)

        assert is_subscripted_generic_node(result)

    def test_benchmark_cached_union_type(self, benchmark: "BenchmarkFixture") -> None:
        union_type = build_union(5)
        # Pre-warm cache
        inspect_type(union_type)

        result = benchmark(inspect_type, union_type)

        assert result is not None

    def test_benchmark_uncached_union_type(self, benchmark: "BenchmarkFixture") -> None:
        union_type = build_union(5)

        result = benchmark(inspect_type, union_type, use_cache=False)

        assert result is not None


class TestCacheSizeImpact:
    @pytest.fixture(autouse=True)
    def clear_cache_for_each_test(self) -> None:
        clear_cache()

    def test_benchmark_lookup_small_cache(self, benchmark: "BenchmarkFixture") -> None:
        # Small cache: 10 entries
        for i in range(10):
            inspect_type(build_nested_list(i % 3 + 1))

        result = benchmark(inspect_type, int)

        assert is_concrete_type(result)

    def test_benchmark_lookup_medium_cache(self, benchmark: "BenchmarkFixture") -> None:
        # Medium cache: 100 entries
        for i in range(100):
            inspect_type(build_nested_list(i % 5 + 1))

        result = benchmark(inspect_type, int)

        assert is_concrete_type(result)

    def test_benchmark_lookup_large_cache(self, benchmark: "BenchmarkFixture") -> None:
        # Large cache: 500 entries
        for i in range(500):
            inspect_type(build_nested_list(i % 7 + 1))

        result = benchmark(inspect_type, int)

        assert is_concrete_type(result)


class TestCacheClearBenchmarks:
    def test_benchmark_clear_empty_cache(self, benchmark: "BenchmarkFixture") -> None:
        clear_cache()

        benchmark(clear_cache)

        assert len(_type_cache) == 0

    def test_benchmark_clear_small_cache(self, benchmark: "BenchmarkFixture") -> None:
        # Populate with 10 entries
        clear_cache()
        for t in [int, str, float, bool, bytes, list, dict, set, tuple, type]:
            inspect_type(t)

        benchmark(clear_cache)

        assert len(_type_cache) == 0

    def test_benchmark_clear_large_cache(self, benchmark: "BenchmarkFixture") -> None:
        # Populate with many entries
        clear_cache()
        for i in range(100):
            inspect_type(build_nested_list(i % 5 + 1))

        benchmark(clear_cache)

        assert len(_type_cache) == 0


class TestCacheMemoryEfficiency:
    @pytest.fixture(autouse=True)
    def clear_cache_for_each_test(self) -> None:
        clear_cache()

    def test_benchmark_inspect_same_type_identity(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        def inspect_same_type() -> tuple[TypeNode, TypeNode]:
            r1 = inspect_type(int)
            r2 = inspect_type(int)
            return r1, r2

        r1, r2 = benchmark(inspect_same_type)

        # Cache should return same object
        assert r1 is r2

    def test_benchmark_inspect_equivalent_types(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        # Use same type reference - cache keys on id(annotation), so
        # each `list[int]` evaluation creates a new GenericAlias with different id
        list_int = list[int]

        def inspect_equivalent_types() -> tuple[TypeNode, TypeNode]:
            r1 = inspect_type(list_int)
            r2 = inspect_type(list_int)
            return r1, r2

        r1, r2 = benchmark(inspect_equivalent_types)

        # Cache should return same object for same type reference
        assert r1 is r2
