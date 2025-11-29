# ruff: noqa: UP007, UP045, PYI030
# pyright: reportDeprecated=false
# These tests intentionally use Union, Optional, and Literal unions
# to verify both old and new syntax representations work correctly.
from typing import Literal, Optional, Union

import pytest

from typing_graph import (
    get_union_members,
    inspect_type,
    is_concrete_node,
    is_optional_node,
    is_union_node,
    unwrap_optional,
)


class TestIsUnionNode:
    @pytest.mark.parametrize(
        ("type_annotation", "expected"),
        [
            pytest.param(int | str, True, id="pep604_union"),
            pytest.param(int | str | float, True, id="pep604_multi_union"),
            pytest.param(int | None, True, id="pep604_optional"),
            pytest.param(Literal["a"] | Literal["b"], True, id="literal_union"),
            pytest.param(Union[int, str], True, id="typing_union"),
            pytest.param(Optional[int], True, id="optional"),
            pytest.param(int, False, id="concrete_type"),
            pytest.param(list[int], False, id="generic"),
            pytest.param(str, False, id="str"),
        ],
    )
    def test_is_union_node(self, type_annotation: type, expected: bool) -> None:
        node = inspect_type(type_annotation)
        assert is_union_node(node) is expected


class TestGetUnionMembers:
    def test_pep604_union_returns_members(self) -> None:
        node = inspect_type(int | str)
        members = get_union_members(node)
        assert members is not None
        assert len(members) == 2

    def test_typing_union_returns_members(self) -> None:
        node = inspect_type(Union[int, str])
        members = get_union_members(node)
        assert members is not None
        assert len(members) == 2

    def test_literal_union_returns_members(self) -> None:
        node = inspect_type(Literal["a"] | Literal["b"])
        members = get_union_members(node)
        assert members is not None
        assert len(members) == 2

    def test_non_union_returns_none(self) -> None:
        node = inspect_type(list[int])
        assert get_union_members(node) is None

    def test_concrete_type_returns_none(self) -> None:
        node = inspect_type(int)
        assert get_union_members(node) is None


class TestIsOptionalNode:
    @pytest.mark.parametrize(
        ("type_annotation", "expected"),
        [
            pytest.param(int | None, True, id="pep604_optional"),
            pytest.param(Union[int, None], True, id="typing_union_none"),
            pytest.param(Optional[int], True, id="optional"),
            pytest.param(int | str | None, True, id="multi_optional"),
            pytest.param(Optional[str], True, id="optional_str"),
            pytest.param(int | str, False, id="union_without_none"),
            pytest.param(int, False, id="not_union"),
            pytest.param(list[int], False, id="generic"),
            pytest.param(type(None), False, id="just_none"),
        ],
    )
    def test_is_optional_node(self, type_annotation: type, expected: bool) -> None:
        node = inspect_type(type_annotation)
        assert is_optional_node(node) is expected


class TestUnwrapOptional:
    def test_simple_optional_returns_inner_type(self) -> None:
        node = inspect_type(int | None)
        unwrapped = unwrap_optional(node)
        assert unwrapped is not None
        assert len(unwrapped) == 1
        assert is_concrete_node(unwrapped[0])
        assert unwrapped[0].cls is int

    def test_typing_optional_returns_inner_type(self) -> None:
        node = inspect_type(Optional[str])
        unwrapped = unwrap_optional(node)
        assert unwrapped is not None
        assert len(unwrapped) == 1
        assert is_concrete_node(unwrapped[0])
        assert unwrapped[0].cls is str

    def test_multi_optional_returns_all_non_none(self) -> None:
        node = inspect_type(int | str | None)
        unwrapped = unwrap_optional(node)
        assert unwrapped is not None
        assert len(unwrapped) == 2
        cls_set = {m.cls for m in unwrapped if is_concrete_node(m)}
        assert cls_set == {int, str}

    def test_non_optional_union_returns_none(self) -> None:
        node = inspect_type(int | str)
        assert unwrap_optional(node) is None

    def test_non_union_returns_none(self) -> None:
        node = inspect_type(int)
        assert unwrap_optional(node) is None
