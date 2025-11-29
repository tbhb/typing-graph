# ruff: noqa: SLF001

from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, Protocol, final, runtime_checkable
from typing_extensions import override

import pytest
from annotated_types import Ge, GroupedMetadata, Interval, Le

from typing_graph._metadata import (
    MetadataCollection,
    MetadataNotFoundError,
    ProtocolNotRuntimeCheckableError,
    SupportsLessThan,
)

if TYPE_CHECKING:
    from collections.abc import Iterator


# Helper protocols for protocol-based filtering tests
@runtime_checkable
class HasValue(Protocol):
    value: int


class NotRuntimeCheckable(Protocol):
    value: int


class NotAProtocol:
    value: int

    def __init__(self, value: int) -> None:
        self.value = value


# Helper dataclass for typed predicate tests
@dataclass
class ItemWithValue:
    value: int


class TestEmptyConstructionAndSingleton:
    def test_empty_construction_returns_zero_length(self) -> None:
        coll = MetadataCollection()
        assert len(coll) == 0

    def test_empty_singleton_is_correct(self) -> None:
        assert len(MetadataCollection.EMPTY) == 0
        assert MetadataCollection.EMPTY._items == ()

    def test_empty_singleton_identity(self) -> None:
        first = MetadataCollection.EMPTY
        second = MetadataCollection.EMPTY
        third = MetadataCollection.EMPTY
        assert first is second
        assert second is third


class TestSequenceProtocol:
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

    def test_iter_yields_items_in_order(self) -> None:
        items = ("a", "b", "c")
        coll = MetadataCollection(_items=items)
        result = list(coll)
        assert result == ["a", "b", "c"]

    def test_iter_yields_nothing_for_empty(self) -> None:
        coll = MetadataCollection()
        result = list(coll)
        assert result == []

    def test_contains_returns_true_for_present_item(self) -> None:
        coll = MetadataCollection(_items=("doc", 42))
        assert "doc" in coll
        assert 42 in coll

    def test_contains_returns_false_for_absent_item(self) -> None:
        coll = MetadataCollection(_items=("doc", 42))
        assert "missing" not in coll
        assert 99 not in coll

    def test_getitem_integer_returns_item_at_index(self) -> None:
        coll = MetadataCollection(_items=("a", "b", "c"))
        assert coll[0] == "a"
        assert coll[1] == "b"
        assert coll[2] == "c"

    def test_getitem_negative_index_counts_from_end(self) -> None:
        coll = MetadataCollection(_items=("a", "b", "c"))
        assert coll[-1] == "c"
        assert coll[-2] == "b"
        assert coll[-3] == "a"

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

    def test_getitem_raises_index_error_for_out_of_bounds(self) -> None:
        coll = MetadataCollection(_items=("a", "b", "c"))
        with pytest.raises(IndexError):
            _ = coll[10]

    def test_getitem_raises_index_error_for_negative_out_of_bounds(self) -> None:
        coll = MetadataCollection(_items=("a", "b", "c"))
        with pytest.raises(IndexError):
            _ = coll[-10]

    def test_bool_returns_true_for_non_empty(self) -> None:
        coll = MetadataCollection(_items=(1,))
        assert bool(coll) is True

    def test_bool_returns_true_for_multi_item(self) -> None:
        coll = MetadataCollection(_items=(1, 2, 3))
        assert bool(coll) is True

    def test_bool_returns_false_for_empty(self) -> None:
        coll = MetadataCollection()
        assert bool(coll) is False

    def test_bool_returns_false_for_empty_singleton(self) -> None:
        assert bool(MetadataCollection.EMPTY) is False


class TestHashability:
    def test_is_hashable_returns_true_for_hashable_items(self) -> None:
        coll = MetadataCollection(_items=("doc", 42, (1, 2, 3)))
        assert coll.is_hashable is True

    def test_is_hashable_returns_true_for_empty(self) -> None:
        coll = MetadataCollection()
        assert coll.is_hashable is True

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

    def test_repr_large_collection_truncates(self) -> None:
        coll = MetadataCollection(_items=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10))
        result = repr(coll)
        assert result == "MetadataCollection([1, 2, 3, 4, 5, ...<5 more>])"

    def test_repr_six_items_truncates(self) -> None:
        coll = MetadataCollection(_items=(1, 2, 3, 4, 5, 6))
        result = repr(coll)
        assert result == "MetadataCollection([1, 2, 3, 4, 5, ...<1 more>])"

    def test_repr_empty_collection_format(self) -> None:
        coll = MetadataCollection.EMPTY
        result = repr(coll)
        assert result == "MetadataCollection([])"

    def test_repr_empty_constructed_format(self) -> None:
        coll = MetadataCollection()
        result = repr(coll)
        assert result == "MetadataCollection([])"


