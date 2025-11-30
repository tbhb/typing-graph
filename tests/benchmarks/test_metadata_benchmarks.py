from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, Protocol, runtime_checkable
from typing_extensions import override

from annotated_types import GroupedMetadata

from typing_graph import MetadataCollection

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pytest_benchmark.fixture import BenchmarkFixture


# Marker classes (10 distinct types for type diversity)
class MarkerA:
    pass


class MarkerB:
    pass


class MarkerC:
    pass


class MarkerD:
    pass


class MarkerE:
    pass


class MarkerF:
    pass


class MarkerG:
    pass


class MarkerH:
    pass


class MarkerI:
    pass


class MarkerJ:
    pass


# List of all marker types for easy iteration
MARKER_TYPES: tuple[type, ...] = (
    MarkerA,
    MarkerB,
    MarkerC,
    MarkerD,
    MarkerE,
    MarkerF,
    MarkerG,
    MarkerH,
    MarkerI,
    MarkerJ,
)

# Error message constant for UnhashableMarker
_UNHASHABLE_ERROR_MSG = "unhashable type: 'UnhashableMarker'"


# Specialized marker types
@dataclass(slots=True, frozen=True)
class HashableMarker:
    """Hashable marker for benchmarking hash-dependent operations."""

    value: int


class UnhashableMarker:
    """Unhashable marker for benchmarking fallback paths."""

    value: list[object]

    def __init__(self, value: list[object]) -> None:
        self.value = value

    @override
    def __hash__(self) -> int:
        raise TypeError(_UNHASHABLE_ERROR_MSG)

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UnhashableMarker):
            return NotImplemented
        return self.value == other.value


@dataclass(slots=True, frozen=True)
class SortableMarker:
    """Sortable marker for benchmarking sort operations."""

    priority: int

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, SortableMarker):
            return NotImplemented
        return self.priority < other.priority


@dataclass(slots=True, frozen=True)
class ReversePrioritySortKey:
    """Sort key that orders by negative priority (reverse order)."""

    value: int

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, ReversePrioritySortKey):
            return NotImplemented
        return self.value < other.value


# Protocol fixtures
@runtime_checkable
class SupportsValidate(Protocol):
    """Protocol for types that support validation."""

    def validate(self) -> bool: ...


class ValidatorImpl:
    """Implementation of SupportsValidate protocol."""

    def validate(self) -> bool:
        return True


class NonValidator:
    """Class that does not implement SupportsValidate."""


@dataclass(slots=True, frozen=True)
class BenchGroupedMetadata(GroupedMetadata):
    """Grouped metadata implementation for benchmarking flattening."""

    items: tuple[object, ...]

    @override
    def __iter__(self) -> "Iterator[object]":
        return iter(self.items)


# Collection generator functions
def create_collection(size: int, types: int = 1) -> MetadataCollection:
    """Create a collection with the specified size and number of types.

    Args:
        size: Number of items in the collection.
        types: Number of distinct marker types to use (1-10).

    Returns:
        MetadataCollection with the specified number of items.
    """
    if types < 1 or types > len(MARKER_TYPES):
        msg = f"types must be between 1 and {len(MARKER_TYPES)}"
        raise ValueError(msg)

    items = [MARKER_TYPES[i % types]() for i in range(size)]
    return MetadataCollection.of(items)


def create_collection_with_target_at(
    size: int, position: int | None
) -> tuple[MetadataCollection, type]:
    """Create collection with target type at specified position.

    Args:
        size: Total number of items in the collection.
        position: Index where target type should appear (None = no target).

    Returns:
        Tuple of (collection, target_type) where target_type is the type
        at the specified position, or a type not in the collection if
        position is None.
    """
    target_type = MarkerA
    filler_type = MarkerB

    items: list[object] = []
    for i in range(size):
        if position is not None and i == position:
            items.append(target_type())
        else:
            items.append(filler_type())

    collection = MetadataCollection.of(items)

    # If position is None, return a type not in the collection
    if position is None:
        return collection, MarkerC

    return collection, target_type


