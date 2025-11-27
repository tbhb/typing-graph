# pyright: reportAny=false, reportExplicitAny=false

from typing import Annotated, Any, ClassVar, Final, Literal

from hypothesis import HealthCheck, example, given, settings

from typing_graph import clear_cache, inspect_type

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
@example(Annotated[int, "meta"])
@example(ClassVar[int])
@example(Final[str])
def test_inspection_is_deterministic(annotation: Any) -> None:
    clear_cache()

    # Inspect the same annotation twice without caching
    result1 = inspect_type(annotation, use_cache=False)
    result2 = inspect_type(annotation, use_cache=False)

    # Results should be structurally equivalent even though they are different objects
    assert nodes_structurally_equal(result1, result2)
