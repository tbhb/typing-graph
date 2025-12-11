# ruff: noqa: UP007, UP045, PYI030
# pyright: reportAny=false, reportDeprecated=false
# These tests intentionally use Union, Optional, and Literal unions
# to verify both old and new syntax representations work correctly.

import sys
from typing import Annotated, ClassVar, Final, Literal, Optional, Union

import pytest

from typing_graph import (
    InspectConfig,
    get_union_members,
    inspect_type,
    is_concrete_node,
    is_optional_node,
    is_union_node,
    unwrap_optional,
)
from typing_graph._node import (
    is_generic_node,
    is_literal_node,
    is_subscripted_generic_node,
    is_union_type_node,
)


class TestBasicNormalization:
    def test_typing_union_normalizes_to_union_node_by_default(self) -> None:
        result = inspect_type(Union[int, str])

        assert is_union_type_node(result)
        assert len(result.members) == 2
        member_classes = {m.cls for m in result.members if is_concrete_node(m)}
        assert member_classes == {int, str}

    def test_typing_union_with_three_types_normalizes(self) -> None:
        result = inspect_type(Union[int, str, float])

        assert is_union_type_node(result)
        assert len(result.members) == 3
        member_classes = {m.cls for m in result.members if is_concrete_node(m)}
        assert member_classes == {int, str, float}

    def test_typing_union_with_four_types_normalizes(self) -> None:
        result = inspect_type(Union[int, str, float, bool])

        assert is_union_type_node(result)
        assert len(result.members) == 4

    def test_native_union_produces_union_node(self) -> None:
        result = inspect_type(int | str)

        assert is_union_type_node(result)
        assert len(result.members) == 2

    def test_default_config_has_normalize_unions_true(self) -> None:
        config = InspectConfig()

        assert config.normalize_unions is True


class TestLiteralUnionNormalization:
    def test_literal_union_produced_by_pipe_normalizes(self) -> None:
        lit_union = Literal["a"] | Literal["b"]
        result = inspect_type(lit_union)

        assert is_union_type_node(result)
        assert len(result.members) == 2

    def test_literal_union_members_are_literal_nodes(self) -> None:
        lit_union = Literal["a"] | Literal["b"]
        result = inspect_type(lit_union)

        assert is_union_type_node(result)
        for member in result.members:
            assert is_literal_node(member)

    def test_literal_union_with_three_values(self) -> None:
        lit_union = Literal["a"] | Literal["b"] | Literal["c"]
        result = inspect_type(lit_union)

        assert is_union_type_node(result)
        assert len(result.members) == 3


class TestOptionalNormalization:
    def test_optional_normalizes_to_union_node_by_default(self) -> None:
        result = inspect_type(Optional[int])

        assert is_union_type_node(result)
        assert len(result.members) == 2
        member_classes = {m.cls for m in result.members if is_concrete_node(m)}
        assert int in member_classes
        assert type(None) in member_classes

    def test_optional_with_complex_type_normalizes(self) -> None:
        result = inspect_type(Optional[list[int]])

        assert is_union_type_node(result)
        assert len(result.members) == 2
        has_list = any(
            is_subscripted_generic_node(m)
            and is_generic_node(m.origin)
            and m.origin.cls is list
            for m in result.members
        )
        assert has_list

    def test_union_with_none_normalizes(self) -> None:
        result = inspect_type(Union[int, None])

        assert is_union_type_node(result)
        assert len(result.members) == 2


class TestNativePreservation:
    @pytest.mark.skipif(
        sys.version_info >= (3, 14),
        reason="Python 3.14+ unifies all unions to types.UnionType at runtime",
    )
    def test_typing_union_with_normalize_false_gives_subscripted_generic(self) -> None:
        config = InspectConfig(normalize_unions=False)
        result = inspect_type(Union[int, str], config=config)

        assert is_subscripted_generic_node(result)
        assert is_generic_node(result.origin)
        assert result.origin.cls is Union
        assert len(result.args) == 2

    @pytest.mark.skipif(
        sys.version_info >= (3, 14),
        reason="Python 3.14+ unifies all unions to types.UnionType at runtime",
    )
    def test_optional_with_normalize_false_gives_subscripted_generic(self) -> None:
        config = InspectConfig(normalize_unions=False)
        result = inspect_type(Optional[int], config=config)

        assert is_subscripted_generic_node(result)
        assert is_generic_node(result.origin)
        assert result.origin.cls is Union
        assert len(result.args) == 2

    @pytest.mark.skipif(
        sys.version_info >= (3, 14),
        reason="Python 3.14+ unifies all unions to types.UnionType at runtime",
    )
    def test_literal_union_with_normalize_false_gives_subscripted_generic(self) -> None:
        lit_union = Literal["a"] | Literal["b"]
        config = InspectConfig(normalize_unions=False)
        result = inspect_type(lit_union, config=config)

        assert is_subscripted_generic_node(result)
        assert is_generic_node(result.origin)
        assert result.origin.cls is Union

    def test_native_union_unaffected_by_normalize_flag(self) -> None:
        # types.UnionType (int | str) always produces UnionNode regardless of config
        result_default = inspect_type(int | str)
        config_false = InspectConfig(normalize_unions=False)
        result_false = inspect_type(int | str, config=config_false)

        assert is_union_type_node(result_default)
        assert is_union_type_node(result_false)