class TestEqualityAndHashing:
    def test_eq_equal_collections_are_equal(self) -> None:
        a = MetadataCollection(_items=(1, 2, 3))
        b = MetadataCollection(_items=(1, 2, 3))
        assert a == b

    def test_eq_empty_collections_are_equal(self) -> None:
        a = MetadataCollection()
        b = MetadataCollection()
        assert a == b

    def test_eq_different_order_not_equal(self) -> None:
        a = MetadataCollection(_items=("a", "b"))
        b = MetadataCollection(_items=("b", "a"))
        assert a != b

    def test_eq_different_lengths_not_equal(self) -> None:
        a = MetadataCollection(_items=(1, 2, 3))
        b = MetadataCollection(_items=(1, 2))
        assert a != b

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

    def test_hash_consistent_for_equal_collections(self) -> None:
        a = MetadataCollection(_items=(1, "doc", (2, 3)))
        b = MetadataCollection(_items=(1, "doc", (2, 3)))
        assert a == b
        assert hash(a) == hash(b)

    def test_hash_empty_collections_consistent(self) -> None:
        a = MetadataCollection()
        b = MetadataCollection()
        assert hash(a) == hash(b)

    def test_hash_raises_for_unhashable_items(self) -> None:
        coll = MetadataCollection(_items=({"key": "value"},))
        with pytest.raises(TypeError, match="unhashable"):
            _ = hash(coll)

    def test_hash_raises_for_list_item(self) -> None:
        coll = MetadataCollection(_items=([1, 2, 3],))
        with pytest.raises(TypeError, match="unhashable"):
            _ = hash(coll)

    def test_hashable_collection_can_be_set_member(self) -> None:
        coll = MetadataCollection(_items=(1, "doc"))
        s = {coll}
        assert coll in s

    def test_hashable_collections_in_set_dedupe(self) -> None:
        a = MetadataCollection(_items=(1, 2))
        b = MetadataCollection(_items=(1, 2))
        s = {a, b}
        assert len(s) == 1

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
        class NotRuntime(Protocol):
            value: int

        error = ProtocolNotRuntimeCheckableError(NotRuntime)
        assert error.protocol is NotRuntime

    def test_protocol_not_runtime_checkable_error_message_format(self) -> None:
        class MyProtocol(Protocol):
            pass

        error = ProtocolNotRuntimeCheckableError(MyProtocol)
        msg = str(error)
        assert "MyProtocol" in msg
        assert "@runtime_checkable" in msg
        assert "find_protocol()" in msg or "has_protocol()" in msg

    def test_protocol_not_runtime_checkable_error_is_type_error(self) -> None:
        class TestProto(Protocol):
            pass

        error = ProtocolNotRuntimeCheckableError(TestProto)
        assert isinstance(error, TypeError)


class TestSupportsLessThanProtocol:
    def test_supports_less_than_is_protocol(self) -> None:
        assert issubclass(SupportsLessThan, Protocol)

    def test_supports_less_than_defines_lt(self) -> None:
        assert hasattr(SupportsLessThan, "__lt__")


class TestOfFactoryMethod:
    def test_of_creates_collection_from_list(self) -> None:
        items = [1, "doc", True]
        coll = MetadataCollection.of(items)
        assert len(coll) == 3
        assert list(coll) == [1, "doc", True]

    def test_of_creates_collection_from_tuple(self) -> None:
        items = (1, 2, 3)
        coll = MetadataCollection.of(items)
        assert len(coll) == 3
        assert list(coll) == [1, 2, 3]

    def test_of_creates_collection_from_generator(self) -> None:
        items = (x * 2 for x in range(3))
        coll = MetadataCollection.of(items)
        assert list(coll) == [0, 2, 4]

    def test_of_preserves_insertion_order(self) -> None:
        items = ["first", "second", "third", "fourth", "fifth"]
        coll = MetadataCollection.of(items)
        assert list(coll) == ["first", "second", "third", "fourth", "fifth"]

    def test_of_preserves_order_with_mixed_types(self) -> None:
        items = [1, "a", None, True, 3.14]
        coll = MetadataCollection.of(items)
        assert list(coll) == [1, "a", None, True, 3.14]

    def test_of_auto_flattens_grouped_metadata(self) -> None:
        interval = Interval(ge=0, le=100)
        items = ["doc", interval, "end"]
        coll = MetadataCollection.of(items)
        # Interval should be flattened to Ge and Le
        result = list(coll)
        assert result[0] == "doc"
        assert result[1] == Ge(ge=0)
        assert result[2] == Le(le=100)
        assert result[3] == "end"
        assert len(coll) == 4

    def test_of_auto_flattens_multiple_grouped_metadata(self) -> None:
        interval1 = Interval(ge=0, le=10)
        interval2 = Interval(ge=20, le=30)
        items = [interval1, interval2]
        coll = MetadataCollection.of(items)
        # Both intervals should be flattened: Ge(0), Le(10), Ge(20), Le(30)
        assert list(coll) == [Ge(ge=0), Le(le=10), Ge(ge=20), Le(le=30)]

    def test_of_preserves_grouped_metadata_when_disabled(self) -> None:
        interval = Interval(ge=0, le=100)
        items = ["doc", interval, "end"]
        coll = MetadataCollection.of(items, auto_flatten=False)
        result = list(coll)
        assert result[0] == "doc"
        assert result[1] is interval
        assert result[2] == "end"
        assert len(coll) == 3

    def test_of_empty_iterable_returns_singleton(self) -> None:
        coll = MetadataCollection.of([])
        assert coll is MetadataCollection.EMPTY

    def test_of_empty_generator_returns_singleton(self) -> None:
        empty: list[object] = []
        coll = MetadataCollection.of(x for x in empty)
        assert coll is MetadataCollection.EMPTY

    def test_of_empty_tuple_returns_singleton(self) -> None:
        coll = MetadataCollection.of(())
        assert coll is MetadataCollection.EMPTY

    def test_of_no_args_returns_singleton(self) -> None:
        coll = MetadataCollection.of()
        assert coll is MetadataCollection.EMPTY


