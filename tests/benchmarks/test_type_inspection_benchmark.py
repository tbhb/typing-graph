from collections.abc import Callable
from typing import TYPE_CHECKING, Annotated, Any, Literal, ParamSpec, TypeVar

import pytest

from typing_graph import inspect_type
from typing_graph._node import (
    is_any_type_node,
    is_callable_type_node,
    is_concrete_type,
    is_literal_node,
    is_param_spec_node,
    is_subscripted_generic_node,
    is_tuple_type_node,
    is_type_var_node,
    is_union_type_node,
)

from .conftest import build_annotated, build_nested_dict, build_nested_list, build_union

if TYPE_CHECKING:
    from pytest_benchmark.fixture import BenchmarkFixture


class TestSimpleTypeBenchmarks:
    def test_benchmark_int(self, benchmark: "BenchmarkFixture") -> None:
        result = benchmark(inspect_type, int, use_cache=False)

        assert is_concrete_type(result)
        assert result.cls is int

    def test_benchmark_str(self, benchmark: "BenchmarkFixture") -> None:
        result = benchmark(inspect_type, str, use_cache=False)

        assert is_concrete_type(result)
        assert result.cls is str

    def test_benchmark_float(self, benchmark: "BenchmarkFixture") -> None:
        result = benchmark(inspect_type, float, use_cache=False)

        assert is_concrete_type(result)
        assert result.cls is float

    def test_benchmark_bool(self, benchmark: "BenchmarkFixture") -> None:
        result = benchmark(inspect_type, bool, use_cache=False)

        assert is_concrete_type(result)
        assert result.cls is bool

    def test_benchmark_bytes(self, benchmark: "BenchmarkFixture") -> None:
        result = benchmark(inspect_type, bytes, use_cache=False)

        assert is_concrete_type(result)
        assert result.cls is bytes

    def test_benchmark_none(self, benchmark: "BenchmarkFixture") -> None:
        result = benchmark(inspect_type, None, use_cache=False)

        assert is_concrete_type(result)
        assert result.cls is type(None)

    def test_benchmark_any(self, benchmark: "BenchmarkFixture") -> None:
        result = benchmark(inspect_type, Any, use_cache=False)

        assert is_any_type_node(result)