def create_multi_type_collection(
    size: int,
    type_count: int,
    match_percentage: float = 0.1,
) -> MetadataCollection:
    """Create collection with multiple types and specified match rate.

    Args:
        size: Total number of items in the collection.
        type_count: Number of distinct types to use as "matching" types.
        match_percentage: Percentage of items that should be matching types.

    Returns:
        MetadataCollection with specified type distribution.
    """
    if type_count > len(MARKER_TYPES):
        msg = f"type_count must be <= {len(MARKER_TYPES)}"
        raise ValueError(msg)

    match_count = int(size * match_percentage)
    filler_count = size - match_count

    # Add matching type items (distributed among type_count types)
    items: list[object] = [MARKER_TYPES[i % type_count]() for i in range(match_count)]

    # Add filler items using a type not in the match set
    # Use HashableMarker as filler to ensure it's a different type
    items.extend(HashableMarker(value=i) for i in range(filler_count))

    return MetadataCollection.of(items)


def create_collection_with_duplicates(
    size: int,
    duplicate_rate: float = 0.3,
) -> MetadataCollection:
    """Create collection with specified duplicate rate.

    Args:
        size: Total number of items in the collection.
        duplicate_rate: Fraction of items that should be duplicates (0.0 to <1.0).

    Returns:
        MetadataCollection with specified duplicate rate.

    Raises:
        ValueError: If duplicate_rate is not in range [0.0, 1.0).
    """
    if not 0.0 <= duplicate_rate < 1.0:
        msg = "duplicate_rate must be in range [0.0, 1.0)"
        raise ValueError(msg)

    unique_count = int(size * (1 - duplicate_rate))
    duplicate_count = size - unique_count

    # Add unique items
    items = [HashableMarker(value=i) for i in range(unique_count)]

    # Add duplicate items (repeat from the beginning)
    items.extend(HashableMarker(value=i % unique_count) for i in range(duplicate_count))

    return MetadataCollection.of(items)


def create_grouped_collection(
    item_count: int, grouped_count: int
) -> MetadataCollection | None:
    """Create collection with GroupedMetadata items.

    Args:
        item_count: Number of regular items.
        grouped_count: Number of GroupedMetadata items to include.

    Returns:
        MetadataCollection with GroupedMetadata items, or None if
        annotated-types is not available.
    """

    # Add regular items
    items: list[object] = [HashableMarker(value=i) for i in range(item_count)]

    # Add grouped items
    for _ in range(grouped_count):
        # Each GroupedMetadata contains 3 items
        grouped = BenchGroupedMetadata(
            items=(
                MarkerA(),
                MarkerB(),
                MarkerC(),
            )
        )
        items.append(grouped)

    return MetadataCollection.of(items, auto_flatten=False)


def create_collection_with_unhashable(
    size: int,
    unhashable_position: int = 0,
) -> MetadataCollection:
    """Create collection with an unhashable item at specified position.

    Args:
        size: Total number of items in the collection.
        unhashable_position: Index where unhashable item should appear.

    Returns:
        MetadataCollection with one unhashable item.
    """
    items: list[object] = []
    for i in range(size):
        if i == unhashable_position:
            items.append(UnhashableMarker(value=[i]))
        else:
            items.append(HashableMarker(value=i))
    return MetadataCollection.of(items)


def create_validator_collection(
    size: int,
    validator_count: int,
) -> MetadataCollection:
    """Create collection with ValidatorImpl items for protocol benchmarks.

    Args:
        size: Total number of items in the collection.
        validator_count: Number of ValidatorImpl instances to include.

    Returns:
        MetadataCollection with validators and non-validators.
    """
    # Add validators
    items: list[object] = [ValidatorImpl() for _ in range(validator_count)]

    # Fill remaining with non-validators
    items.extend(NonValidator() for _ in range(size - validator_count))

    return MetadataCollection.of(items)