class TestFromAnnotatedFactoryMethod:
    def test_from_annotated_extracts_metadata(self) -> None:
        t = Annotated[int, "doc", 42]
        coll = MetadataCollection.from_annotated(t)
        assert len(coll) == 2
        assert list(coll) == ["doc", 42]

    def test_from_annotated_extracts_single_metadata(self) -> None:
        t = Annotated[str, "description"]
        coll = MetadataCollection.from_annotated(t)
        assert len(coll) == 1
        assert list(coll) == ["description"]

    def test_from_annotated_extracts_many_metadata(self) -> None:
        t = Annotated[int, "a", "b", "c", "d", "e"]
        coll = MetadataCollection.from_annotated(t)
        assert len(coll) == 5
        assert list(coll) == ["a", "b", "c", "d", "e"]

    # Note: Python automatically flattens nested Annotated types at definition
    # time, with inner metadata appearing before outer metadata. This is Python
    # behavior, not typing-graph behavior.
    def test_from_annotated_unwraps_nested_by_default(self) -> None:
        inner_type = Annotated[int, "inner1", "inner2"]
        outer_type = Annotated[inner_type, "outer1", "outer2"]
        coll = MetadataCollection.from_annotated(outer_type)
        # Python flattens nested Annotated: inner metadata comes first
        assert list(coll) == ["inner1", "inner2", "outer1", "outer2"]

    def test_from_annotated_unwraps_deeply_nested(self) -> None:
        level1 = Annotated[int, "L1"]
        level2 = Annotated[level1, "L2"]
        level3 = Annotated[level2, "L3"]
        coll = MetadataCollection.from_annotated(level3)
        # Python flattens all levels: innermost metadata comes first
        assert list(coll) == ["L1", "L2", "L3"]

    # Note: Since Python automatically flattens nested Annotated types,
    # the unwrap_nested=False parameter has no practical effect - all
    # metadata is already collected by get_args().
    def test_from_annotated_preserves_nesting_when_disabled(self) -> None:
        inner_type = Annotated[int, "inner"]
        outer_type = Annotated[inner_type, "outer"]
        coll = MetadataCollection.from_annotated(outer_type, unwrap_nested=False)
        # Python already flattened, so we get all metadata
        assert list(coll) == ["inner", "outer"]

    def test_from_annotated_preserves_deep_nesting_when_disabled(self) -> None:
        level1 = Annotated[int, "L1"]
        level2 = Annotated[level1, "L2"]
        level3 = Annotated[level2, "L3"]
        coll = MetadataCollection.from_annotated(level3, unwrap_nested=False)
        # Python already flattened, so we get all metadata
        assert list(coll) == ["L1", "L2", "L3"]

    def test_from_annotated_non_annotated_returns_empty(self) -> None:
        coll = MetadataCollection.from_annotated(int)
        assert coll is MetadataCollection.EMPTY

    def test_from_annotated_list_type_returns_empty(self) -> None:
        coll = MetadataCollection.from_annotated(list[int])
        assert coll is MetadataCollection.EMPTY

    def test_from_annotated_none_type_returns_empty(self) -> None:
        coll = MetadataCollection.from_annotated(None)
        assert coll is MetadataCollection.EMPTY

    def test_from_annotated_string_returns_empty(self) -> None:
        coll = MetadataCollection.from_annotated("not a type")
        assert coll is MetadataCollection.EMPTY

    def test_from_annotated_flattens_grouped_metadata(self) -> None:
        interval = Interval(ge=0, le=100)
        t = Annotated[int, "doc", interval]
        coll = MetadataCollection.from_annotated(t)
        result = list(coll)
        assert result[0] == "doc"
        assert result[1] == Ge(ge=0)
        assert result[2] == Le(le=100)

    def test_from_annotated_flattens_nested_grouped_metadata(self) -> None:
        inner_type = Annotated[int, Interval(ge=0, le=10)]
        outer_type = Annotated[inner_type, Interval(ge=100, le=200)]
        coll = MetadataCollection.from_annotated(outer_type)
        result = list(coll)
        # Outer interval flattened first, then inner
        assert Ge(ge=100) in result
        assert Le(le=200) in result
        assert Ge(ge=0) in result
        assert Le(le=10) in result


class TestFlattenMethod:
    def test_flatten_expands_grouped_metadata(self) -> None:
        interval = Interval(ge=5, le=15)
        coll = MetadataCollection.of([interval], auto_flatten=False)
        flattened = coll.flatten()
        result = list(flattened)
        assert result == [Ge(ge=5), Le(le=15)]

    def test_flatten_expands_multiple_grouped_metadata(self) -> None:
        interval1 = Interval(ge=0, le=10)
        interval2 = Interval(ge=20, le=30)
        coll = MetadataCollection.of([interval1, interval2], auto_flatten=False)
        flattened = coll.flatten()
        assert len(flattened) == 4

    def test_flatten_preserves_non_grouped_items(self) -> None:
        coll = MetadataCollection(_items=("doc", 42, True))
        flattened = coll.flatten()
        assert list(flattened) == ["doc", 42, True]

    def test_flatten_preserves_order(self) -> None:
        interval = Interval(ge=0, le=10)
        coll = MetadataCollection.of(["before", interval, "after"], auto_flatten=False)
        flattened = coll.flatten()
        result = list(flattened)
        assert result[0] == "before"
        assert result[1] == Ge(ge=0)
        assert result[2] == Le(le=10)
        assert result[3] == "after"

    def test_flatten_returns_self_when_no_grouped(self) -> None:
        coll = MetadataCollection(_items=(1, 2, 3))
        flattened = coll.flatten()
        assert flattened is coll

    def test_flatten_empty_returns_self(self) -> None:
        coll = MetadataCollection.EMPTY
        flattened = coll.flatten()
        assert flattened is coll

    def test_flatten_empty_grouped_metadata_returns_empty(self) -> None:
        @final
        class EmptyGrouped(GroupedMetadata):
            @override
            def __iter__(self) -> "Iterator[object]":
                return iter([])

        empty_grouped = EmptyGrouped()
        coll = MetadataCollection.of([empty_grouped], auto_flatten=False)
        flattened = coll.flatten()
        assert flattened is MetadataCollection.EMPTY


# Helper classes for subclass tests
class Animal:
    pass


class Dog(Animal):
    name: str

    def __init__(self, name: str) -> None:
        self.name = name


class Cat(Animal):
    name: str

    def __init__(self, name: str) -> None:
        self.name = name


class TestFindMethod:
    def test_find_returns_first_matching_type(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0), Le(le=100), Ge(ge=10)))
        result = coll.find(Ge)
        assert result == Ge(ge=0)
        assert result != Ge(ge=10)

    def test_find_returns_none_when_no_match(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0), "doc"))
        result = coll.find(Le)
        assert result is None

    def test_find_returns_none_for_empty_collection(self) -> None:
        coll = MetadataCollection.EMPTY
        result = coll.find(int)
        assert result is None

    def test_find_matches_subclasses(self) -> None:
        dog = Dog("Fido")
        cat = Cat("Whiskers")
        coll = MetadataCollection(_items=("doc", dog, cat))
        result = coll.find(Animal)
        assert result is dog

    def test_find_with_bool_matches_int_due_to_subclass(self) -> None:
        coll = MetadataCollection(_items=(True, 42, "doc"))
        result = coll.find(int)
        # bool is a subclass of int, so True matches first
        assert result is True


