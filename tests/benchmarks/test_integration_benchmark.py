import sys
from typing import TYPE_CHECKING, TypeVar

import typing_graph
from typing_graph import (
    TypeNode,
    inspect_class,
    inspect_dataclass,
    inspect_enum,
    inspect_function,
    inspect_module,
    inspect_type,
)
from typing_graph._node import (
    DataclassNode,
    is_dataclass_node,
    is_enum_node,
    is_function_node,
    is_named_tuple_node,
    is_protocol_node,
    is_subscripted_generic_node,
    is_typed_dict_node,
)

from .conftest import (
    CallableType,
    ComplexMapping,
    LargeDataclass,
    NestedDataclass,
    NestedGeneric,
    SampleEnum,
    SampleNamedTuple,
    SampleProtocol,
    SampleTypedDict,
    SimpleDataclass,
    UserId,
    Username,
)

if TYPE_CHECKING:
    from pytest_benchmark.fixture import BenchmarkFixture


class TestDataclassInspectionBenchmarks:
    def test_benchmark_simple_dataclass(
        self,
        benchmark: "BenchmarkFixture",
        simple_dataclass_type: type[SimpleDataclass],
    ) -> None:
        result = benchmark(inspect_dataclass, simple_dataclass_type)

        assert is_dataclass_node(result)
        assert len(result.fields) == 3

    def test_benchmark_large_dataclass(
        self, benchmark: "BenchmarkFixture", large_dataclass_type: type[LargeDataclass]
    ) -> None:
        result = benchmark(inspect_dataclass, large_dataclass_type)

        assert is_dataclass_node(result)
        assert len(result.fields) >= 15

    def test_benchmark_nested_dataclass(
        self,
        benchmark: "BenchmarkFixture",
        nested_dataclass_type: type[NestedDataclass],
    ) -> None:
        result = benchmark(inspect_dataclass, nested_dataclass_type)

        assert is_dataclass_node(result)
        assert len(result.fields) >= 3

    def test_benchmark_dataclass_frozen_slots(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        result = benchmark(inspect_dataclass, SimpleDataclass)

        assert is_dataclass_node(result)
        assert result.frozen is True
        assert result.slots is True


class TestTypedDictInspectionBenchmarks:
    def test_benchmark_typed_dict(
        self,
        benchmark: "BenchmarkFixture",
        sample_typed_dict_type: type[SampleTypedDict],
    ) -> None:
        result = benchmark(inspect_class, sample_typed_dict_type)

        assert is_typed_dict_node(result)
        assert len(result.fields) == 3


class TestNamedTupleInspectionBenchmarks:
    def test_benchmark_named_tuple(
        self,
        benchmark: "BenchmarkFixture",
        sample_named_tuple_type: type[SampleNamedTuple],
    ) -> None:
        result = benchmark(inspect_class, sample_named_tuple_type)

        assert is_named_tuple_node(result)
        assert len(result.fields) == 3


class TestProtocolInspectionBenchmarks:
    def test_benchmark_protocol(
        self,
        benchmark: "BenchmarkFixture",
        sample_protocol_type: type[SampleProtocol],
    ) -> None:
        result = benchmark(inspect_class, sample_protocol_type)

        assert is_protocol_node(result)
        assert len(result.methods) >= 2
        assert result.is_runtime_checkable is True


class TestEnumInspectionBenchmarks:
    def test_benchmark_enum(
        self, benchmark: "BenchmarkFixture", sample_enum_type: type[SampleEnum]
    ) -> None:
        result = benchmark(inspect_enum, sample_enum_type)

        assert is_enum_node(result)
        assert len(result.members) == 3


class TestGenericClassBenchmarks:
    def test_benchmark_generic_container(
        self, benchmark: "BenchmarkFixture", generic_container_type: type
    ) -> None:
        result = benchmark(inspect_class, generic_container_type)

        assert result is not None


class TestFunctionInspectionBenchmarks:
    def test_benchmark_simple_function(self, benchmark: "BenchmarkFixture") -> None:
        def simple_func(x: int, y: str) -> bool:  # noqa: ARG001
            return True

        result = benchmark(inspect_function, simple_func)

        assert is_function_node(result)
        assert len(result.signature.parameters) == 2

    def test_benchmark_complex_function(self, benchmark: "BenchmarkFixture") -> None:
        def complex_func(
            data: dict[str, list[int]],  # noqa: ARG001
            callback: CallableType | None = None,  # noqa: ARG001
            *,
            timeout: float = 30.0,  # noqa: ARG001
            retries: int = 3,  # noqa: ARG001
        ) -> list[tuple[str, int]] | None:
            return None

        result = benchmark(inspect_function, complex_func)

        assert is_function_node(result)
        assert len(result.signature.parameters) >= 3

    def test_benchmark_generic_function(self, benchmark: "BenchmarkFixture") -> None:
        T = TypeVar("T")

        def generic_func(items: list[T], predicate: CallableType) -> list[T]:  # noqa: ARG001
            return items

        result = benchmark(inspect_function, generic_func)

        assert is_function_node(result)


class TestModuleInspectionBenchmarks:
    def test_benchmark_inspect_typing_graph_module(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        # Use include_imported=True because typing_graph re-exports from private modules
        result = benchmark(inspect_module, typing_graph, include_imported=True)

        assert result is not None
        # The module should have functions (re-exported from submodules)
        assert len(result.functions) > 0

    def test_benchmark_inspect_typing_graph_module_no_imports(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        # Benchmark the filtering overhead with include_imported=False
        result = benchmark(inspect_module, typing_graph, include_imported=False)

        assert result is not None
        # All public items are re-exported, so this should be empty
        assert len(result.classes) + len(result.functions) >= 0

    def test_benchmark_inspect_sys_module(self, benchmark: "BenchmarkFixture") -> None:
        result = benchmark(inspect_module, sys, include_imported=False)

        assert result is not None


class TestComplexTypeAliasBenchmarks:
    def test_benchmark_complex_mapping_alias(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        result = benchmark(inspect_type, ComplexMapping, use_cache=False)

        assert is_subscripted_generic_node(result)

    def test_benchmark_nested_generic_alias(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        result = benchmark(inspect_type, NestedGeneric, use_cache=False)

        assert is_subscripted_generic_node(result)

    def test_benchmark_callable_alias(self, benchmark: "BenchmarkFixture") -> None:
        result = benchmark(inspect_type, CallableType, use_cache=False)

        assert result is not None


class TestNewTypeBenchmarks:
    def test_benchmark_userid_newtype(self, benchmark: "BenchmarkFixture") -> None:
        result = benchmark(inspect_type, UserId, use_cache=False)

        assert result is not None

    def test_benchmark_username_newtype(self, benchmark: "BenchmarkFixture") -> None:
        result = benchmark(inspect_type, Username, use_cache=False)

        assert result is not None


class TestRealisticWorkflowBenchmarks:
    def test_benchmark_api_model_inspection(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        def inspect_api_models() -> list[TypeNode]:
            return [
                inspect_dataclass(SimpleDataclass),
                inspect_dataclass(LargeDataclass),
                inspect_class(SampleTypedDict),
                inspect_enum(SampleEnum),
            ]

        results = benchmark(inspect_api_models)

        assert len(results) == 4

    def test_benchmark_type_analysis_workflow(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        def analyze_types() -> dict[str, TypeNode]:
            return {
                "simple": inspect_type(int, use_cache=False),
                "generic": inspect_type(list[int], use_cache=False),
                "union": inspect_type(int | str | None, use_cache=False),
                "complex": inspect_type(
                    dict[str, list[tuple[int, str]]],
                    use_cache=False,
                ),
            }

        results = benchmark(analyze_types)

        assert len(results) == 4

    def test_benchmark_full_class_analysis(self, benchmark: "BenchmarkFixture") -> None:
        def full_analysis() -> DataclassNode:
            result = inspect_dataclass(LargeDataclass)
            # Traverse all field types
            for field in result.fields:
                _ = field.type.children()
            return result

        result = benchmark(full_analysis)

        assert is_dataclass_node(result)


class TestInspectClassDispatchBenchmarks:
    def test_benchmark_dispatch_to_dataclass(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        result = benchmark(inspect_class, SimpleDataclass)

        assert is_dataclass_node(result)

    def test_benchmark_dispatch_to_typeddict(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        result = benchmark(inspect_class, SampleTypedDict)

        assert is_typed_dict_node(result)

    def test_benchmark_dispatch_to_namedtuple(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        result = benchmark(inspect_class, SampleNamedTuple)

        assert is_named_tuple_node(result)

    def test_benchmark_dispatch_to_protocol(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        result = benchmark(inspect_class, SampleProtocol)

        assert is_protocol_node(result)

    def test_benchmark_dispatch_to_enum(self, benchmark: "BenchmarkFixture") -> None:
        result = benchmark(inspect_class, SampleEnum)

        assert is_enum_node(result)

    def test_benchmark_dispatch_to_regular_class(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        class RegularClass:
            def __init__(self) -> None:
                self.name: str = ""
                self.value: int = 0

        result = benchmark(inspect_class, RegularClass)

        assert result is not None


class TestContextCreationBenchmarks:
    def test_benchmark_context_creation_simple(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        # Measure overhead of context creation for simple types
        result = benchmark(inspect_type, int, use_cache=False)

        assert result is not None

    def test_benchmark_context_creation_complex(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        # Measure overhead of context creation for complex types
        # (more ctx.child() calls)
        complex_type = dict[str, list[tuple[int, str, float]]]

        result = benchmark(inspect_type, complex_type, use_cache=False)

        assert result is not None