class TestConstructionBenchmarks:
    def test_bench_of_construction_small(self, benchmark: "BenchmarkFixture") -> None:
        items = [MARKER_TYPES[i % len(MARKER_TYPES)]() for i in range(5)]

        result = benchmark(MetadataCollection.of, items)

        assert len(result) == 5
        assert not result.is_empty

    def test_bench_of_construction_medium(self, benchmark: "BenchmarkFixture") -> None:
        items = [MARKER_TYPES[i % len(MARKER_TYPES)]() for i in range(50)]

        result = benchmark(MetadataCollection.of, items)

        assert len(result) == 50

    def test_bench_of_construction_large(self, benchmark: "BenchmarkFixture") -> None:
        items = [MARKER_TYPES[i % len(MARKER_TYPES)]() for i in range(500)]

        result = benchmark(MetadataCollection.of, items)

        assert len(result) == 500

    def test_bench_from_annotated_simple(self, benchmark: "BenchmarkFixture") -> None:
        annotated_type = Annotated[int, MarkerA(), MarkerB(), MarkerC()]

        result = benchmark(MetadataCollection.from_annotated, annotated_type)

        assert len(result) == 3

    def test_bench_from_annotated_nested(self, benchmark: "BenchmarkFixture") -> None:
        # Note: Python flattens nested Annotated at definition time
        inner = Annotated[int, MarkerA(), MarkerB()]
        middle = Annotated[inner, MarkerC(), MarkerD()]
        outer = Annotated[middle, MarkerE(), MarkerF()]

        result = benchmark(MetadataCollection.from_annotated, outer)

        # All 6 metadata items should be collected
        assert len(result) == 6

    def test_bench_empty_singleton_access(self, benchmark: "BenchmarkFixture") -> None:
        result = benchmark(lambda: MetadataCollection.EMPTY)

        assert result is MetadataCollection.EMPTY
        assert result.is_empty

    def test_bench_of_with_auto_flatten(self, benchmark: "BenchmarkFixture") -> None:
        # 10 regular items + 3 grouped (each with 3 items) = 19 total after flatten
        items: list[object] = [HashableMarker(value=i) for i in range(10)]
        for _ in range(3):
            grouped = BenchGroupedMetadata(items=(MarkerA(), MarkerB(), MarkerC()))
            items.append(grouped)

        result = benchmark(lambda: MetadataCollection.of(items, auto_flatten=True))

        # 10 + (3 * 3) = 19 items after flattening
        assert len(result) == 19

    def test_bench_of_without_auto_flatten(self, benchmark: "BenchmarkFixture") -> None:
        # 10 regular items + 3 grouped = 13 total (grouped not expanded)
        items: list[object] = [HashableMarker(value=i) for i in range(10)]
        for _ in range(3):
            grouped = BenchGroupedMetadata(items=(MarkerA(), MarkerB(), MarkerC()))
            items.append(grouped)

        result = benchmark(lambda: MetadataCollection.of(items, auto_flatten=False))

        # 10 + 3 = 13 items (grouped preserved)
        assert len(result) == 13