class TestFindFirstMethod:
    def test_find_first_single_type_matches(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0), Le(le=100)))
        result = coll.find_first(Ge)
        assert result == Ge(ge=0)

    def test_find_first_multiple_types_returns_first_match(self) -> None:
        dog = Dog("Fido")
        coll = MetadataCollection(_items=(dog, "doc", Le(le=100)))
        result = coll.find_first(Le, str)
        # "doc" comes before Le(100) in the collection
        assert result == "doc"

    def test_find_first_returns_none_when_no_match(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0), "doc"))
        result = coll.find_first(Le, int)
        assert result is None

    def test_find_first_returns_none_for_empty_collection(self) -> None:
        coll = MetadataCollection.EMPTY
        result = coll.find_first(int, str)
        assert result is None

    def test_find_first_returns_none_with_no_types(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0), "doc"))
        result = coll.find_first()
        assert result is None


class TestFindAllMethod:
    def test_find_all_no_args_returns_all_items(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0), "doc", Le(le=100)))
        result = coll.find_all()
        assert list(result) == [Ge(ge=0), "doc", Le(le=100)]
        assert isinstance(result, MetadataCollection)

    def test_find_all_no_args_on_empty_returns_empty_singleton(self) -> None:
        coll = MetadataCollection.EMPTY
        result = coll.find_all()
        assert result is MetadataCollection.EMPTY

    def test_find_all_single_type_returns_matching(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0), Le(le=100), Ge(ge=10)))
        result = coll.find_all(Ge)
        assert list(result) == [Ge(ge=0), Ge(ge=10)]

    def test_find_all_multiple_types_returns_all_matching(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0), "doc", Le(le=100), 42))
        result = coll.find_all(Ge, Le)
        assert list(result) == [Ge(ge=0), Le(le=100)]

    def test_find_all_preserves_order(self) -> None:
        items = (Ge(ge=1), Le(le=2), Ge(ge=3), Le(le=4), Ge(ge=5))
        coll = MetadataCollection(_items=items)
        result = coll.find_all(Ge)
        assert list(result) == [Ge(ge=1), Ge(ge=3), Ge(ge=5)]

    def test_find_all_returns_empty_singleton_when_no_match(self) -> None:
        coll = MetadataCollection(_items=("doc", 42))
        result = coll.find_all(Ge)
        assert result is MetadataCollection.EMPTY

    def test_find_all_enables_chaining(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0), Le(le=100), Ge(ge=10)))
        result = coll.find_all(Ge, Le).exclude(Le)
        assert list(result) == [Ge(ge=0), Ge(ge=10)]


class TestHasMethod:
    def test_has_returns_true_when_type_present(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0), "doc"))
        assert coll.has(Ge) is True

    def test_has_returns_false_when_type_absent(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0), "doc"))
        assert coll.has(Le) is False

    def test_has_returns_false_for_empty_collection(self) -> None:
        coll = MetadataCollection.EMPTY
        assert coll.has(int) is False

    def test_has_multiple_types_returns_true_if_any_present(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0),))
        assert coll.has(Le, Ge) is True

    def test_has_multiple_types_returns_false_if_none_present(self) -> None:
        coll = MetadataCollection(_items=("doc", 42))
        assert coll.has(Ge, Le) is False

    def test_has_with_no_types_returns_false(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0), "doc"))
        assert coll.has() is False


class TestCountMethod:
    def test_count_single_type_returns_correct_count(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0), Ge(ge=10), Le(le=100)))
        assert coll.count(Ge) == 2

    def test_count_returns_zero_when_no_match(self) -> None:
        coll = MetadataCollection(_items=("doc", 42))
        assert coll.count(Ge) == 0

    def test_count_returns_all_for_matching_type(self) -> None:
        coll = MetadataCollection(_items=("a", "b", "c"))
        assert coll.count(str) == 3

    def test_count_multiple_types_returns_combined_count(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0), Ge(ge=10), Le(le=100), "doc"))
        assert coll.count(Ge, Le) == 3

    def test_count_with_no_types_returns_zero(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0), "doc"))
        assert coll.count() == 0


class TestGetMethod:
    def test_get_without_default_returns_match(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0), "doc"))
        result = coll.get(Ge)
        assert result == Ge(ge=0)

    def test_get_without_default_returns_none_on_miss(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0), "doc"))
        result = coll.get(Le)
        assert result is None

    def test_get_with_same_type_default_returns_match(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0), "doc"))
        result = coll.get(Ge, Ge(ge=999))
        assert result == Ge(ge=0)

    def test_get_with_same_type_default_returns_default_on_miss(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0),))
        result = coll.get(Le, Le(le=100))
        assert result == Le(le=100)

    def test_get_with_sentinel_default_pattern(self) -> None:
        class _Missing:
            pass

        missing = _Missing()
        coll = MetadataCollection(_items=(Ge(ge=0),))
        result = coll.get(Le, missing)
        assert result is missing

    def test_get_returns_falsy_values_correctly(self) -> None:
        coll = MetadataCollection(_items=(0, False, ""))
        # Should return 0, not the default
        assert coll.get(int, -1) == 0
        # Should return False, not True default
        # Note: bool is a subclass of int, so int matches first
        coll2 = MetadataCollection(_items=(False, 1))
        assert coll2.get(bool, True) is False
        # Should return empty string, not default
        assert coll.get(str, "default") == ""


class TestGetRequiredMethod:
    def test_get_required_returns_matching_item(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0), "doc"))
        result = coll.get_required(Ge)
        assert result == Ge(ge=0)

    def test_get_required_raises_metadata_not_found_error(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0), "doc"))
        with pytest.raises(MetadataNotFoundError):
            _ = coll.get_required(Le)

    def test_get_required_raises_for_empty_collection(self) -> None:
        coll = MetadataCollection.EMPTY
        with pytest.raises(MetadataNotFoundError):
            _ = coll.get_required(int)

    def test_get_required_error_has_correct_attributes(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0),))
        with pytest.raises(MetadataNotFoundError) as exc_info:
            _ = coll.get_required(Le)
        error = exc_info.value
        assert error.requested_type is Le
        assert error.collection is coll
        assert "Le" in str(error)
        assert "find()" in str(error)


