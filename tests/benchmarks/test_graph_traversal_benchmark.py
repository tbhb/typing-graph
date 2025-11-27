from collections import deque
from collections.abc import Callable
from typing import TYPE_CHECKING, Annotated

import pytest

from typing_graph import inspect_type

from .conftest import (
    ComplexMapping,
    NestedGeneric,
    build_nested_dict,
    build_nested_list,
    build_union,
    count_nodes,
    max_depth,
)

if TYPE_CHECKING:
    from pytest_benchmark.fixture import BenchmarkFixture

    from typing_graph._node import TypeNode


def traverse_depth_first(node: "TypeNode") -> int:
    visited: set[int] = set()
    stack = [node]
    count = 0

    while stack:
        current = stack.pop()
        current_id = id(current)
        if current_id in visited:
            continue
        visited.add(current_id)
        count += 1
        stack.extend(current.children())

    return count


def traverse_breadth_first(node: "TypeNode") -> int:
    visited: set[int] = set()
    queue: deque[TypeNode] = deque([node])
    count = 0

    while queue:
        current = queue.popleft()
        current_id = id(current)
        if current_id in visited:
            continue
        visited.add(current_id)
        count += 1
        queue.extend(current.children())

    return count


def collect_all_nodes(node: "TypeNode") -> list["TypeNode"]:
    visited: set[int] = set()
    result: list[TypeNode] = []
    stack = [node]

    while stack:
        current = stack.pop()
        current_id = id(current)
        if current_id in visited:
            continue
        visited.add(current_id)
        result.append(current)
        stack.extend(current.children())

    return result