class TestHelperFunctionConsistency:
    def test_is_union_node_works_with_normalized(self) -> None:
        config = InspectConfig(normalize_unions=True)
        result = inspect_type(Union[int, str], config=config)

        assert is_union_node(result) is True

    def test_is_union_node_works_with_native_representation(self) -> None:
        config = InspectConfig(normalize_unions=False)
        result = inspect_type(Union[int, str], config=config)

        assert is_union_node(result) is True

    def test_get_union_members_works_with_normalized(self) -> None:
        config = InspectConfig(normalize_unions=True)
        result = inspect_type(Union[int, str], config=config)
        members = get_union_members(result)

        assert members is not None
        assert len(members) == 2

    def test_get_union_members_works_with_native_representation(self) -> None:
        config = InspectConfig(normalize_unions=False)
        result = inspect_type(Union[int, str], config=config)
        members = get_union_members(result)

        assert members is not None
        assert len(members) == 2

    def test_is_optional_node_works_with_normalized(self) -> None:
        config = InspectConfig(normalize_unions=True)
        result = inspect_type(Optional[int], config=config)

        assert is_optional_node(result) is True

    def test_is_optional_node_works_with_native_representation(self) -> None:
        config = InspectConfig(normalize_unions=False)
        result = inspect_type(Optional[int], config=config)

        assert is_optional_node(result) is True

    def test_unwrap_optional_works_with_normalized(self) -> None:
        config = InspectConfig(normalize_unions=True)
        result = inspect_type(Optional[int], config=config)
        unwrapped = unwrap_optional(result)

        assert unwrapped is not None
        assert len(unwrapped) == 1
        assert is_concrete_node(unwrapped[0])
        assert unwrapped[0].cls is int

    def test_unwrap_optional_works_with_native_representation(self) -> None:
        config = InspectConfig(normalize_unions=False)
        result = inspect_type(Optional[int], config=config)
        unwrapped = unwrap_optional(result)

        assert unwrapped is not None
        assert len(unwrapped) == 1
        assert is_concrete_node(unwrapped[0])
        assert unwrapped[0].cls is int


class TestMetadataHoisting:
    def test_annotated_union_preserves_metadata(self) -> None:
        result = inspect_type(Annotated[Union[int, str], "doc"])

        assert is_union_type_node(result)
        assert "doc" in result.metadata

    def test_annotated_optional_preserves_metadata(self) -> None:
        result = inspect_type(Annotated[Optional[int], "nullable"])

        assert is_union_type_node(result)
        assert "nullable" in result.metadata

    def test_multiple_metadata_items_preserved(self) -> None:
        result = inspect_type(Annotated[Union[int, str], "meta1", "meta2"])

        assert is_union_type_node(result)
        assert "meta1" in result.metadata
        assert "meta2" in result.metadata


class TestQualifierPreservation:
    def test_final_qualifier_preserved_on_union(self) -> None:
        result = inspect_type(Final[Union[int, str]])

        assert is_union_type_node(result)
        assert "final" in result.qualifiers

    def test_classvar_qualifier_preserved_on_union(self) -> None:
        result = inspect_type(ClassVar[Union[int, str]])

        assert is_union_type_node(result)
        assert "class_var" in result.qualifiers