class TestIsEmptyProperty:
    def test_is_empty_returns_true_for_empty(self) -> None:
        assert MetadataCollection.EMPTY.is_empty is True
        assert MetadataCollection().is_empty is True

    def test_is_empty_returns_false_for_non_empty(self) -> None:
        coll = MetadataCollection(_items=(1,))
        assert coll.is_empty is False
        coll_multi = MetadataCollection(_items=(1, 2, 3))
        assert coll_multi.is_empty is False


class TestFlattenDeepMethod:
    def test_flatten_deep_handles_nested_grouped(self) -> None:
        @final
        class NestedGrouped(GroupedMetadata):
            _items: list[object]

            def __init__(self, items: list[object]) -> None:
                self._items = items

            @override
            def __iter__(self) -> "Iterator[object]":
                return iter(self._items)

        # Create nested GroupedMetadata: outer contains inner
        inner = NestedGrouped([3, 4])
        outer = NestedGrouped([1, inner, 2])
        coll = MetadataCollection.of([outer], auto_flatten=False)

        # Single flatten would produce [1, inner, 2]
        single_flat = coll.flatten()
        assert len(single_flat) == 3

        # Deep flatten should fully expand
        deep_flat = coll.flatten_deep()
        assert list(deep_flat) == [1, 3, 4, 2]

    def test_flatten_deep_handles_triple_nested(self) -> None:
        @final
        class NestedGrouped(GroupedMetadata):
            _items: list[object]

            def __init__(self, items: list[object]) -> None:
                self._items = items

            @override
            def __iter__(self) -> "Iterator[object]":
                return iter(self._items)

        innermost = NestedGrouped([5, 6])
        middle = NestedGrouped([3, innermost, 4])
        outer = NestedGrouped([1, middle, 2])
        coll = MetadataCollection.of([outer], auto_flatten=False)
        deep_flat = coll.flatten_deep()
        assert list(deep_flat) == [1, 3, 5, 6, 4, 2]

    def test_flatten_deep_preserves_non_grouped(self) -> None:
        coll = MetadataCollection(_items=("doc", 42, True))
        deep_flat = coll.flatten_deep()
        assert list(deep_flat) == ["doc", 42, True]

    def test_flatten_deep_returns_self_when_no_grouped(self) -> None:
        coll = MetadataCollection(_items=(1, 2, 3))
        deep_flat = coll.flatten_deep()
        assert deep_flat is coll

    def test_flatten_deep_empty_returns_self(self) -> None:
        coll = MetadataCollection.EMPTY
        deep_flat = coll.flatten_deep()
        assert deep_flat is coll

    def test_flatten_deep_same_as_flatten_for_single_level(self) -> None:
        interval = Interval(ge=0, le=10)
        coll = MetadataCollection.of(["doc", interval], auto_flatten=False)
        single_flat = coll.flatten()
        deep_flat = coll.flatten_deep()
        assert list(single_flat) == list(deep_flat)

    def test_flatten_deep_empty_grouped_metadata_returns_empty(self) -> None:
        @final
        class EmptyGrouped(GroupedMetadata):
            @override
            def __iter__(self) -> "Iterator[object]":
                return iter([])

        empty_grouped = EmptyGrouped()
        coll = MetadataCollection.of([empty_grouped], auto_flatten=False)
        deep_flat = coll.flatten_deep()
        assert deep_flat is MetadataCollection.EMPTY


class TestFindProtocol:
    def test_find_protocol_returns_matching_items(self) -> None:
        item1 = ItemWithValue(value=10)
        item2 = ItemWithValue(value=20)
        coll = MetadataCollection(_items=("doc", item1, 42, item2))
        result = coll.find_protocol(HasValue)
        assert list(result) == [item1, item2]

    def test_find_protocol_enables_chaining(self) -> None:
        item1 = ItemWithValue(value=5)
        item2 = ItemWithValue(value=15)
        item3 = ItemWithValue(value=25)
        coll = MetadataCollection(_items=(item1, item2, item3))
        # Ignore: lambda operates on heterogeneous collection items
        result = coll.find_protocol(HasValue).filter(
            lambda x: x.value > 10  # pyright: ignore[reportAttributeAccessIssue,reportUnknownLambdaType,reportUnknownMemberType]
        )
        assert list(result) == [item2, item3]

    def test_find_protocol_raises_for_non_runtime_checkable(self) -> None:
        coll = MetadataCollection(_items=("doc", 42))
        with pytest.raises(ProtocolNotRuntimeCheckableError) as exc_info:
            _ = coll.find_protocol(NotRuntimeCheckable)
        assert exc_info.value.protocol is NotRuntimeCheckable

    def test_find_protocol_raises_for_non_protocol(self) -> None:
        coll = MetadataCollection(_items=("doc", 42))
        with pytest.raises(TypeError, match="NotAProtocol is not a Protocol"):
            _ = coll.find_protocol(NotAProtocol)

    def test_find_protocol_returns_empty_when_no_match(self) -> None:
        coll = MetadataCollection(_items=("doc", 42, True))
        result = coll.find_protocol(HasValue)
        assert result is MetadataCollection.EMPTY

    def test_find_protocol_on_empty_collection(self) -> None:
        coll = MetadataCollection.EMPTY
        result = coll.find_protocol(HasValue)
        assert result is MetadataCollection.EMPTY


