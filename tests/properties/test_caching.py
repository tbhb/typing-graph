# pyright: reportAny=false, reportExplicitAny=false

from typing import Annotated, Any, ClassVar, Final, Literal

from hypothesis import HealthCheck, example, given, settings

from typing_graph import TypeNode, cache_clear, inspect_type

from .helpers import nodes_structurally_equal
from .strategies import type_annotations


@given(type_annotations())
@settings(suppress_health_check=[HealthCheck.too_slow], deadline=None)
@example(int)
@example(str)
@example(list[int])
@example(dict[str, int])
@example(int | str)
@example(tuple[int, str])
@example(tuple[int, ...])
@example(Literal[1, 2, 3])
@example(Annotated[int, "metadata"])
@example(ClassVar[int])
@example(Final[str])
def test_cache_returns_identical_objects(annotation: Any) -> None:
    cache_clear()
    result1 = inspect_type(annotation, use_cache=True)
    result2 = inspect_type(annotation, use_cache=True)

    # Cached results should be identical objects (same id)
    assert result1 is result2


@given(type_annotations())
@settings(suppress_health_check=[HealthCheck.too_slow], deadline=None)
@example(int)
@example(str)
@example(list[int])
@example(dict[str, int])
@example(int | str)
@example(ClassVar[int])
@example(Final[str])
def test_cache_disabled_returns_different_objects(annotation: Any) -> None:
    cache_clear()
    result1 = inspect_type(annotation, use_cache=False)
    result2 = inspect_type(annotation, use_cache=False)

    # Uncached results should be different objects
    assert result1 is not result2


@given(type_annotations())
@settings(suppress_health_check=[HealthCheck.too_slow], deadline=None)
@example(int)
@example(str)
@example(list[int])
@example(dict[str, int])
@example(int | str)
def test_cache_clear_invalidates_results(annotation: Any) -> None:
    result1 = inspect_type(annotation, use_cache=True)
    cache_clear()
    result2 = inspect_type(annotation, use_cache=True)

    # After clearing cache, results should be different objects
    assert result1 is not result2


@given(type_annotations())
@settings(suppress_health_check=[HealthCheck.too_slow], deadline=None)
@example(int)
@example(str)
@example(list[int])
@example(dict[str, int])
@example(int | str)
@example(tuple[int, str])
@example(tuple[int, ...])
@example(Literal["a", "b"])
@example(Annotated[int, "meta"])
@example(ClassVar[int])
@example(Final[str])
def test_caching_does_not_affect_result_structure(annotation: Any) -> None:
    cache_clear()
    cached = inspect_type(annotation, use_cache=True)
    uncached = inspect_type(annotation, use_cache=False)

    # Cached and uncached results should be structurally equivalent
    assert nodes_structurally_equal(cached, uncached)


@given(type_annotations())
@settings(suppress_health_check=[HealthCheck.too_slow], deadline=None)
@example(int)
@example(str)
@example(list[int])
@example(Annotated[int, "meta"])
def test_cache_disabled_produces_equivalent_results(annotation: Any) -> None:
    cache_clear()
    result1 = inspect_type(annotation, use_cache=False)
    result2 = inspect_type(annotation, use_cache=False)

    # Different object instances
    assert result1 is not result2
    # But structurally equivalent
    assert nodes_structurally_equal(result1, result2)


def test_default_caching_behavior_is_enabled() -> None:
    cache_clear()

    # Call without specifying use_cache - should use default (True)
    result1 = inspect_type(int)
    result2 = inspect_type(int)

    # Default behavior should cache (same object identity)
    assert result1 is result2


def test_different_types_have_different_cache_entries() -> None:
    cache_clear()

    int_node = inspect_type(int, use_cache=True)
    str_node = inspect_type(str, use_cache=True)

    # Different types must have different cache entries
    assert int_node is not str_node

    # Same type returns cached instance
    assert inspect_type(int, use_cache=True) is int_node
    assert inspect_type(str, use_cache=True) is str_node


def test_cache_actually_returns_stored_value() -> None:
    cache_clear()

    first = inspect_type(int, use_cache=True)
    second = inspect_type(int, use_cache=True)

    # Both must be valid TypeNodes
    assert first is not None
    assert isinstance(first, TypeNode)
    assert first is second


@given(type_annotations())
@settings(suppress_health_check=[HealthCheck.too_slow], deadline=None)
@example(int)
@example(list[int])
@example(dict[str, int])
def test_cached_result_is_valid_typenode(annotation: Any) -> None:
    cache_clear()

    first = inspect_type(annotation, use_cache=True)
    cached = inspect_type(annotation, use_cache=True)

    assert first is cached
    assert isinstance(cached, TypeNode)


@given(type_annotations())
@settings(suppress_health_check=[HealthCheck.too_slow], deadline=None)
@example(int)
@example(list[int])
@example(Annotated[int, "meta"])
def test_cache_stores_actual_result_not_none(annotation: Any) -> None:
    cache_clear()

    result = inspect_type(annotation, use_cache=True)
    assert isinstance(result, TypeNode)

    cached = inspect_type(annotation, use_cache=True)
    assert cached is result
    assert isinstance(cached, TypeNode)
