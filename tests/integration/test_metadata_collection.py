# pyright: reportAny=false, reportExplicitAny=false
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false, reportUnusedCallResult=false
# pyright: reportAbstractUsage=false, reportAttributeAccessIssue=false
# ruff: noqa: BLE001, SLF001

import concurrent.futures
import contextlib
import threading
from typing import Annotated, Protocol

import pytest
from annotated_types import Ge, GroupedMetadata, Gt, Le, Lt

from typing_graph._metadata import (
    MetadataCollection,
    ProtocolNotRuntimeCheckableError,
)

# =============================================================================
# Thread Safety Tests (Stage 0 - Basic Tests)
# =============================================================================


class TestThreadSafetySingletonAccess:
    # MC-139
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
    # MC-138
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


# =============================================================================
# Integration Tests with xfail markers for later stages
# These tests are expected to fail until the corresponding stage is implemented.
# Pyright errors are suppressed at file level since these test unimplemented APIs.
# =============================================================================


class TestFlattenWithAnnotatedTypes:
    # MC-131
    @pytest.mark.xfail(reason="Stage 1 implementation required - factory methods")
    def test_flatten_with_annotated_types_groupedmetadata(self) -> None:
        # This test requires MetadataCollection.from_annotated() from Stage 1
        # Collection from Annotated[int, GroupedMetadata([Gt(0), Lt(100)])]
        ann = Annotated[int, GroupedMetadata([Gt(0), Lt(100)])]  # pyright: ignore[reportCallIssue]

        # This will be implemented in Stage 1
        coll = MetadataCollection.from_annotated(ann)  # type: ignore[attr-defined]
        items = list(coll)

        # Should have Gt(0) and Lt(100) as separate items
        assert len(items) == 2
        assert any(isinstance(item, Gt) for item in items)
        assert any(isinstance(item, Lt) for item in items)


class TestProtocolMatchingWithConstraints:
    # MC-132
    @pytest.mark.xfail(reason="Stage 2 implementation required - protocol methods")
    def test_protocol_matching_with_annotated_types_constraints(self) -> None:
        from typing import runtime_checkable

        @runtime_checkable
        class HasValue(Protocol):
            value: object

        # Collection with constraint types
        coll = MetadataCollection(_items=(Gt(0), Lt(100), Ge(0), Le(100)))

        # This will be implemented in Stage 2
        matches = coll.find_protocol(HasValue)  # type: ignore[attr-defined]

        # All constraint types have 'value' attribute
        assert len(matches) == 4


class TestFromAnnotatedNested:
    # MC-133
    @pytest.mark.xfail(reason="Stage 1 implementation required - factory methods")
    def test_from_annotated_with_nested_grouped_metadata(self) -> None:
        inner = Annotated[int, GroupedMetadata([Gt(0), Lt(100)])]  # pyright: ignore[reportCallIssue]
        outer = Annotated[inner, "outer"]

        # This will be implemented in Stage 1
        coll = MetadataCollection.from_annotated(outer)  # type: ignore[attr-defined]

        # Should have all metadata flattened
        assert "outer" in coll


class TestGetRequiredErrorMessage:
    # MC-134
    @pytest.mark.xfail(reason="Stage 2 implementation required - get_required method")
    def test_get_required_error_message_with_real_constraints(self) -> None:
        coll = MetadataCollection(_items=(Gt(0), Lt(100)))

        # This will be implemented in Stage 2
        try:
            coll.get_required(Ge)  # type: ignore[attr-defined]
            pytest.fail("Should have raised MetadataNotFoundError")
        except LookupError as e:
            # Error message should show available types
            msg = str(e)
            assert "Gt" in msg or "Lt" in msg


class TestPredicateExecutionIsolation:
    # MC-135
    @pytest.mark.xfail(reason="Stage 3 implementation required - filter methods")
    def test_predicate_execution_isolation(self) -> None:
        coll = MetadataCollection(_items=(1, 2, 3, 4, 5))
        original_items = coll._items

        def failing_predicate(x: object) -> bool:
            if x == 3:
                msg = "Intentional failure"
                raise ValueError(msg)
            return True

        # This will be implemented in Stage 3
        with contextlib.suppress(ValueError):
            _ = coll.filter(failing_predicate)  # type: ignore[attr-defined]

        # Collection should be unchanged
        assert coll._items is original_items


class TestProtocolNotRuntimeCheckableErrorClear:
    # MC-136
    @pytest.mark.xfail(reason="Stage 2 implementation required - protocol methods")
    def test_protocol_not_runtime_checkable_error_clear(self) -> None:
        class NotRuntime(Protocol):
            value: int

        coll = MetadataCollection(_items=("doc",))

        # This will be implemented in Stage 2
        with pytest.raises(ProtocolNotRuntimeCheckableError) as exc_info:
            coll.find_protocol(NotRuntime)  # type: ignore[attr-defined]

        # Error message should suggest adding @runtime_checkable
        msg = str(exc_info.value)
        assert "@runtime_checkable" in msg


class TestGroupedMetadataLargeExpansion:
    # MC-137
    @pytest.mark.xfail(reason="Stage 1 implementation required - factory methods")
    def test_grouped_metadata_infinite_iterator_protection(self) -> None:
        # Create a GroupedMetadata with many items (not infinite, just large)
        large_grouped = GroupedMetadata(list(range(1000)))  # pyright: ignore[reportCallIssue]

        # This will be implemented in Stage 1
        coll = MetadataCollection.of([large_grouped])  # type: ignore[attr-defined]

        # Should work correctly with large GroupedMetadata
        assert len(coll) == 1000


class TestFactoryMethodsThreadSafety:
    # MC-140
    @pytest.mark.xfail(reason="Stage 1 implementation required - factory methods")
    def test_thread_safety_factory_methods(self) -> None:
        results: list[MetadataCollection] = []
        errors: list[BaseException] = []

        def create_collection(i: int) -> None:
            try:
                items = [f"item_{i}_{j}" for j in range(10)]
                # This will be implemented in Stage 1
                coll = MetadataCollection.of(items)  # type: ignore[attr-defined]
                results.append(coll)
            except BaseException as e:
                errors.append(e)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_collection, i) for i in range(20)]
            _ = concurrent.futures.wait(futures)

        assert not errors, f"Errors during concurrent factory calls: {errors}"
        assert len(results) == 20
