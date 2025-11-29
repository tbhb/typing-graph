# pyright: reportAny=false, reportExplicitAny=false
# pyright: reportUnusedCallResult=false
# ruff: noqa: SLF001

import pytest

from typing_graph._metadata import (
    MetadataCollection,
    MetadataNotFoundError,
    ProtocolNotRuntimeCheckableError,
    SupportsLessThan,
)


class TestEmptyConstructionAndSingleton:
    # MC-001
    def test_empty_construction_returns_zero_length(self) -> None:
        coll = MetadataCollection()
        assert len(coll) == 0

    # MC-002: Note - Direct construction does NOT return singleton.
    # The EMPTY singleton is accessed via MetadataCollection.EMPTY.
    # The test verifies that the EMPTY class variable is correctly set.
    def test_empty_singleton_is_correct(self) -> None:
        assert len(MetadataCollection.EMPTY) == 0
        assert MetadataCollection.EMPTY._items == ()

    # MC-003
    def test_empty_singleton_identity(self) -> None:
        first = MetadataCollection.EMPTY
        second = MetadataCollection.EMPTY
        third = MetadataCollection.EMPTY
        assert first is second
        assert second is third


class TestSequenceProtocol:
    # MC-058
    def test_len_returns_item_count(self) -> None:
        coll = MetadataCollection(_items=("a", "b", "c"))
        assert len(coll) == 3

    def test_len_returns_zero_for_empty(self) -> None:
        coll = MetadataCollection()
        assert len(coll) == 0

    def test_len_returns_correct_for_large_collection(self) -> None:
        items = tuple(range(100))
        coll = MetadataCollection(_items=items)
        assert len(coll) == 100

    # MC-059
    def test_iter_yields_items_in_order(self) -> None:
        items = ("a", "b", "c")
        coll = MetadataCollection(_items=items)
        result = list(coll)
        assert result == ["a", "b", "c"]

    def test_iter_yields_nothing_for_empty(self) -> None:
        coll = MetadataCollection()
        result = list(coll)
        assert result == []

    # MC-060
    def test_contains_returns_true_for_present_item(self) -> None:
        coll = MetadataCollection(_items=("doc", 42))
        assert "doc" in coll
        assert 42 in coll

    # MC-061
    def test_contains_returns_false_for_absent_item(self) -> None:
        coll = MetadataCollection(_items=("doc", 42))
        assert "missing" not in coll
        assert 99 not in coll

    # MC-062
    def test_getitem_integer_returns_item_at_index(self) -> None:
        coll = MetadataCollection(_items=("a", "b", "c"))
        assert coll[0] == "a"
        assert coll[1] == "b"
        assert coll[2] == "c"

    # MC-063
    def test_getitem_negative_index_counts_from_end(self) -> None:
        coll = MetadataCollection(_items=("a", "b", "c"))
        assert coll[-1] == "c"
        assert coll[-2] == "b"
        assert coll[-3] == "a"

    # MC-064
    def test_getitem_slice_returns_new_collection(self) -> None:
        coll = MetadataCollection(_items=("a", "b", "c", "d"))
        result = coll[1:3]
        assert isinstance(result, MetadataCollection)
        assert list(result) == ["b", "c"]

    def test_getitem_slice_empty_returns_empty_singleton(self) -> None:
        coll = MetadataCollection(_items=("a", "b", "c"))
        result = coll[10:20]
        assert result is MetadataCollection.EMPTY

    def test_getitem_full_slice_returns_new_collection(self) -> None:
        coll = MetadataCollection(_items=("a", "b", "c"))
        result = coll[:]
        assert isinstance(result, MetadataCollection)
        assert list(result) == ["a", "b", "c"]

    # MC-065
    def test_getitem_raises_index_error_for_out_of_bounds(self) -> None:
        coll = MetadataCollection(_items=("a", "b", "c"))
        with pytest.raises(IndexError):
            _ = coll[10]

    def test_getitem_raises_index_error_for_negative_out_of_bounds(self) -> None:
        coll = MetadataCollection(_items=("a", "b", "c"))
        with pytest.raises(IndexError):
            _ = coll[-10]

    # MC-066
    def test_bool_returns_true_for_non_empty(self) -> None:
        coll = MetadataCollection(_items=(1,))
        assert bool(coll) is True

    def test_bool_returns_true_for_multi_item(self) -> None:
        coll = MetadataCollection(_items=(1, 2, 3))
        assert bool(coll) is True

    # MC-067
    def test_bool_returns_false_for_empty(self) -> None:
        coll = MetadataCollection()
        assert bool(coll) is False

    def test_bool_returns_false_for_empty_singleton(self) -> None:
        assert bool(MetadataCollection.EMPTY) is False