class TestShallowGraphBenchmarks:
    def test_benchmark_traverse_simple_type(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        node = inspect_type(int, use_cache=False)

        count = benchmark(traverse_depth_first, node)

        assert count == 1

    def test_benchmark_traverse_list_int(self, benchmark: "BenchmarkFixture") -> None:
        node = inspect_type(list[int], use_cache=False)

        count = benchmark(traverse_depth_first, node)

        assert count >= 2  # origin + arg

    def test_benchmark_traverse_dict_str_int(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        node = inspect_type(dict[str, int], use_cache=False)

        count = benchmark(traverse_depth_first, node)

        assert count >= 3  # origin + 2 args

    def test_benchmark_traverse_union_2(self, benchmark: "BenchmarkFixture") -> None:
        node = inspect_type(int | str, use_cache=False)

        count = benchmark(traverse_depth_first, node)

        assert count >= 3  # union + 2 members


class TestDeepGraphBenchmarks:
    @pytest.mark.parametrize("depth", [5, 7, 10])
    def test_benchmark_traverse_nested_list(
        self, benchmark: "BenchmarkFixture", depth: int
    ) -> None:
        nested_type = build_nested_list(depth)
        node = inspect_type(nested_type, use_cache=False)

        count = benchmark(traverse_depth_first, node)

        assert count >= depth + 1  # Each level has at least origin + arg

    @pytest.mark.parametrize("depth", [5, 7, 10])
    def test_benchmark_traverse_nested_dict(
        self, benchmark: "BenchmarkFixture", depth: int
    ) -> None:
        nested_type = build_nested_dict(depth)
        node = inspect_type(nested_type, use_cache=False)

        count = benchmark(traverse_depth_first, node)

        assert count >= depth + 1


class TestWideGraphBenchmarks:
    def test_benchmark_traverse_large_union(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        union_type = build_union(10)
        node = inspect_type(union_type, use_cache=False)

        count = benchmark(traverse_depth_first, node)

        assert count >= 10  # union + 10 members

    def test_benchmark_traverse_large_tuple(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        tuple_type = tuple[
            int, str, float, bool, bytes, list[int], dict[str, int], set[str], type
        ]
        node = inspect_type(tuple_type, use_cache=False)

        count = benchmark(traverse_depth_first, node)

        assert count >= 9

    def test_benchmark_traverse_callable_many_params(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        callable_type = Callable[
            [int, str, float, bool, bytes, list[int], dict[str, int], set[str]],
            tuple[int, str],
        ]
        node = inspect_type(callable_type, use_cache=False)

        count = benchmark(traverse_depth_first, node)

        assert count >= 10

    def test_benchmark_traverse_annotated_many_metadata(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        annotated_type = Annotated[
            dict[str, list[int]],
            "meta1",
            "meta2",
            "meta3",
            "meta4",
            "meta5",
        ]
        node = inspect_type(annotated_type, use_cache=False)

        count = benchmark(traverse_depth_first, node)

        assert count >= 3  # dict + str + list + int


class TestGraphMetricsBenchmarks:
    def test_benchmark_count_nodes_simple(self, benchmark: "BenchmarkFixture") -> None:
        node = inspect_type(list[int], use_cache=False)

        count = benchmark(count_nodes, node)

        assert count >= 2

    def test_benchmark_count_nodes_complex(self, benchmark: "BenchmarkFixture") -> None:
        complex_type = dict[str, list[tuple[int, str] | None]]
        node = inspect_type(complex_type, use_cache=False)

        count = benchmark(count_nodes, node)

        assert count >= 5

    def test_benchmark_max_depth_shallow(self, benchmark: "BenchmarkFixture") -> None:
        node = inspect_type(list[int], use_cache=False)

        depth = benchmark(max_depth, node)

        assert depth >= 2

    def test_benchmark_max_depth_deep(self, benchmark: "BenchmarkFixture") -> None:
        nested_type = build_nested_list(10)
        node = inspect_type(nested_type, use_cache=False)

        depth = benchmark(max_depth, node)

        assert depth >= 10


class TestTraversalMethodBenchmarks:
    def test_benchmark_dfs_complex_type(self, benchmark: "BenchmarkFixture") -> None:
        complex_type = dict[str, list[tuple[int, str, float] | None]]
        node = inspect_type(complex_type, use_cache=False)

        count = benchmark(traverse_depth_first, node)

        assert count >= 5

    def test_benchmark_bfs_complex_type(self, benchmark: "BenchmarkFixture") -> None:
        complex_type = dict[str, list[tuple[int, str, float] | None]]
        node = inspect_type(complex_type, use_cache=False)

        count = benchmark(traverse_breadth_first, node)

        assert count >= 5

    def test_benchmark_collect_all_nodes(self, benchmark: "BenchmarkFixture") -> None:
        complex_type = dict[str, list[tuple[int, str] | None]]
        node = inspect_type(complex_type, use_cache=False)

        nodes = benchmark(collect_all_nodes, node)

        assert len(nodes) >= 5


class TestRealisticGraphBenchmarks:
    def test_benchmark_traverse_api_response(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        # Typical REST API response structure
        response_type = dict[
            str,
            list[
                dict[
                    str,
                    int | str | float | bool | None,
                ]
            ]
            | None,
        ]
        node = inspect_type(response_type, use_cache=False)

        count = benchmark(traverse_depth_first, node)

        assert count >= 5

    def test_benchmark_traverse_callback_signature(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        # Complex callback type
        callback_type = Callable[
            [
                dict[str, str | int | bool],
                list[tuple[str, int]],
                Callable[[str], bool] | None,
            ],
            dict[str, list[int]] | None,
        ]
        node = inspect_type(callback_type, use_cache=False)

        count = benchmark(traverse_depth_first, node)

        assert count >= 5

    def test_benchmark_traverse_complex_mapping(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        node = inspect_type(ComplexMapping, use_cache=False)

        count = benchmark(traverse_depth_first, node)

        assert count >= 4

    def test_benchmark_traverse_nested_generic(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        node = inspect_type(NestedGeneric, use_cache=False)

        count = benchmark(traverse_depth_first, node)

        assert count >= 4


class TestGraphSizeBenchmarks:
    @pytest.mark.parametrize("depth", [1, 3, 5, 7, 10])
    def test_benchmark_traverse_scaling_by_depth(
        self, benchmark: "BenchmarkFixture", depth: int
    ) -> None:
        nested_type = build_nested_list(depth)
        node = inspect_type(nested_type, use_cache=False)

        count = benchmark(traverse_depth_first, node)

        # Verify graph was traversed
        assert count >= depth

    @pytest.mark.parametrize("width", [2, 4, 6, 8, 10])
    def test_benchmark_traverse_scaling_by_width(
        self, benchmark: "BenchmarkFixture", width: int
    ) -> None:
        union_type = build_union(width)
        node = inspect_type(union_type, use_cache=False)

        count = benchmark(traverse_depth_first, node)

        # Verify graph was traversed
        assert count >= width
