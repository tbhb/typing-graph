# pyright: reportAny=false, reportExplicitAny=false
# pyright: reportAttributeAccessIssue=false
# ruff: noqa: SLF001

from typing import TYPE_CHECKING

from hypothesis import given, settings, strategies as st

from typing_graph._metadata import MetadataCollection

if TYPE_CHECKING:
    from hypothesis.strategies import DrawFn


# =============================================================================
# Custom Hypothesis Strategies for MetadataCollection
# =============================================================================


@st.composite
def hashable_items(draw: "DrawFn") -> object:
    """Generate hashable items for MetadataCollection."""
    return draw(
        st.one_of(
            st.text(min_size=0, max_size=20),
            st.integers(-100, 100),
            st.booleans(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.none(),
            st.tuples(st.integers(), st.integers()),
            st.frozensets(st.integers(0, 10), max_size=3),
        )
    )


@st.composite
def unhashable_items(draw: "DrawFn") -> object:
    """Generate unhashable items for MetadataCollection."""
    return draw(
        st.one_of(
            st.lists(st.integers(), max_size=5),
            st.dictionaries(st.text(max_size=5), st.integers(), max_size=3),
            st.lists(st.text(max_size=5), max_size=3),
        )
    )


@st.composite
def metadata_items(draw: "DrawFn") -> object:
    """Generate any metadata items (hashable or unhashable)."""
    return draw(st.one_of(hashable_items(), unhashable_items()))


@st.composite
def metadata_collections(draw: "DrawFn", max_size: int = 10) -> MetadataCollection:
    """Generate MetadataCollection instances with random items."""
    items = draw(st.lists(metadata_items(), max_size=max_size))
    return MetadataCollection(_items=tuple(items))


@st.composite
def hashable_metadata_collections(
    draw: "DrawFn", max_size: int = 10
) -> MetadataCollection:
    """Generate MetadataCollection instances with only hashable items."""
    items = draw(st.lists(hashable_items(), max_size=max_size))
    return MetadataCollection(_items=tuple(items))


@st.composite
def slice_indices(draw: "DrawFn", max_len: int = 20) -> slice:
    """Generate slice objects for testing __getitem__."""
    start = draw(st.none() | st.integers(-max_len * 2, max_len * 2))
    stop = draw(st.none() | st.integers(-max_len * 2, max_len * 2))
    step = draw(st.none() | st.integers(1, 5))
    return slice(start, stop, step)


# =============================================================================
# Property Tests - Immutability (MC-103, MC-104, MC-105)
# =============================================================================


class TestImmutabilityProperties:
    # MC-103
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

    # MC-105
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


# =============================================================================
# Property Tests - Sequence Invariants (MC-109, MC-110, MC-130)
# =============================================================================


class TestSequenceInvariants:
    # MC-109
    @given(metadata_collections())
    @settings(deadline=None)
    def test_len_equals_iteration_count(self, coll: MetadataCollection) -> None:
        iteration_count = sum(1 for _ in coll)
        assert len(coll) == iteration_count

    # MC-110
    @given(metadata_collections(), metadata_items())
    @settings(deadline=None)
    def test_contains_consistent_with_iteration(
        self, coll: MetadataCollection, item: object
    ) -> None:
        in_iteration = any(x == item for x in coll)
        in_contains = item in coll
        assert in_contains == in_iteration

    # MC-130
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


# =============================================================================
# Property Tests - Equality (MC-122, MC-123)
# =============================================================================


class TestEqualityProperties:
    # MC-122
    @given(metadata_collections())
    @settings(deadline=None)
    def test_equality_reflexive(self, coll: MetadataCollection) -> None:
        # Using explicit comparison to test __eq__ behavior
        assert coll.__eq__(coll) is True

    # MC-123
    @given(metadata_collections(), metadata_collections())
    @settings(deadline=None)
    def test_equality_symmetric(
        self, a: MetadataCollection, b: MetadataCollection
    ) -> None:
        if a == b:
            assert b == a
        else:
            assert b != a


# =============================================================================
# Property Tests - Hashing (MC-124, MC-125)
# =============================================================================


class TestHashingProperties:
    # MC-124
    @given(hashable_metadata_collections())
    @settings(deadline=None)
    def test_hash_deterministic(self, coll: MetadataCollection) -> None:
        h1 = hash(coll)
        h2 = hash(coll)
        h3 = hash(coll)
        assert h1 == h2 == h3

    # MC-125
    @given(hashable_metadata_collections(), hashable_metadata_collections())
    @settings(deadline=None)
    def test_hash_consistency_with_equality(
        self, a: MetadataCollection, b: MetadataCollection
    ) -> None:
        if a == b:
            assert hash(a) == hash(b)
        # Note: hash(a) == hash(b) does NOT imply a == b (hash collisions allowed)


# =============================================================================
# Property Tests - Singleton Safety (MC-129)
# =============================================================================


class TestSingletonProperties:
    # MC-129
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