class TestHashability:
    # MC-091
    def test_is_hashable_returns_true_for_hashable_items(self) -> None:
        coll = MetadataCollection(_items=("doc", 42, (1, 2, 3)))
        assert coll.is_hashable is True

    def test_is_hashable_returns_true_for_empty(self) -> None:
        coll = MetadataCollection()
        assert coll.is_hashable is True

    # MC-092
    def test_is_hashable_returns_false_for_unhashable_items(self) -> None:
        coll = MetadataCollection(_items=({"key": "value"},))
        assert coll.is_hashable is False

    def test_is_hashable_returns_false_for_list_item(self) -> None:
        coll = MetadataCollection(_items=([1, 2, 3],))
        assert coll.is_hashable is False

    def test_is_hashable_returns_false_for_mixed_with_unhashable(self) -> None:
        coll = MetadataCollection(_items=("hashable", {"not": "hashable"}))
        assert coll.is_hashable is False


class TestRepr:
    # MC-093
    def test_repr_small_collection_shows_all_items(self) -> None:
        coll = MetadataCollection(_items=(1, 2))
        result = repr(coll)
        assert result == "MetadataCollection([1, 2])"

    def test_repr_single_item_shows_item(self) -> None:
        coll = MetadataCollection(_items=("doc",))
        result = repr(coll)
        assert result == "MetadataCollection(['doc'])"

    def test_repr_five_items_shows_all(self) -> None:
        coll = MetadataCollection(_items=(1, 2, 3, 4, 5))
        result = repr(coll)
        assert result == "MetadataCollection([1, 2, 3, 4, 5])"

    # MC-094
    def test_repr_large_collection_truncates(self) -> None:
        coll = MetadataCollection(_items=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10))
        result = repr(coll)
        assert result == "MetadataCollection([1, 2, 3, 4, 5, ...<5 more>])"

    def test_repr_six_items_truncates(self) -> None:
        coll = MetadataCollection(_items=(1, 2, 3, 4, 5, 6))
        result = repr(coll)
        assert result == "MetadataCollection([1, 2, 3, 4, 5, ...<1 more>])"

    # MC-095
    def test_repr_empty_collection_format(self) -> None:
        coll = MetadataCollection.EMPTY
        result = repr(coll)
        assert result == "MetadataCollection([])"

    def test_repr_empty_constructed_format(self) -> None:
        coll = MetadataCollection()
        result = repr(coll)
        assert result == "MetadataCollection([])"


