# ruff: noqa: BLE001, SLF001

import concurrent.futures
import contextlib
import threading
from typing import Annotated, Protocol, runtime_checkable

import pytest
from annotated_types import Ge, Gt, Interval, Le, Lt

from typing_graph._metadata import (
    MetadataCollection,
    ProtocolNotRuntimeCheckableError,
)


class TestThreadSafetySingletonAccess:
    def test_thread_safety_empty_singleton_access(self) -> None:
        results: list[MetadataCollection] = []
        errors: list[BaseException] = []

        def access_singleton() -> None:
            try:
                for _ in range(100):
                    empty = MetadataCollection.EMPTY
                    results.append(empty)
            except BaseException as e:
                errors.append(e)

        threads = [threading.Thread(target=access_singleton) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Errors during concurrent access: {errors}"

        # All accesses should return the same singleton
        if results:
            first = results[0]
            assert all(r is first for r in results)


class TestThreadSafetyConcurrentReads:
    def test_thread_safety_concurrent_reads(self) -> None:
        coll = MetadataCollection(_items=tuple(range(100)))
        results: list[list[object]] = []
        errors: list[BaseException] = []

        def read_collection() -> None:
            try:
                for _ in range(50):
                    _ = len(coll)
                    _ = list(coll)
                    _ = bool(coll)
                    _ = repr(coll)
                    _ = coll.is_hashable
                    if coll:
                        _ = coll[0]
                        _ = coll[-1]
                        _ = coll[1:5]
                results.append(list(coll))
            except BaseException as e:
                errors.append(e)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(read_collection) for _ in range(10)]
            _ = concurrent.futures.wait(futures)

        assert not errors, f"Errors during concurrent reads: {errors}"

        # All reads should return consistent data
        if results:
            expected = list(range(100))
            assert all(r == expected for r in results)


class TestFlattenWithAnnotatedTypes:
    def test_flatten_with_annotated_types_groupedmetadata(self) -> None:
        # Interval is a concrete GroupedMetadata that yields Gt and Lt when iterated
        ann = Annotated[int, Interval(gt=0, lt=100)]

        coll = MetadataCollection.from_annotated(ann)
        items = list(coll)

        # Should have Gt(0) and Lt(100) as separate items (flattened from Interval)
        assert len(items) == 2
        assert any(isinstance(item, Gt) for item in items)
        assert any(isinstance(item, Lt) for item in items)


class TestProtocolMatchingWithConstraints:
    @pytest.mark.xfail(reason="find_protocol method not yet implemented")
    def test_protocol_matching_with_annotated_types_constraints(self) -> None:
        @runtime_checkable
        class HasValue(Protocol):
            value: object

        # Collection with constraint types
        coll = MetadataCollection(_items=(Gt(0), Lt(100), Ge(0), Le(100)))

        matches = coll.find_protocol(HasValue)  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType,reportUnknownVariableType]

        # All constraint types have 'value' attribute
        assert len(matches) == 4  # pyright: ignore[reportUnknownArgumentType]


class TestFromAnnotatedNested:
    def test_from_annotated_with_nested_grouped_metadata(self) -> None:
        # Interval is a concrete GroupedMetadata that yields Gt and Lt when iterated
        inner = Annotated[int, Interval(gt=0, lt=100)]
        outer = Annotated[inner, "outer"]

        coll = MetadataCollection.from_annotated(outer)

        # Should have all metadata flattened (outer first, then inner's Gt and Lt)
        assert "outer" in coll
        assert any(isinstance(item, Gt) for item in coll)
        assert any(isinstance(item, Lt) for item in coll)


class TestGetRequiredErrorMessage:
    def test_get_required_error_message_with_real_constraints(self) -> None:
        coll = MetadataCollection(_items=(Gt(0), Lt(100)))

        try:
            _ = coll.get_required(Ge)
            pytest.fail("Should have raised MetadataNotFoundError")
        except LookupError as e:
            # Error message should show available types
            msg = str(e)
            assert "Ge" in msg


class TestPredicateExecutionIsolation:
    @pytest.mark.xfail(reason="filter method not yet implemented")
    def test_predicate_execution_isolation(self) -> None:
        coll = MetadataCollection(_items=(1, 2, 3, 4, 5))
        original_items = coll._items

        def failing_predicate(x: object) -> bool:
            if x == 3:
                msg = "Intentional failure"
                raise ValueError(msg)
            return True

        with contextlib.suppress(ValueError):
            _ = coll.filter(failing_predicate)  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType,reportUnknownVariableType]

        # Collection should be unchanged
        assert coll._items is original_items


class TestProtocolNotRuntimeCheckableErrorClear:
    @pytest.mark.xfail(reason="find_protocol method not yet implemented")
    def test_protocol_not_runtime_checkable_error_clear(self) -> None:
        class NotRuntime(Protocol):
            value: int

        coll = MetadataCollection(_items=("doc",))

        with pytest.raises(ProtocolNotRuntimeCheckableError) as exc_info:
            coll.find_protocol(NotRuntime)  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType]

        # Error message should suggest adding @runtime_checkable
        msg = str(exc_info.value)
        assert "@runtime_checkable" in msg


class _LargeGroupedMetadata:
    """A concrete GroupedMetadata implementation for testing large expansions."""

    _items: list[object]

    def __init__(self, items: list[object]) -> None:
        self._items = items

    def __iter__(self):  # type: ignore[override]
        return iter(self._items)


# Make it look like GroupedMetadata to pass the duck typing check
_LargeGroupedMetadata.__name__ = "GroupedMetadata"


class TestGroupedMetadataLargeExpansion:
    def test_grouped_metadata_infinite_iterator_protection(self) -> None:
        # Create a GroupedMetadata-like object with many items
        large_grouped = _LargeGroupedMetadata(list(range(1000)))

        coll = MetadataCollection.of([large_grouped])

        # Should work correctly with large GroupedMetadata
        assert len(coll) == 1000


class TestFactoryMethodsThreadSafety:
    def test_thread_safety_factory_methods(self) -> None:
        results: list[MetadataCollection] = []
        errors: list[BaseException] = []

        def create_collection(i: int) -> None:
            try:
                items = [f"item_{i}_{j}" for j in range(10)]
                coll = MetadataCollection.of(items)
                results.append(coll)
            except BaseException as e:
                errors.append(e)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_collection, i) for i in range(20)]
            _ = concurrent.futures.wait(futures)

        assert not errors, f"Errors during concurrent factory calls: {errors}"
        assert len(results) == 20