class TestAnnotatedTypeBenchmarks:
    def test_benchmark_annotated_1_metadata(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        annotated_type = build_annotated(1)

        result = benchmark(inspect_type, annotated_type, use_cache=False)

        assert is_concrete_type(result)
        assert len(result.metadata) == 1

    def test_benchmark_annotated_3_metadata(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        annotated_type = build_annotated(3)

        result = benchmark(inspect_type, annotated_type, use_cache=False)

        assert is_concrete_type(result)
        assert len(result.metadata) == 3

    def test_benchmark_annotated_5_metadata(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        annotated_type = build_annotated(5)

        result = benchmark(inspect_type, annotated_type, use_cache=False)

        assert is_concrete_type(result)
        assert len(result.metadata) == 5

    def test_benchmark_annotated_10_metadata(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        annotated_type = build_annotated(10)

        result = benchmark(inspect_type, annotated_type, use_cache=False)

        assert is_concrete_type(result)
        assert len(result.metadata) == 10


class TestNestedGenericBenchmarks:
    @pytest.mark.parametrize("depth", [1, 2, 3, 5, 10])
    def test_benchmark_nested_list(
        self, benchmark: "BenchmarkFixture", depth: int
    ) -> None:
        nested_type = build_nested_list(depth)

        result = benchmark(inspect_type, nested_type, use_cache=False)

        assert is_subscripted_generic_node(result)

    @pytest.mark.parametrize("depth", [1, 2, 3, 5, 10])
    def test_benchmark_nested_dict(
        self, benchmark: "BenchmarkFixture", depth: int
    ) -> None:
        nested_type = build_nested_dict(depth)

        result = benchmark(inspect_type, nested_type, use_cache=False)

        assert is_subscripted_generic_node(result)

    def test_benchmark_complex_nested_generic(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        # list[dict[str, list[tuple[int, str]]]]
        complex_type = list[dict[str, list[tuple[int, str]]]]

        result = benchmark(inspect_type, complex_type, use_cache=False)

        assert is_subscripted_generic_node(result)


class TestUnionTypeBenchmarks:
    def test_benchmark_union_2(self, benchmark: "BenchmarkFixture") -> None:
        union_type = int | str

        result = benchmark(inspect_type, union_type, use_cache=False)

        assert is_union_type_node(result)
        assert len(result.members) == 2

    def test_benchmark_union_3(self, benchmark: "BenchmarkFixture") -> None:
        union_type = int | str | float

        result = benchmark(inspect_type, union_type, use_cache=False)

        assert is_union_type_node(result)
        assert len(result.members) == 3

    def test_benchmark_union_5(self, benchmark: "BenchmarkFixture") -> None:
        union_type = build_union(5)

        result = benchmark(inspect_type, union_type, use_cache=False)

        assert is_union_type_node(result)
        assert len(result.members) == 5

    def test_benchmark_union_10(self, benchmark: "BenchmarkFixture") -> None:
        union_type = build_union(10)

        result = benchmark(inspect_type, union_type, use_cache=False)

        assert is_union_type_node(result)
        assert len(result.members) == 10

    def test_benchmark_optional_type(self, benchmark: "BenchmarkFixture") -> None:
        optional_type = int | None

        result = benchmark(inspect_type, optional_type, use_cache=False)

        assert is_union_type_node(result)
        assert len(result.members) == 2


class TestTupleTypeBenchmarks:
    def test_benchmark_homogeneous_tuple(self, benchmark: "BenchmarkFixture") -> None:
        tuple_type = tuple[int, ...]

        result = benchmark(inspect_type, tuple_type, use_cache=False)

        assert is_tuple_type_node(result)
        assert result.homogeneous is True

    def test_benchmark_heterogeneous_tuple_2(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        tuple_type = tuple[int, str]

        result = benchmark(inspect_type, tuple_type, use_cache=False)

        assert is_tuple_type_node(result)
        assert result.homogeneous is False
        assert len(result.elements) == 2

    def test_benchmark_heterogeneous_tuple_5(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        tuple_type = tuple[int, str, float, bool, bytes]

        result = benchmark(inspect_type, tuple_type, use_cache=False)

        assert is_tuple_type_node(result)
        assert result.homogeneous is False
        assert len(result.elements) == 5

    def test_benchmark_empty_tuple(self, benchmark: "BenchmarkFixture") -> None:
        tuple_type = tuple[()]

        result = benchmark(inspect_type, tuple_type, use_cache=False)

        assert is_tuple_type_node(result)
        assert result.elements == ()


class TestCallableTypeBenchmarks:
    def test_benchmark_simple_callable(self, benchmark: "BenchmarkFixture") -> None:
        callable_type = Callable[[int], str]

        result = benchmark(inspect_type, callable_type, use_cache=False)

        assert is_callable_type_node(result)

    def test_benchmark_multi_param_callable(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        callable_type = Callable[[int, str, float, bool], bytes]

        result = benchmark(inspect_type, callable_type, use_cache=False)

        assert is_callable_type_node(result)
        assert isinstance(result.params, tuple)
        assert len(result.params) == 4

    def test_benchmark_no_param_callable(self, benchmark: "BenchmarkFixture") -> None:
        callable_type = Callable[[], int]

        result = benchmark(inspect_type, callable_type, use_cache=False)

        assert is_callable_type_node(result)
        assert isinstance(result.params, tuple)
        assert len(result.params) == 0

    def test_benchmark_ellipsis_callable(self, benchmark: "BenchmarkFixture") -> None:
        callable_type = Callable[..., int]

        result = benchmark(inspect_type, callable_type, use_cache=False)

        assert is_callable_type_node(result)


class TestLiteralTypeBenchmarks:
    def test_benchmark_literal_single(self, benchmark: "BenchmarkFixture") -> None:
        literal_type = Literal["value"]

        result = benchmark(inspect_type, literal_type, use_cache=False)

        assert is_literal_node(result)
        assert len(result.values) == 1

    def test_benchmark_literal_multiple(self, benchmark: "BenchmarkFixture") -> None:
        literal_type = Literal["a", "b", "c", "d", "e"]

        result = benchmark(inspect_type, literal_type, use_cache=False)

        assert is_literal_node(result)
        assert len(result.values) == 5

    def test_benchmark_literal_int_values(self, benchmark: "BenchmarkFixture") -> None:
        literal_type = Literal[1, 2, 3, 4, 5]

        result = benchmark(inspect_type, literal_type, use_cache=False)

        assert is_literal_node(result)
        assert len(result.values) == 5


class TestTypeVarBenchmarks:
    def test_benchmark_simple_typevar(self, benchmark: "BenchmarkFixture") -> None:
        T = TypeVar("T")

        result = benchmark(inspect_type, T, use_cache=False)

        assert is_type_var_node(result)
        assert result.name == "T"

    def test_benchmark_bound_typevar(self, benchmark: "BenchmarkFixture") -> None:
        T = TypeVar("T", bound=int)

        result = benchmark(inspect_type, T, use_cache=False)

        assert is_type_var_node(result)
        assert result.bound is not None

    def test_benchmark_constrained_typevar(self, benchmark: "BenchmarkFixture") -> None:
        T = TypeVar("T", int, str, float)

        result = benchmark(inspect_type, T, use_cache=False)

        assert is_type_var_node(result)
        assert len(result.constraints) == 3

    def test_benchmark_paramspec(self, benchmark: "BenchmarkFixture") -> None:
        P = ParamSpec("P")  # noqa: N806 - type parameter naming convention

        result = benchmark(inspect_type, P, use_cache=False)

        assert is_param_spec_node(result)
        assert result.name == "P"


class TestInspectorDispatchBenchmarks:
    def test_benchmark_early_dispatch_none(self, benchmark: "BenchmarkFixture") -> None:
        # None is checked first in the inspector chain
        result = benchmark(inspect_type, None, use_cache=False)

        assert is_concrete_type(result)
        assert result.cls is type(None)

    def test_benchmark_late_dispatch_plain_class(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        # Plain classes are checked last in the inspector chain
        class CustomClass:
            pass

        result = benchmark(inspect_type, CustomClass, use_cache=False)

        assert is_concrete_type(result)
        assert result.cls is CustomClass

    def test_benchmark_mid_dispatch_subscripted_generic(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        # Subscripted generics are in the middle of the chain
        result = benchmark(inspect_type, list[int], use_cache=False)

        assert is_subscripted_generic_node(result)


class TestComplexTypeBenchmarks:
    def test_benchmark_response_type(self, benchmark: "BenchmarkFixture") -> None:
        # Typical API response type
        response_type = dict[str, list[dict[str, int | str | None]]]

        result = benchmark(inspect_type, response_type, use_cache=False)

        assert is_subscripted_generic_node(result)

    def test_benchmark_callback_type(self, benchmark: "BenchmarkFixture") -> None:
        # Typical callback type
        callback_type = Callable[[str, dict[str, str | int]], list[int] | None]

        result = benchmark(inspect_type, callback_type, use_cache=False)

        assert is_callable_type_node(result)

    def test_benchmark_annotated_complex(self, benchmark: "BenchmarkFixture") -> None:
        # Annotated complex type
        annotated_type = Annotated[
            dict[str, list[int]],
            "description",
            "validator",
            "constraint",
        ]

        result = benchmark(inspect_type, annotated_type, use_cache=False)

        assert is_subscripted_generic_node(result)
        assert len(result.metadata) == 3

    def test_benchmark_union_of_generics(self, benchmark: "BenchmarkFixture") -> None:
        # Union of generic types
        union_type = list[int] | dict[str, int] | set[str] | None

        result = benchmark(inspect_type, union_type, use_cache=False)

        assert is_union_type_node(result)