class TestEqualityAndHashing:
    # MC-096
    def test_eq_equal_collections_are_equal(self) -> None:
        a = MetadataCollection(_items=(1, 2, 3))
        b = MetadataCollection(_items=(1, 2, 3))
        assert a == b

    def test_eq_empty_collections_are_equal(self) -> None:
        a = MetadataCollection()
        b = MetadataCollection()
        assert a == b

    # MC-097
    def test_eq_different_order_not_equal(self) -> None:
        a = MetadataCollection(_items=("a", "b"))
        b = MetadataCollection(_items=("b", "a"))
        assert a != b

    def test_eq_different_lengths_not_equal(self) -> None:
        a = MetadataCollection(_items=(1, 2, 3))
        b = MetadataCollection(_items=(1, 2))
        assert a != b

    # MC-098
    def test_eq_non_collection_not_equal(self) -> None:
        coll = MetadataCollection(_items=(1, 2, 3))
        assert (coll == [1, 2, 3]) is False
        assert (coll == (1, 2, 3)) is False
        assert (coll == "not a collection") is False

    def test_eq_non_collection_returns_not_implemented(self) -> None:
        coll = MetadataCollection(_items=(1, 2))
        # When comparing with non-MetadataCollection, __eq__ returns NotImplemented
        # which Python interprets as False
        assert coll != [1, 2]

    # MC-099
    def test_hash_consistent_for_equal_collections(self) -> None:
        a = MetadataCollection(_items=(1, "doc", (2, 3)))
        b = MetadataCollection(_items=(1, "doc", (2, 3)))
        assert a == b
        assert hash(a) == hash(b)

    def test_hash_empty_collections_consistent(self) -> None:
        a = MetadataCollection()
        b = MetadataCollection()
        assert hash(a) == hash(b)

    # MC-100
    def test_hash_raises_for_unhashable_items(self) -> None:
        coll = MetadataCollection(_items=({"key": "value"},))
        with pytest.raises(TypeError, match="unhashable"):
            hash(coll)

    def test_hash_raises_for_list_item(self) -> None:
        coll = MetadataCollection(_items=([1, 2, 3],))
        with pytest.raises(TypeError, match="unhashable"):
            hash(coll)

    # MC-101
    def test_hashable_collection_can_be_set_member(self) -> None:
        coll = MetadataCollection(_items=(1, "doc"))
        s = {coll}
        assert coll in s

    def test_hashable_collections_in_set_dedupe(self) -> None:
        a = MetadataCollection(_items=(1, 2))
        b = MetadataCollection(_items=(1, 2))
        s = {a, b}
        assert len(s) == 1

    # MC-102
    def test_hashable_collection_can_be_dict_key(self) -> None:
        coll = MetadataCollection(_items=(1, "doc"))
        d = {coll: "value"}
        assert d[coll] == "value"

    def test_hashable_collections_as_dict_keys_merge(self) -> None:
        a = MetadataCollection(_items=(1, 2))
        b = MetadataCollection(_items=(1, 2))
        d = {a: "first", b: "second"}
        assert len(d) == 1
        assert d[a] == "second"


class TestExceptionClasses:
    def test_metadata_not_found_error_has_requested_type_attribute(self) -> None:
        coll = MetadataCollection(_items=("doc",))
        error = MetadataNotFoundError(int, coll)
        assert error.requested_type is int

    def test_metadata_not_found_error_has_collection_attribute(self) -> None:
        coll = MetadataCollection(_items=("doc",))
        error = MetadataNotFoundError(int, coll)
        assert error.collection is coll

    def test_metadata_not_found_error_message_format(self) -> None:
        coll = MetadataCollection(_items=("doc",))
        error = MetadataNotFoundError(int, coll)
        msg = str(error)
        assert "'int'" in msg
        assert "find()" in msg

    def test_metadata_not_found_error_is_lookup_error(self) -> None:
        coll = MetadataCollection()
        error = MetadataNotFoundError(str, coll)
        assert isinstance(error, LookupError)

    def test_protocol_not_runtime_checkable_error_has_protocol_attribute(self) -> None:
        from typing import Protocol

        class NotRuntime(Protocol):
            value: int

        error = ProtocolNotRuntimeCheckableError(NotRuntime)
        assert error.protocol is NotRuntime

    def test_protocol_not_runtime_checkable_error_message_format(self) -> None:
        from typing import Protocol

        class MyProtocol(Protocol):
            pass

        error = ProtocolNotRuntimeCheckableError(MyProtocol)
        msg = str(error)
        assert "MyProtocol" in msg
        assert "@runtime_checkable" in msg
        assert "find_protocol()" in msg or "has_protocol()" in msg

    def test_protocol_not_runtime_checkable_error_is_type_error(self) -> None:
        from typing import Protocol

        class TestProto(Protocol):
            pass

        error = ProtocolNotRuntimeCheckableError(TestProto)
        assert isinstance(error, TypeError)


class TestSupportsLessThanProtocol:
    def test_supports_less_than_is_protocol(self) -> None:
        from typing import Protocol

        assert issubclass(SupportsLessThan, Protocol)

    def test_supports_less_than_defines_lt(self) -> None:
        assert hasattr(SupportsLessThan, "__lt__")
