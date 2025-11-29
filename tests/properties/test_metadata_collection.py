# ruff: noqa: SLF001

from typing import TYPE_CHECKING, cast

from hypothesis import given, settings, strategies as st

from typing_graph._metadata import MetadataCollection

if TYPE_CHECKING:
    from hypothesis.strategies import DrawFn


@st.composite
def hashable_items(draw: "DrawFn") -> object:
    """Generate hashable items for MetadataCollection."""
    return cast(
        "object",
        draw(
            st.one_of(
                st.text(min_size=0, max_size=20),
                st.integers(-100, 100),
                st.booleans(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.none(),
                st.tuples(st.integers(), st.integers()),
                st.frozensets(st.integers(0, 10), max_size=3),
            )
        ),
    )


@st.composite
def unhashable_items(draw: "DrawFn") -> object:
    """Generate unhashable items for MetadataCollection."""
    return cast(
        "object",
        draw(
            st.one_of(
                st.lists(st.integers(), max_size=5),
                st.dictionaries(st.text(max_size=5), st.integers(), max_size=3),
                st.lists(st.text(max_size=5), max_size=3),
            )
        ),
    )


@st.composite
def metadata_items(draw: "DrawFn") -> object:
    """Generate any metadata items (hashable or unhashable)."""
    return draw(st.one_of(hashable_items(), unhashable_items()))


@st.composite
def metadata_collections(draw: "DrawFn", max_size: int = 10) -> MetadataCollection:
    """Generate MetadataCollection instances with random items."""
    items: list[object] = draw(st.lists(metadata_items(), max_size=max_size))
    return MetadataCollection(_items=tuple(items))


@st.composite
def hashable_metadata_collections(
    draw: "DrawFn", max_size: int = 10
) -> MetadataCollection:
    """Generate MetadataCollection instances with only hashable items."""
    items: list[object] = draw(st.lists(hashable_items(), max_size=max_size))
    return MetadataCollection(_items=tuple(items))


@st.composite
def slice_indices(draw: "DrawFn", max_len: int = 20) -> slice:
    """Generate slice objects for testing __getitem__."""
    start: int | None = draw(st.none() | st.integers(-max_len * 2, max_len * 2))
    stop: int | None = draw(st.none() | st.integers(-max_len * 2, max_len * 2))
    step: int | None = draw(st.none() | st.integers(1, 5))
    return slice(start, stop, step)


class TestImmutabilityProperties:
    @given(metadata_collections())
    @settings(deadline=None)
    def test_immutability_no_public_mutation_methods(
        self, coll: MetadataCollection
    ) -> None:
        original_items = coll._items
        original_len = len(coll)

        # Access various methods - none should mutate
        _ = len(coll)
        _ = bool(coll)
        _ = list(coll)
        if coll:
            _ = coll[0]
        _ = coll[:]
        _ = repr(coll)
        _ = coll.is_hashable
        for _ in coll:
            pass

        # Verify nothing changed
        assert coll._items is original_items
        assert len(coll) == original_len

    @given(
        st.lists(hashable_items(), min_size=2, max_size=10),
        slice_indices(),
    )
    @settings(deadline=None)
    def test_transformation_returns_new_collection(
        self, items: list[object], slc: slice
    ) -> None:
        coll = MetadataCollection(_items=tuple(items))
        sliced = coll[slc]

        # Slice always returns a MetadataCollection
        assert isinstance(sliced, MetadataCollection)

        # If slice is non-empty and not the whole collection, it's a new instance
        # (unless it matches EMPTY singleton)
        if len(sliced) == 0:
            assert sliced is MetadataCollection.EMPTY
        elif list(sliced) != list(coll):
            assert sliced is not coll


class TestSequenceInvariants:
    @given(metadata_collections())
    @settings(deadline=None)
    def test_len_equals_iteration_count(self, coll: MetadataCollection) -> None:
        iteration_count = sum(1 for _ in coll)
        assert len(coll) == iteration_count

    @given(metadata_collections(), metadata_items())
    @settings(deadline=None)
    def test_contains_consistent_with_iteration(
        self, coll: MetadataCollection, item: object
    ) -> None:
        in_iteration = any(x == item for x in coll)
        in_contains = item in coll
        assert in_contains == in_iteration

    @given(
        st.lists(hashable_items(), min_size=1, max_size=10),
        slice_indices(),
    )
    @settings(deadline=None)
    def test_getitem_slice_preserves_relative_order(
        self, items: list[object], slc: slice
    ) -> None:
        coll = MetadataCollection(_items=tuple(items))
        sliced = coll[slc]

        # Compare with expected Python slice behavior
        expected = items[slc]
        assert list(sliced) == expected


class TestEqualityProperties:
    @given(metadata_collections())
    @settings(deadline=None)
    def test_equality_reflexive(self, coll: MetadataCollection) -> None:
        # Using explicit comparison to test __eq__ behavior
        assert coll.__eq__(coll) is True

    @given(metadata_collections(), metadata_collections())
    @settings(deadline=None)
    def test_equality_symmetric(
        self, a: MetadataCollection, b: MetadataCollection
    ) -> None:
        if a == b:
            assert b == a
        else:
            assert b != a


class TestHashingProperties:
    @given(hashable_metadata_collections())
    @settings(deadline=None)
    def test_hash_deterministic(self, coll: MetadataCollection) -> None:
        h1 = hash(coll)
        h2 = hash(coll)
        h3 = hash(coll)
        assert h1 == h2 == h3

    @given(hashable_metadata_collections(), hashable_metadata_collections())
    @settings(deadline=None)
    def test_hash_consistency_with_equality(
        self, a: MetadataCollection, b: MetadataCollection
    ) -> None:
        if a == b:
            assert hash(a) == hash(b)
        # Note: hash(a) == hash(b) does NOT imply a == b (hash collisions allowed)


class TestSingletonProperties:
    def test_empty_singleton_initialization_safe(self) -> None:
        # Test that EMPTY is available immediately after import
        assert MetadataCollection.EMPTY is not None
        assert len(MetadataCollection.EMPTY) == 0
        assert MetadataCollection.EMPTY._items == ()

        # Multiple accesses return same object
        empty1 = MetadataCollection.EMPTY
        empty2 = MetadataCollection.EMPTY
        assert empty1 is empty2

    @given(st.integers(1, 100))
    @settings(deadline=None)
    def test_empty_singleton_consistent_across_accesses(self, n: int) -> None:
        empties = [MetadataCollection.EMPTY for _ in range(n)]
        first = empties[0]
        assert all(e is first for e in empties)


class TestOfFactoryProperties:
    @given(st.lists(hashable_items(), max_size=20))
    @settings(deadline=None)
    def test_of_roundtrip_preserves_items(self, items: list[object]) -> None:
        # Items without GroupedMetadata should roundtrip exactly
        coll = MetadataCollection.of(items, auto_flatten=False)
        assert list(coll) == items

    @given(st.lists(hashable_items(), max_size=20))
    @settings(deadline=None)
    def test_of_length_matches_input_when_no_grouped(self, items: list[object]) -> None:
        coll = MetadataCollection.of(items, auto_flatten=False)
        assert len(coll) == len(items)


class TestQueryMethodProperties:
    @given(metadata_collections())
    @settings(deadline=None)
    def test_find_none_implies_has_false(self, coll: MetadataCollection) -> None:
        # If find returns None for a type, has should return False
        if coll.find(int) is None:
            assert coll.has(int) is False
        if coll.find(str) is None:
            assert coll.has(str) is False
        if coll.find(float) is None:
            assert coll.has(float) is False

    @given(metadata_collections())
    @settings(deadline=None)
    def test_count_equals_find_all_length(self, coll: MetadataCollection) -> None:
        # count(T) should equal len(list(find_all(T)))
        assert coll.count(int) == len(list(coll.find_all(int)))
        assert coll.count(str) == len(list(coll.find_all(str)))
        assert coll.count(float) == len(list(coll.find_all(float)))

    @given(metadata_collections())
    @settings(deadline=None)
    def test_has_equals_count_positive(self, coll: MetadataCollection) -> None:
        # has(T) should equal count(T) > 0
        assert coll.has(int) == (coll.count(int) > 0)
        assert coll.has(str) == (coll.count(str) > 0)
        assert coll.has(float) == (coll.count(float) > 0)

    @given(metadata_collections())
    @settings(deadline=None)
    def test_find_all_idempotence(self, coll: MetadataCollection) -> None:
        # find_all(T).find_all(T) should equal find_all(T)
        first_pass = coll.find_all(int)
        second_pass = first_pass.find_all(int)
        assert list(first_pass) == list(second_pass)

    @given(metadata_collections())
    @settings(deadline=None)
    def test_get_equals_find_with_none_default(self, coll: MetadataCollection) -> None:
        # get(T) should equal find(T) when no default provided
        assert coll.get(int) == coll.find(int)
        assert coll.get(str) == coll.find(str)
        assert coll.get(float) == coll.find(float)

    @given(metadata_collections())
    @settings(deadline=None)
    def test_is_empty_equals_len_zero(self, coll: MetadataCollection) -> None:
        # is_empty should equal len(coll) == 0
        assert coll.is_empty == (len(coll) == 0)

    @given(metadata_collections())
    @settings(deadline=None)
    def test_find_all_no_args_returns_all_items(self, coll: MetadataCollection) -> None:
        # find_all() with no args should return all items
        result = coll.find_all()
        assert list(result) == list(coll)

    @given(metadata_collections())
    @settings(deadline=None)
    def test_has_with_no_types_returns_false(self, coll: MetadataCollection) -> None:
        # has() with no arguments should always return False
        assert coll.has() is False

    @given(metadata_collections())
    @settings(deadline=None)
    def test_count_with_no_types_returns_zero(self, coll: MetadataCollection) -> None:
        # count() with no arguments should always return 0
        assert coll.count() == 0

    @given(metadata_collections())
    @settings(deadline=None)
    def test_find_first_no_args_returns_none(self, coll: MetadataCollection) -> None:
        # find_first() with no arguments should always return None
        assert coll.find_first() is None


class TestFlattenProperties:
    @given(st.lists(hashable_items(), max_size=20))
    @settings(deadline=None)
    def test_flatten_idempotent(self, items: list[object]) -> None:
        coll = MetadataCollection.of(items, auto_flatten=False)
        once = coll.flatten()
        twice = once.flatten()
        assert list(once) == list(twice)

    @given(st.lists(hashable_items(), max_size=20))
    @settings(deadline=None)
    def test_flatten_deep_idempotent(self, items: list[object]) -> None:
        coll = MetadataCollection.of(items, auto_flatten=False)
        once = coll.flatten_deep()
        twice = once.flatten_deep()
        assert list(once) == list(twice)

    @given(st.lists(hashable_items(), max_size=20))
    @settings(deadline=None)
    def test_flatten_preserves_non_grouped_items(self, items: list[object]) -> None:
        # Items without GroupedMetadata should be unchanged by flatten
        coll = MetadataCollection.of(items, auto_flatten=False)
        flattened = coll.flatten()
        assert list(flattened) == items

    @given(st.lists(hashable_items(), max_size=20))
    @settings(deadline=None)
    def test_flatten_deep_preserves_non_grouped(self, items: list[object]) -> None:
        # Items without GroupedMetadata should be unchanged by flatten_deep
        coll = MetadataCollection.of(items, auto_flatten=False)
        flattened = coll.flatten_deep()
        assert list(flattened) == items