class TestQueryBenchmarks:
    def test_bench_find_first_item(self, benchmark: "BenchmarkFixture") -> None:
        # Target at first position - O(1) best case
        collection, target_type = create_collection_with_target_at(100, 0)

        result = benchmark(collection.find, target_type)

        assert result is not None
        assert isinstance(result, target_type)

    def test_bench_find_last_item(self, benchmark: "BenchmarkFixture") -> None:
        # Target at last position - O(n) worst case
        collection, target_type = create_collection_with_target_at(100, 99)

        result = benchmark(collection.find, target_type)

        assert result is not None
        assert isinstance(result, target_type)

    def test_bench_find_no_match(self, benchmark: "BenchmarkFixture") -> None:
        # No matching item - O(n)
        collection, target_type = create_collection_with_target_at(100, None)

        result = benchmark(collection.find, target_type)

        assert result is None

    def test_bench_find_all_single_type(self, benchmark: "BenchmarkFixture") -> None:
        # Single type with 10% matches
        collection = create_multi_type_collection(
            100, type_count=1, match_percentage=0.1
        )

        result = benchmark(collection.find_all, MarkerA)

        assert len(result) == 10

    def test_bench_find_all_multiple_types(self, benchmark: "BenchmarkFixture") -> None:
        # Multiple types with 30% matches
        collection = create_multi_type_collection(
            100, type_count=3, match_percentage=0.3
        )

        result = benchmark(collection.find_all, MarkerA, MarkerB, MarkerC)

        assert len(result) == 30

    def test_bench_has_positive(self, benchmark: "BenchmarkFixture") -> None:
        # Target at mid-position
        collection, target_type = create_collection_with_target_at(100, 50)

        result = benchmark(collection.has, target_type)

        assert result is True

    def test_bench_has_negative(self, benchmark: "BenchmarkFixture") -> None:
        # Non-existing target - O(n)
        collection, target_type = create_collection_with_target_at(100, None)

        result = benchmark(collection.has, target_type)

        assert result is False

    def test_bench_filter_by_type_selective(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        # 20% type match, 50% predicate match
        items: list[object] = [HashableMarker(value=i) for i in range(20)]
        items.extend(MarkerA() for _ in range(80))
        collection = MetadataCollection.of(items)

        # Predicate matches 50% of HashableMarker items (value < 10)
        def predicate(m: HashableMarker) -> bool:
            return m.value < 10

        result = benchmark(collection.filter_by_type, HashableMarker, predicate)

        assert len(result) == 10

    def test_bench_count_multiple_types(self, benchmark: "BenchmarkFixture") -> None:
        # 3 types with 30% matches
        collection = create_multi_type_collection(
            100, type_count=3, match_percentage=0.3
        )

        result = benchmark(collection.count, MarkerA, MarkerB, MarkerC)

        assert result == 30

    def test_bench_get_required_success(self, benchmark: "BenchmarkFixture") -> None:
        # Target at mid-position
        collection, target_type = create_collection_with_target_at(100, 50)

        result = benchmark(collection.get_required, target_type)

        assert isinstance(result, target_type)


class TestProtocolFilteringBenchmarks:
    def test_bench_find_protocol_small(self, benchmark: "BenchmarkFixture") -> None:
        # Small collection with ~30% validators
        collection = create_validator_collection(10, validator_count=3)

        result = benchmark(collection.find_protocol, SupportsValidate)

        assert len(result) == 3
        assert all(isinstance(item, ValidatorImpl) for item in result)

    def test_bench_find_protocol_large(self, benchmark: "BenchmarkFixture") -> None:
        # Large collection with ~30% validators
        collection = create_validator_collection(100, validator_count=30)

        result = benchmark(collection.find_protocol, SupportsValidate)

        assert len(result) == 30
        assert all(isinstance(item, ValidatorImpl) for item in result)

    def test_bench_has_protocol(self, benchmark: "BenchmarkFixture") -> None:
        # Validator in middle for average-case performance
        collection = create_validator_collection(100, validator_count=1)

        result = benchmark(collection.has_protocol, SupportsValidate)

        assert result is True


class TestOperationsBenchmarks:
    def test_bench_combine_small(self, benchmark: "BenchmarkFixture") -> None:
        # Two small collections (5 + 5 items)
        left = create_collection(5, types=5)
        right = create_collection(5, types=5)

        result = benchmark(lambda: left + right)

        assert len(result) == 10

    def test_bench_combine_medium(self, benchmark: "BenchmarkFixture") -> None:
        # Two medium collections (50 + 50 items)
        left = create_collection(50, types=10)
        right = create_collection(50, types=10)

        result = benchmark(lambda: left + right)

        assert len(result) == 100

    def test_bench_union_operator(self, benchmark: "BenchmarkFixture") -> None:
        left = create_collection(50, types=10)
        right = create_collection(50, types=10)

        result = benchmark(lambda: left | right)

        assert len(result) == 100

    def test_bench_sorted_default_key(self, benchmark: "BenchmarkFixture") -> None:
        # Default key uses (type_name, repr) for stable heterogeneous sorting
        items = [SortableMarker(priority=i % 20) for i in range(100)]
        collection = MetadataCollection.of(items)

        result = benchmark(collection.sorted)

        assert len(result) == 100
        # Verify all items are preserved (default key sorts by type_name, repr)
        result_set = {(type(m).__name__, m.priority) for m in result}
        original_set = {(type(m).__name__, m.priority) for m in items}
        assert result_set == original_set

    def test_bench_sorted_custom_key(self, benchmark: "BenchmarkFixture") -> None:
        items = [SortableMarker(priority=i % 20) for i in range(100)]
        collection = MetadataCollection.of(items)

        def reverse_priority_key(m: object) -> ReversePrioritySortKey:
            # Return key object for proper SupportsLessThan compatibility
            if isinstance(m, SortableMarker):
                return ReversePrioritySortKey(value=-m.priority)
            return ReversePrioritySortKey(value=0)

        # Use lambda wrapper for keyword argument
        result = benchmark(lambda: collection.sorted(key=reverse_priority_key))

        assert len(result) == 100
        # Verify reverse sorted order
        priorities = [m.priority for m in result]
        assert priorities == sorted(priorities, reverse=True)

    def test_bench_unique_hashable(self, benchmark: "BenchmarkFixture") -> None:
        # 30% duplicate rate
        collection = create_collection_with_duplicates(100, duplicate_rate=0.3)

        result = benchmark(collection.unique)

        # With 30% duplicates of 100 items: ~70 unique
        assert len(result) == 70

    def test_bench_unique_unhashable(self, benchmark: "BenchmarkFixture") -> None:
        # 50 UnhashableMarker items with 30% duplicates - O(n^2) worst case
        unique_count = int(50 * 0.7)  # 35 unique
        duplicate_count = 50 - unique_count  # 15 duplicates

        items: list[object] = [UnhashableMarker(value=[i]) for i in range(unique_count)]
        items.extend(
            UnhashableMarker(value=[i % unique_count]) for i in range(duplicate_count)
        )
        collection = MetadataCollection.of(items)

        result = benchmark(collection.unique)

        assert len(result) == unique_count

    def test_bench_map_transformation(self, benchmark: "BenchmarkFixture") -> None:
        items = [HashableMarker(value=i) for i in range(100)]
        collection = MetadataCollection.of(items)

        def transform(m: object) -> object:
            if isinstance(m, HashableMarker):
                return HashableMarker(value=m.value * 2)
            return m

        result = benchmark(collection.map, transform)

        assert len(result) == 100

    def test_bench_partition(self, benchmark: "BenchmarkFixture") -> None:
        items = [HashableMarker(value=i) for i in range(100)]
        collection = MetadataCollection.of(items)

        def predicate(m: object) -> bool:
            return isinstance(m, HashableMarker) and m.value < 50

        result = benchmark(collection.partition, predicate)

        matching, non_matching = result
        assert len(matching) == 50
        assert len(non_matching) == 50

    def test_bench_exclude_single_type(self, benchmark: "BenchmarkFixture") -> None:
        # 10% MarkerA, 90% other types
        items: list[object] = [MarkerA() for _ in range(10)]
        items.extend(HashableMarker(value=i) for i in range(90))
        collection = MetadataCollection.of(items)

        result = benchmark(collection.exclude, MarkerA)

        assert len(result) == 90


class TestIntrospectionBenchmarks:
    def test_bench_types_introspection(self, benchmark: "BenchmarkFixture") -> None:
        collection = create_collection(100, types=10)

        result = benchmark(collection.types)

        assert isinstance(result, frozenset)
        assert len(result) == 10

    def test_bench_by_type_grouping(self, benchmark: "BenchmarkFixture") -> None:
        collection = create_collection(100, types=10)

        result = benchmark(collection.by_type)

        assert len(result) == 10
        total_items = sum(len(group) for group in result.values())
        assert total_items == 100


class TestSequenceProtocolBenchmarks:
    def test_bench_len(self, benchmark: "BenchmarkFixture") -> None:
        collection = create_collection(1000, types=10)

        result = benchmark(len, collection)

        assert result == 1000

    def test_bench_bool(self, benchmark: "BenchmarkFixture") -> None:
        collection = create_collection(1000, types=10)

        result = benchmark(bool, collection)

        assert result is True

    def test_bench_is_empty_property(self, benchmark: "BenchmarkFixture") -> None:
        collection = create_collection(1000, types=10)

        result = benchmark(lambda: collection.is_empty)

        assert result is False

    def test_bench_getitem_index(self, benchmark: "BenchmarkFixture") -> None:
        collection = create_collection(1000, types=10)
        # Access middle element for average case
        index = 500

        result = benchmark(lambda: collection[index])

        assert result is not None

    def test_bench_getitem_slice(self, benchmark: "BenchmarkFixture") -> None:
        collection = create_collection(100, types=10)
        # Slice of 50 items from middle

        result = benchmark(lambda: collection[25:75])

        assert len(result) == 50
        assert isinstance(result, MetadataCollection)

    def test_bench_contains(self, benchmark: "BenchmarkFixture") -> None:
        collection = create_collection(100, types=10)
        # Get an item from the middle for average-case lookup
        target = collection[50]

        result = benchmark(lambda: target in collection)

        assert result is True

    def test_bench_iteration(self, benchmark: "BenchmarkFixture") -> None:
        collection = create_collection(100, types=10)

        # Benchmark full iteration by consuming iterator
        def iterate_all() -> None:
            for _ in collection:
                pass

        benchmark(iterate_all)

        # Verify iteration works correctly
        items = list(collection)
        assert len(items) == 100


class TestHashingEqualityBenchmarks:
    def test_bench_hash_small(self, benchmark: "BenchmarkFixture") -> None:
        items = [HashableMarker(value=i) for i in range(10)]
        collection = MetadataCollection.of(items)

        result = benchmark(hash, collection)

        assert isinstance(result, int)

    def test_bench_hash_large(self, benchmark: "BenchmarkFixture") -> None:
        items = [HashableMarker(value=i) for i in range(100)]
        collection = MetadataCollection.of(items)

        result = benchmark(hash, collection)

        assert isinstance(result, int)

    def test_bench_equality_same(self, benchmark: "BenchmarkFixture") -> None:
        items = [HashableMarker(value=i) for i in range(100)]
        collection1 = MetadataCollection.of(items)
        collection2 = MetadataCollection.of(items)

        result = benchmark(lambda: collection1 == collection2)

        assert result is True

    def test_bench_equality_different(self, benchmark: "BenchmarkFixture") -> None:
        items1 = [HashableMarker(value=i) for i in range(100)]
        items2 = [HashableMarker(value=i) for i in range(50)]
        collection1 = MetadataCollection.of(items1)
        collection2 = MetadataCollection.of(items2)

        result = benchmark(lambda: collection1 == collection2)

        assert result is False

    def test_bench_is_hashable_positive(self, benchmark: "BenchmarkFixture") -> None:
        items = [HashableMarker(value=i) for i in range(100)]
        collection = MetadataCollection.of(items)

        result = benchmark(lambda: collection.is_hashable)

        assert result is True

    def test_bench_is_hashable_negative_early(
        self, benchmark: "BenchmarkFixture"
    ) -> None:
        collection = create_collection_with_unhashable(100, unhashable_position=0)

        result = benchmark(lambda: collection.is_hashable)

        assert result is False