class TestHasProtocol:
    def test_has_protocol_returns_true_when_match_exists(self) -> None:
        item = ItemWithValue(value=42)
        coll = MetadataCollection(_items=("doc", item, 100))
        assert coll.has_protocol(HasValue) is True

    def test_has_protocol_returns_false_when_no_match(self) -> None:
        coll = MetadataCollection(_items=("doc", 42, True))
        assert coll.has_protocol(HasValue) is False

    def test_has_protocol_raises_for_non_runtime_checkable(self) -> None:
        coll = MetadataCollection(_items=("doc", 42))
        with pytest.raises(ProtocolNotRuntimeCheckableError) as exc_info:
            _ = coll.has_protocol(NotRuntimeCheckable)
        assert exc_info.value.protocol is NotRuntimeCheckable

    def test_has_protocol_raises_for_non_protocol(self) -> None:
        coll = MetadataCollection(_items=("doc", 42))
        with pytest.raises(TypeError, match="NotAProtocol is not a Protocol"):
            _ = coll.has_protocol(NotAProtocol)

    def test_has_protocol_on_empty_collection(self) -> None:
        coll = MetadataCollection.EMPTY
        assert coll.has_protocol(HasValue) is False


class TestCountProtocol:
    def test_count_protocol_returns_matching_count(self) -> None:
        item1 = ItemWithValue(value=10)
        item2 = ItemWithValue(value=20)
        item3 = ItemWithValue(value=30)
        coll = MetadataCollection(_items=("doc", item1, 42, item2, "end", item3))
        assert coll.count_protocol(HasValue) == 3

    def test_count_protocol_raises_for_non_runtime_checkable(self) -> None:
        coll = MetadataCollection(_items=("doc", 42))
        with pytest.raises(ProtocolNotRuntimeCheckableError) as exc_info:
            _ = coll.count_protocol(NotRuntimeCheckable)
        assert exc_info.value.protocol is NotRuntimeCheckable

    def test_count_protocol_raises_for_non_protocol(self) -> None:
        coll = MetadataCollection(_items=("doc", 42))
        with pytest.raises(TypeError, match="NotAProtocol is not a Protocol"):
            _ = coll.count_protocol(NotAProtocol)

    def test_count_protocol_returns_zero_when_no_match(self) -> None:
        coll = MetadataCollection(_items=("doc", 42, True))
        assert coll.count_protocol(HasValue) == 0

    def test_count_protocol_on_empty_collection(self) -> None:
        coll = MetadataCollection.EMPTY
        assert coll.count_protocol(HasValue) == 0


class TestFilter:
    def test_filter_returns_matching_items(self) -> None:
        coll = MetadataCollection(_items=(1, 2, 3, 4, 5))
        # Ignore: lambda operates on object type, not narrowed int
        result = coll.filter(lambda x: x > 2)  # pyright: ignore[reportOperatorIssue,reportUnknownLambdaType]
        assert list(result) == [3, 4, 5]

    def test_filter_preserves_order(self) -> None:
        coll = MetadataCollection(_items=("a", "bb", "c", "ddd", "ee"))
        # Ignore: lambda operates on object type, not narrowed str
        result = coll.filter(lambda x: len(x) > 1)  # pyright: ignore[reportArgumentType]
        assert list(result) == ["bb", "ddd", "ee"]

    def test_filter_returns_empty_when_none_match(self) -> None:
        coll = MetadataCollection(_items=(1, 2, 3))
        # Ignore: lambda operates on object type, not narrowed int
        result = coll.filter(lambda x: x > 100)  # pyright: ignore[reportOperatorIssue,reportUnknownLambdaType]
        assert result is MetadataCollection.EMPTY

    def test_filter_on_empty_collection(self) -> None:
        coll = MetadataCollection.EMPTY
        result = coll.filter(lambda _: True)
        assert result is MetadataCollection.EMPTY

    def test_filter_returns_collection_type(self) -> None:
        coll = MetadataCollection(_items=(1, 2, 3))
        # Ignore: lambda operates on object type, not narrowed int
        result = coll.filter(lambda x: x > 0)  # pyright: ignore[reportOperatorIssue,reportUnknownLambdaType]
        assert isinstance(result, MetadataCollection)

    def test_filter_with_type_check_predicate(self) -> None:
        coll = MetadataCollection(_items=("doc", 42, True, "end"))
        result = coll.filter(lambda x: isinstance(x, str))
        assert list(result) == ["doc", "end"]


class TestFilterByType:
    def test_filter_by_type_filters_with_typed_predicate(self) -> None:
        item1 = ItemWithValue(value=5)
        item2 = ItemWithValue(value=15)
        item3 = ItemWithValue(value=25)
        coll = MetadataCollection(_items=(item1, "doc", item2, 42, item3))
        result = coll.filter_by_type(ItemWithValue, lambda x: x.value > 10)
        assert list(result) == [item2, item3]

    def test_filter_by_type_only_considers_matching_type(self) -> None:
        item1 = ItemWithValue(value=100)
        coll = MetadataCollection(_items=("doc", 42, item1, True))
        # Predicate only receives ItemWithValue instances
        result = coll.filter_by_type(ItemWithValue, lambda x: x.value > 50)
        assert list(result) == [item1]

    def test_filter_by_type_returns_empty_when_no_type_match(self) -> None:
        coll = MetadataCollection(_items=("doc", 42, True))
        result = coll.filter_by_type(ItemWithValue, lambda _: True)
        assert result is MetadataCollection.EMPTY

    def test_filter_by_type_returns_empty_when_predicate_rejects_all(self) -> None:
        item1 = ItemWithValue(value=5)
        item2 = ItemWithValue(value=10)
        coll = MetadataCollection(_items=(item1, item2))
        result = coll.filter_by_type(ItemWithValue, lambda x: x.value > 100)
        assert result is MetadataCollection.EMPTY

    def test_filter_by_type_on_empty_collection(self) -> None:
        coll = MetadataCollection.EMPTY
        result = coll.filter_by_type(int, lambda _: True)
        assert result is MetadataCollection.EMPTY