class TestCacheIsolation:
    @pytest.mark.skipif(
        sys.version_info >= (3, 14),
        reason="Python 3.14+ unifies all unions to types.UnionType at runtime",
    )
    def test_cache_isolation_between_normalize_configs(self) -> None:
        # Same type inspected with different normalize_unions settings
        # must return different node types (cache bypass for custom configs)
        norm_config = InspectConfig(normalize_unions=True)
        norm_node = inspect_type(Union[int, str], config=norm_config)

        native_config = InspectConfig(normalize_unions=False)
        native_node = inspect_type(Union[int, str], config=native_config)

        # Results must differ in type
        assert is_union_type_node(norm_node)
        assert is_subscripted_generic_node(native_node)

    @pytest.mark.skipif(
        sys.version_info >= (3, 14),
        reason="Python 3.14+ unifies all unions to types.UnionType at runtime",
    )
    def test_custom_config_result_not_cached(self) -> None:
        # Verify the custom config result wasn't cached
        norm_config = InspectConfig(normalize_unions=True)
        native_config = InspectConfig(normalize_unions=False)

        # First inspection with normalize=False
        native_node = inspect_type(Union[int, str], config=native_config)

        # Second inspection with normalize=True
        norm_node = inspect_type(Union[int, str], config=norm_config)

        # Third inspection with normalize=True should still work
        norm_node_again = inspect_type(Union[int, str], config=norm_config)

        assert is_subscripted_generic_node(native_node)
        assert is_union_type_node(norm_node)
        assert is_union_type_node(norm_node_again)


class TestPython314Behavior:
    @pytest.mark.skipif(
        sys.version_info < (3, 14),
        reason="Python 3.14+ required for union runtime unification",
    )
    def test_both_configs_produce_union_node_on_314(self) -> None:
        # On Python 3.14+, both configs should produce UnionNode
        # because runtime unifies all union forms
        norm_config = InspectConfig(normalize_unions=True)
        native_config = InspectConfig(normalize_unions=False)

        norm_node = inspect_type(Union[int, str], config=norm_config)
        native_node = inspect_type(Union[int, str], config=native_config)

        # Both should be UnionNode on 3.14+
        assert is_union_type_node(norm_node)
        assert is_union_type_node(native_node)

    def test_normalize_true_accepted_on_all_versions(self) -> None:
        config = InspectConfig(normalize_unions=True)
        result = inspect_type(Union[int, str], config=config)

        # Should not raise, and should produce valid result
        assert result is not None
        assert is_union_type_node(result)

    def test_normalize_false_accepted_on_all_versions(self) -> None:
        config = InspectConfig(normalize_unions=False)
        result = inspect_type(Union[int, str], config=config)

        # Should not raise, and should produce valid result
        assert result is not None
        # On pre-3.14, should be SubscriptedGenericNode; on 3.14+ could be UnionNode
        assert is_union_node(result)


class TestNestedUnions:
    def test_nested_typing_union_normalizes_members(self) -> None:
        # Python flattens unions at runtime
        result = inspect_type(Union[Union[int, str], None])

        # Python runtime flattens to Union[int, str, None]
        assert is_union_type_node(result)
        member_classes = {m.cls for m in result.members if is_concrete_node(m)}
        assert int in member_classes
        assert str in member_classes
        assert type(None) in member_classes

    def test_deeply_nested_union_flattened(self) -> None:
        # Python flattens nested unions at runtime
        result = inspect_type(Union[Union[int, str], Union[float, bool]])

        # Runtime flattens to Union[int, str, float, bool]
        assert is_union_type_node(result)
        assert len(result.members) == 4


class TestForwardReferencesInUnions:
    def test_typing_union_with_forward_ref_normalizes(self) -> None:
        result = inspect_type(Union[int, "str"])

        assert is_union_type_node(result)
        assert len(result.members) == 2

    def test_optional_with_forward_ref_normalizes(self) -> None:
        result = inspect_type(Optional["int"])

        assert is_union_type_node(result)
        assert len(result.members) == 2


class TestEdgeCases:
    def test_union_with_single_type_simplifies(self) -> None:
        # Union[int] simplifies to int at runtime
        result = inspect_type(Union[int])

        # Python simplifies Union[X] to X at runtime
        assert is_concrete_node(result)
        assert result.cls is int

    def test_native_union_with_none(self) -> None:
        result = inspect_type(int | None)

        assert is_union_type_node(result)
        assert len(result.members) == 2
        assert is_optional_node(result)

    def test_union_with_duplicate_types_deduplicated(self) -> None:
        # Python deduplicates union members at runtime
        result = inspect_type(Union[int, int, str])  # noqa: PYI016

        assert is_union_type_node(result)
        # Should only have 2 members after deduplication
        assert len(result.members) == 2

    def test_union_preserves_member_order(self) -> None:
        result = inspect_type(Union[int, str, float])

        assert is_union_type_node(result)
        # Verify members are in order
        assert is_concrete_node(result.members[0])
        assert result.members[0].cls is int
        assert is_concrete_node(result.members[1])
        assert result.members[1].cls is str
        assert is_concrete_node(result.members[2])
        assert result.members[2].cls is float

    def test_union_with_generic_type_normalizes(self) -> None:
        result = inspect_type(Union[list[int], dict[str, int]])

        assert is_union_type_node(result)
        assert len(result.members) == 2
        for member in result.members:
            assert is_subscripted_generic_node(member)
