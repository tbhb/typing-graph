from typing import Annotated

import pytest

from typing_graph import ConcreteNode, InspectConfig, MetadataCollection, inspect_type
from typing_graph._context import (
    InspectContext,
    extract_field_metadata,
    get_source_location,
)
from typing_graph._node import (
    AnnotatedNode,
)


@pytest.fixture
def config() -> InspectConfig:
    return InspectConfig()


class TestInspectContext:
    def test_child_increments_depth(self, config: InspectConfig) -> None:
        ctx = InspectContext(config=config)
        child = ctx.child()
        assert child.depth == 1
        assert child.config is ctx.config

    def test_child_shares_seen(self, config: InspectConfig) -> None:
        ctx = InspectContext(config=config)
        dummy_node = ConcreteNode(cls=int)
        ctx.seen[123] = dummy_node
        child = ctx.child()
        assert child.seen is ctx.seen
        assert 123 in child.seen

    def test_child_shares_resolving(self, config: InspectConfig) -> None:
        ctx = InspectContext(config=config)
        ctx.resolving.add("SomeType")
        child = ctx.child()
        assert child.resolving is ctx.resolving
        assert "SomeType" in child.resolving

    def test_unlimited_depth_allows_recursion(self) -> None:
        config = InspectConfig(max_depth=None)
        ctx = InspectContext(config=config)
        assert ctx.check_max_depth_exceeded() is True

    def test_depth_below_limit_allows_recursion(self) -> None:
        config = InspectConfig(max_depth=5)
        ctx = InspectContext(config=config, depth=3)
        assert ctx.check_max_depth_exceeded() is True

    def test_depth_at_limit_blocks_recursion(self) -> None:
        config = InspectConfig(max_depth=5)
        ctx = InspectContext(config=config, depth=5)
        assert ctx.check_max_depth_exceeded() is False

    def test_depth_exceeding_limit_blocks_recursion(self) -> None:
        config = InspectConfig(max_depth=5)
        ctx = InspectContext(config=config, depth=10)
        assert ctx.check_max_depth_exceeded() is False

    def test_nested_children_increment_depth(self) -> None:
        config = InspectConfig(max_depth=3)
        ctx = InspectContext(config=config)
        assert ctx.depth == 0
        assert ctx.check_max_depth_exceeded() is True

        child1 = ctx.child()
        assert child1.depth == 1
        assert child1.check_max_depth_exceeded() is True

        child2 = child1.child()
        assert child2.depth == 2
        assert child2.check_max_depth_exceeded() is True

        child3 = child2.child()
        assert child3.depth == 3
        assert child3.check_max_depth_exceeded() is False


class TestExtractFieldMetadata:
    def test_returns_annotations_for_annotated_type_node(self) -> None:
        # Create an AnnotatedNode directly
        # (inspect_type hoists metadata to ConcreteNode)
        node = AnnotatedNode(
            base=ConcreteNode(cls=int),
            annotations=("meta1", "meta2"),
        )

        result = extract_field_metadata(node)

        # AnnotatedNode stores metadata in annotations field
        assert list(result) == ["meta1", "meta2"]

    def test_returns_metadata_for_annotated_via_inspect_type(self) -> None:
        # inspect_type returns ConcreteNode with hoisted metadata
        node = inspect_type(Annotated[int, "meta1", "meta2"])

        result = extract_field_metadata(node)

        # Metadata is hoisted to the ConcreteNode's metadata field
        assert list(result) == ["meta1", "meta2"]

    def test_returns_metadata_for_concrete_type(self) -> None:
        node = ConcreteNode(cls=int, metadata=MetadataCollection.of(["meta"]))

        result = extract_field_metadata(node)

        assert list(result) == ["meta"]

    def test_returns_empty_collection_for_no_metadata(self) -> None:
        node = ConcreteNode(cls=int)

        result = extract_field_metadata(node)

        assert len(result) == 0
        assert result is MetadataCollection.EMPTY


class TestGetSourceLocation:
    def test_returns_none_when_disabled(self) -> None:
        config = InspectConfig(include_source_locations=False)

        def sample_func() -> None:
            pass

        result = get_source_location(sample_func, config)

        assert result is None

    def test_returns_location_when_enabled_for_function(self) -> None:
        config = InspectConfig(include_source_locations=True)

        def sample_func() -> None:
            pass

        result = get_source_location(sample_func, config)

        assert result is not None
        assert result.module is not None
        expected_qualname = (
            "TestGetSourceLocation"
            ".test_returns_location_when_enabled_for_function"
            ".<locals>.sample_func"
        )
        assert result.qualname == expected_qualname
        assert result.file is not None
        assert result.lineno is not None

    def test_returns_location_for_class(self) -> None:
        config = InspectConfig(include_source_locations=True)

        class SampleClass:
            pass

        result = get_source_location(SampleClass, config)

        assert result is not None
        expected_qualname = (
            "TestGetSourceLocation.test_returns_location_for_class.<locals>.SampleClass"
        )
        assert result.qualname == expected_qualname

    def test_handles_object_without_source(self) -> None:
        config = InspectConfig(include_source_locations=True)

        # Built-in types don't have source
        result = get_source_location(int, config)

        # Should still return module and qualname even without file/line
        assert result is not None
        assert result.module == "builtins"
        assert result.qualname == "int"
        # file and lineno may be None for builtins

    def test_returns_none_for_object_with_no_info(self) -> None:
        config = InspectConfig(include_source_locations=True)

        # Lambda without any useful source info
        obj = 42  # An int literal has no module, qualname, file, or lineno

        result = get_source_location(obj, config)

        # 42 has no useful source location attributes
        assert result is None