class TestFirst:
    def test_first_returns_first_matching_item(self) -> None:
        coll = MetadataCollection(_items=(1, 2, 3, 4, 5))
        # Ignore: lambda operates on object type, not narrowed int
        result = coll.first(lambda x: x > 2)  # pyright: ignore[reportOperatorIssue,reportUnknownLambdaType]
        assert result == 3

    def test_first_returns_none_when_no_match(self) -> None:
        coll = MetadataCollection(_items=(1, 2, 3))
        # Ignore: lambda operates on object type, not narrowed int
        result = coll.first(lambda x: x > 100)  # pyright: ignore[reportOperatorIssue,reportUnknownLambdaType]
        assert result is None

    def test_first_on_empty_collection(self) -> None:
        coll = MetadataCollection.EMPTY
        result = coll.first(lambda _: True)
        assert result is None

    def test_first_stops_at_first_match(self) -> None:
        checked: list[object] = []

        def predicate(x: object) -> bool:
            checked.append(x)
            return x == 3

        coll = MetadataCollection(_items=(1, 2, 3, 4, 5))
        result = coll.first(predicate)
        assert result == 3
        # Should have checked 1, 2, 3 but not 4, 5
        assert checked == [1, 2, 3]


class TestFirstOfType:
    def test_first_of_type_without_predicate_returns_first_of_type(self) -> None:
        item1 = ItemWithValue(value=10)
        item2 = ItemWithValue(value=20)
        coll = MetadataCollection(_items=("doc", item1, 42, item2))
        result = coll.first_of_type(ItemWithValue)
        assert result is item1

    def test_first_of_type_with_predicate_filters_typed_items(self) -> None:
        item1 = ItemWithValue(value=5)
        item2 = ItemWithValue(value=15)
        item3 = ItemWithValue(value=25)
        coll = MetadataCollection(_items=(item1, item2, item3))
        result = coll.first_of_type(ItemWithValue, lambda x: x.value > 10)
        assert result is item2

    def test_first_of_type_returns_none_when_no_type_match(self) -> None:
        coll = MetadataCollection(_items=("doc", 42, True))
        result = coll.first_of_type(ItemWithValue)
        assert result is None

    def test_first_of_type_returns_none_when_predicate_rejects_all(self) -> None:
        item1 = ItemWithValue(value=5)
        item2 = ItemWithValue(value=10)
        coll = MetadataCollection(_items=(item1, item2))
        result = coll.first_of_type(ItemWithValue, lambda x: x.value > 100)
        assert result is None

    def test_first_of_type_on_empty_collection(self) -> None:
        coll = MetadataCollection.EMPTY
        result = coll.first_of_type(int)
        assert result is None

    def test_first_of_type_with_none_predicate_same_as_find(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0), Le(le=100), Ge(ge=10)))
        result_first_of_type = coll.first_of_type(Ge, None)
        result_find = coll.find(Ge)
        assert result_first_of_type == result_find


class TestAny:
    def test_any_returns_true_when_predicate_matches(self) -> None:
        coll = MetadataCollection(_items=(1, 2, 3, 4, 5))
        # Ignore: lambda operates on object type, not narrowed int
        result = coll.any(lambda x: x > 4)  # pyright: ignore[reportOperatorIssue,reportUnknownLambdaType]
        assert result is True

    def test_any_returns_false_when_no_match(self) -> None:
        coll = MetadataCollection(_items=(1, 2, 3))
        # Ignore: lambda operates on object type, not narrowed int
        result = coll.any(lambda x: x > 100)  # pyright: ignore[reportOperatorIssue,reportUnknownLambdaType]
        assert result is False

    def test_any_on_empty_collection(self) -> None:
        coll = MetadataCollection.EMPTY
        result = coll.any(lambda _: True)
        assert result is False

    def test_any_with_type_check(self) -> None:
        coll = MetadataCollection(_items=("doc", 42, True))
        assert coll.any(lambda x: isinstance(x, int)) is True
        assert coll.any(lambda x: isinstance(x, float)) is False

    def test_any_short_circuits_on_first_match(self) -> None:
        checked: list[object] = []

        def predicate(x: object) -> bool:
            checked.append(x)
            return x == 2

        coll = MetadataCollection(_items=(1, 2, 3, 4, 5))
        result = coll.any(predicate)
        assert result is True
        # Should have checked 1, 2 but not 3, 4, 5
        assert checked == [1, 2]


class TestAdd:
    def test_add_concatenates_collections(self) -> None:
        a = MetadataCollection(_items=("x",))
        b = MetadataCollection(_items=("y",))
        result = a + b
        assert isinstance(result, MetadataCollection)
        assert list(result) == ["x", "y"]

    def test_add_with_empty_collection(self) -> None:
        a = MetadataCollection(_items=(1, 2))
        empty = MetadataCollection.EMPTY
        result = a + empty
        assert list(result) == [1, 2]

    def test_add_empty_plus_empty_returns_empty_singleton(self) -> None:
        result = MetadataCollection.EMPTY + MetadataCollection.EMPTY
        assert result is MetadataCollection.EMPTY

    def test_add_returns_not_implemented_for_non_collection(self) -> None:
        coll = MetadataCollection(_items=(1, 2))
        result = coll.__add__([3, 4])
        assert result is NotImplemented


class TestOr:
    def test_or_concatenates_collections(self) -> None:
        a = MetadataCollection(_items=(Ge(ge=0),))
        b = MetadataCollection(_items=(Le(le=100),))
        result = a | b
        assert isinstance(result, MetadataCollection)
        assert list(result) == [Ge(ge=0), Le(le=100)]

    def test_or_behaves_like_add(self) -> None:
        a = MetadataCollection(_items=("x", "y"))
        b = MetadataCollection(_items=("z", "w"))
        add_result = a + b
        or_result = a | b
        assert add_result == or_result
        assert list(add_result) == list(or_result)


class TestExclude:
    def test_exclude_removes_matching_types(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0), "doc", Le(le=100)))
        result = coll.exclude(str)
        assert list(result) == [Ge(ge=0), Le(le=100)]

    def test_exclude_multiple_types(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0), "doc", Le(le=100), 42))
        result = coll.exclude(str, int)
        assert list(result) == [Ge(ge=0), Le(le=100)]

    def test_exclude_all_types_returns_empty(self) -> None:
        coll = MetadataCollection(_items=("a", "b"))
        result = coll.exclude(str)
        assert result is MetadataCollection.EMPTY

    def test_exclude_no_types_returns_self(self) -> None:
        coll = MetadataCollection(_items=(1, 2, 3))
        result = coll.exclude()
        assert result is coll


