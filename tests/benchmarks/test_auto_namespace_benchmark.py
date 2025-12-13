from typing import TYPE_CHECKING, Annotated

from typing_graph import (
    InspectConfig,
    inspect_dataclass,
    inspect_function,
    inspect_type,
)
from typing_graph._node import is_dataclass_node, is_function_node

from .conftest import (
    BenchmarkComplexDataclass,
    BenchmarkSimpleClass,
    benchmark_complex_function,
    benchmark_generic_function,
    benchmark_simple_function,
)

if TYPE_CHECKING:
    from pytest_benchmark.fixture import BenchmarkFixture


class TestClassInspectionOverhead:
    def test_simple_dataclass_baseline(
        self,
        benchmark: "BenchmarkFixture",
        benchmark_simple_class_type: type[BenchmarkSimpleClass],
    ) -> None:
        config = InspectConfig(auto_namespace=False)

        result = benchmark(
            inspect_dataclass, benchmark_simple_class_type, config=config
        )

        assert is_dataclass_node(result)
        assert len(result.fields) == 3

    def test_simple_dataclass_auto_namespace(
        self,
        benchmark: "BenchmarkFixture",
        benchmark_simple_class_type: type[BenchmarkSimpleClass],
    ) -> None:
        config = InspectConfig(auto_namespace=True)

        result = benchmark(
            inspect_dataclass, benchmark_simple_class_type, config=config
        )

        assert is_dataclass_node(result)
        assert len(result.fields) == 3

    def test_complex_dataclass_baseline(
        self,
        benchmark: "BenchmarkFixture",
        benchmark_complex_dataclass_type: type[BenchmarkComplexDataclass],
    ) -> None:
        config = InspectConfig(auto_namespace=False)

        result = benchmark(
            inspect_dataclass, benchmark_complex_dataclass_type, config=config
        )

        assert is_dataclass_node(result)
        assert len(result.fields) >= 15

    def test_complex_dataclass_auto_namespace(
        self,
        benchmark: "BenchmarkFixture",
        benchmark_complex_dataclass_type: type[BenchmarkComplexDataclass],
    ) -> None:
        config = InspectConfig(auto_namespace=True)

        result = benchmark(
            inspect_dataclass, benchmark_complex_dataclass_type, config=config
        )

        assert is_dataclass_node(result)
        assert len(result.fields) >= 15


class TestFunctionInspectionOverhead:
    def test_simple_function_baseline(self, benchmark: "BenchmarkFixture") -> None:
        config = InspectConfig(auto_namespace=False)

        result = benchmark(inspect_function, benchmark_simple_function, config=config)

        assert is_function_node(result)
        assert len(result.signature.parameters) == 2

    def test_simple_function_auto_namespace(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        config = InspectConfig(auto_namespace=True)

        result = benchmark(inspect_function, benchmark_simple_function, config=config)

        assert is_function_node(result)
        assert len(result.signature.parameters) == 2

    def test_complex_function_baseline(self, benchmark: "BenchmarkFixture") -> None:
        config = InspectConfig(auto_namespace=False)

        result = benchmark(inspect_function, benchmark_complex_function, config=config)

        assert is_function_node(result)
        assert len(result.signature.parameters) >= 4

    def test_complex_function_auto_namespace(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        config = InspectConfig(auto_namespace=True)

        result = benchmark(inspect_function, benchmark_complex_function, config=config)

        assert is_function_node(result)
        assert len(result.signature.parameters) >= 4

    def test_generic_function_baseline(self, benchmark: "BenchmarkFixture") -> None:
        config = InspectConfig(auto_namespace=False)

        result = benchmark(inspect_function, benchmark_generic_function, config=config)

        assert is_function_node(result)
        assert len(result.signature.parameters) >= 2

    def test_generic_function_auto_namespace(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        config = InspectConfig(auto_namespace=True)

        result = benchmark(inspect_function, benchmark_generic_function, config=config)

        assert is_function_node(result)
        assert len(result.signature.parameters) >= 2


class TestInspectTypeSourceOverhead:
    def test_simple_type_baseline(self, benchmark: "BenchmarkFixture") -> None:
        result = benchmark(inspect_type, int, use_cache=False)

        assert result is not None

    def test_simple_type_with_class_source(
        self,
        benchmark: "BenchmarkFixture",
        benchmark_simple_class_type: type[BenchmarkSimpleClass],
    ) -> None:
        result = benchmark(
            inspect_type, int, use_cache=False, source=benchmark_simple_class_type
        )

        assert result is not None

    def test_annotated_type_baseline(self, benchmark: "BenchmarkFixture") -> None:
        annotated_type = Annotated[int, "description", "validator"]

        result = benchmark(inspect_type, annotated_type, use_cache=False)

        assert result is not None
        assert len(result.metadata) == 2

    def test_annotated_type_with_class_source(
        self,
        benchmark: "BenchmarkFixture",
        benchmark_complex_dataclass_type: type[BenchmarkComplexDataclass],
    ) -> None:
        annotated_type = Annotated[int, "description", "validator"]

        result = benchmark(
            inspect_type,
            annotated_type,
            use_cache=False,
            source=benchmark_complex_dataclass_type,
        )

        assert result is not None
        assert len(result.metadata) == 2

    def test_generic_type_baseline(self, benchmark: "BenchmarkFixture") -> None:
        generic_type = dict[str, list[tuple[int, str]]]

        result = benchmark(inspect_type, generic_type, use_cache=False)

        assert result is not None

    def test_generic_type_with_function_source(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        generic_type = dict[str, list[tuple[int, str]]]

        result = benchmark(
            inspect_type,
            generic_type,
            use_cache=False,
            source=benchmark_complex_function,
        )

        assert result is not None

    def test_union_type_baseline(self, benchmark: "BenchmarkFixture") -> None:
        union_type = int | str | float | None

        result = benchmark(inspect_type, union_type, use_cache=False)

        assert result is not None

    def test_union_type_with_class_source(
        self,
        benchmark: "BenchmarkFixture",
        benchmark_complex_dataclass_type: type[BenchmarkComplexDataclass],
    ) -> None:
        union_type = int | str | float | None

        result = benchmark(
            inspect_type,
            union_type,
            use_cache=False,
            source=benchmark_complex_dataclass_type,
        )

        assert result is not None