class TestUnique:
    def test_unique_removes_duplicates(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0), Ge(ge=0), Le(le=100)))
        result = coll.unique()
        assert list(result) == [Ge(ge=0), Le(le=100)]

    def test_unique_preserves_first_occurrence_order(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0), Le(le=100), Ge(ge=0)))
        result = coll.unique()
        assert list(result) == [Ge(ge=0), Le(le=100)]

    def test_unique_handles_unhashable_items(self) -> None:
        coll = MetadataCollection(_items=({"a": 1}, {"a": 1}, {"b": 2}))
        result = coll.unique()
        assert list(result) == [{"a": 1}, {"b": 2}]

    def test_unique_no_duplicates_returns_self(self) -> None:
        coll = MetadataCollection(_items=(1, 2, 3))
        result = coll.unique()
        assert result is coll

    def test_unique_empty_returns_empty_singleton(self) -> None:
        result = MetadataCollection.EMPTY.unique()
        assert result is MetadataCollection.EMPTY


class TestSorted:
    def test_sorted_with_default_key(self) -> None:
        coll = MetadataCollection(_items=(3, 1, 2))
        result = coll.sorted()
        assert isinstance(result, MetadataCollection)
        # Default key is (type_name, repr), so ints sorted by repr
        assert list(result) == [1, 2, 3]

    def test_sorted_with_custom_key(self) -> None:
        coll = MetadataCollection(_items=("bb", "a", "ccc"))
        # Ignore: lambda operates on object type
        result = coll.sorted(key=lambda x: len(x))  # pyright: ignore[reportArgumentType]
        assert list(result) == ["a", "bb", "ccc"]

    def test_sorted_heterogeneous_with_default_key(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0), "doc", Le(le=100)))
        result = coll.sorted()
        # Default key groups by type name, so 'Ge' < 'Le' < 'str'
        type_names = [type(item).__name__ for item in result]
        assert type_names == sorted(type_names)

    def test_sorted_empty_returns_empty_singleton(self) -> None:
        result = MetadataCollection.EMPTY.sorted()
        assert result is MetadataCollection.EMPTY


class TestReversed:
    def test_reversed_returns_items_in_reverse_order(self) -> None:
        coll = MetadataCollection(_items=("a", "b", "c"))
        result = coll.reversed()
        assert isinstance(result, MetadataCollection)
        assert list(result) == ["c", "b", "a"]

    def test_reversed_single_item(self) -> None:
        coll = MetadataCollection(_items=(1,))
        result = coll.reversed()
        assert list(result) == [1]

    def test_reversed_empty_returns_empty_singleton(self) -> None:
        result = MetadataCollection.EMPTY.reversed()
        assert result is MetadataCollection.EMPTY


class TestMap:
    def test_map_applies_function_to_all_items(self) -> None:
        coll = MetadataCollection(_items=(1, 2, 3))
        # Ignore: lambda operates on object type
        result: tuple[object, ...] = coll.map(  # pyright: ignore[reportUnknownVariableType]
            lambda x: x * 2  # pyright: ignore[reportOperatorIssue,reportUnknownLambdaType]
        )
        assert result == (2, 4, 6)

    def test_map_returns_tuple_not_collection(self) -> None:
        coll = MetadataCollection(_items=(1, 2, 3))
        result = coll.map(str)
        assert isinstance(result, tuple)
        assert not isinstance(result, MetadataCollection)
        assert result == ("1", "2", "3")

    def test_map_empty_returns_empty_tuple(self) -> None:
        result = MetadataCollection.EMPTY.map(str)
        assert result == ()


class TestPartition:
    def test_partition_splits_by_predicate(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0), "doc", Le(le=100), "note"))
        matching, non_matching = coll.partition(lambda x: isinstance(x, str))
        assert list(matching) == ["doc", "note"]
        assert list(non_matching) == [Ge(ge=0), Le(le=100)]

    def test_partition_returns_two_collections(self) -> None:
        coll = MetadataCollection(_items=(1, 2, 3, 4, 5))
        # Ignore: lambda operates on object type
        matching, non_matching = coll.partition(lambda x: x % 2 == 0)  # pyright: ignore[reportOperatorIssue,reportUnknownLambdaType]
        assert isinstance(matching, MetadataCollection)
        assert isinstance(non_matching, MetadataCollection)

    def test_partition_all_match_returns_empty_non_matching(self) -> None:
        coll = MetadataCollection(_items=(1, 2, 3))
        matching, non_matching = coll.partition(lambda _: True)
        assert list(matching) == [1, 2, 3]
        assert non_matching is MetadataCollection.EMPTY

    def test_partition_none_match_returns_empty_matching(self) -> None:
        coll = MetadataCollection(_items=(1, 2, 3))
        matching, non_matching = coll.partition(lambda _: False)
        assert matching is MetadataCollection.EMPTY
        assert list(non_matching) == [1, 2, 3]


class TestTypes:
    def test_types_returns_unique_types(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0), Ge(ge=10), "doc"))
        result = coll.types()
        assert isinstance(result, frozenset)
        assert result == frozenset({type(Ge(ge=0)), str})

    def test_types_empty_returns_empty_frozenset(self) -> None:
        result = MetadataCollection.EMPTY.types()
        assert result == frozenset()


class TestByType:
    def test_by_type_groups_items_by_type(self) -> None:
        coll = MetadataCollection(_items=(Ge(ge=0), "a", Ge(ge=10), "b"))
        result = coll.by_type()
        assert result[type(Ge(ge=0))] == (Ge(ge=0), Ge(ge=10))
        assert result[str] == ("a", "b")

    def test_by_type_returns_immutable_mapping(self) -> None:
        coll = MetadataCollection(_items=(1, 2, "a"))
        result = coll.by_type()
        # MappingProxyType doesn't support item assignment
        with pytest.raises(TypeError):
            result[int] = (3, 4)  # pyright: ignore[reportIndexIssue]

    def test_by_type_empty_returns_empty_mapping(self) -> None:
        result = MetadataCollection.EMPTY.by_type()
        assert len(result) == 0
