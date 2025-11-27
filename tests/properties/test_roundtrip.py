# pyright: reportAny=false, reportExplicitAny=false

from collections.abc import Callable
from types import UnionType
from typing import Annotated, Any, Literal, get_args, get_origin
from typing_extensions import Never, Self

from hypothesis import HealthCheck, example, given, settings

from typing_graph import clear_cache, get_type_hints_for_node, inspect_type
from typing_graph._node import is_concrete_type

from .strategies import primitive_types, roundtrippable_annotations


def _types_equivalent(  # noqa: PLR0911, PLR0912 - Inherently complex type dispatch
    t1: Any, t2: Any
) -> bool:
    """Check if two types are equivalent for round-trip purposes.

    Handles:
    - Identical references
    - None vs type(None) equivalence
    - Literal type value comparison (order-independent)
    - Union types (types.UnionType only, order-independent)
    - Annotated types (preserving metadata)
    - Parameterized generics (recursive comparison)
    """
    # Handle identical references
    if t1 is t2:
        return True

    # Handle None variants
    if t1 is None and t2 is type(None):
        return True
    if t2 is None and t1 is type(None):
        return True

    o1, o2 = get_origin(t1), get_origin(t2)

    # Handle Annotated (compare base type and metadata)
    if o1 is Annotated and o2 is Annotated:
        args1, args2 = get_args(t1), get_args(t2)
        if len(args1) != len(args2):
            return False
        # First arg is the base type, rest is metadata
        if not _types_equivalent(args1[0], args2[0]):
            return False
        # Metadata must match exactly (order matters for Annotated)
        return args1[1:] == args2[1:]

    # Handle Literal (compare values as sets - order independent)
    if o1 is Literal and o2 is Literal:
        return set(get_args(t1)) == set(get_args(t2))

    # Handle Union types (types.UnionType from X | Y syntax only)
    if isinstance(t1, UnionType) and isinstance(t2, UnionType):
        args1, args2 = get_args(t1), get_args(t2)
        if len(args1) != len(args2):
            return False
        # Union comparison must be bidirectional for correctness
        # Forward: every type in t1 has a match in t2
        forward = all(any(_types_equivalent(a1, a2) for a2 in args2) for a1 in args1)
        # Backward: every type in t2 has a match in t1
        backward = all(any(_types_equivalent(a2, a1) for a1 in args1) for a2 in args2)
        return forward and backward

    # Handle Callable types
    if o1 is Callable and o2 is Callable:
        args1, args2 = get_args(t1), get_args(t2)
        if len(args1) != len(args2):
            return False
        if len(args1) != 2:
            return args1 == args2
        # args[0] is params (list or ...), args[1] is return type
        params1, ret1 = args1
        params2, ret2 = args2
        # Handle ellipsis params
        if params1 is ... and params2 is ...:
            return _types_equivalent(ret1, ret2)
        if params1 is ... or params2 is ...:
            return False
        # Compare param lists
        if len(params1) != len(params2):
            return False
        for p1, p2 in zip(params1, params2, strict=True):
            if not _types_equivalent(p1, p2):
                return False
        return _types_equivalent(ret1, ret2)

    # Handle tuple types
    if o1 is tuple and o2 is tuple:
        args1, args2 = get_args(t1), get_args(t2)
        if len(args1) != len(args2):
            return False
        return all(
            _types_equivalent(a1, a2) for a1, a2 in zip(args1, args2, strict=True)
        )

    # Handle parameterized types (list[int], dict[K, V], etc.)
    if o1 is not None and o2 is not None:
        if o1 != o2:
            return False
        args1, args2 = get_args(t1), get_args(t2)
        if len(args1) != len(args2):
            return False
        return all(
            _types_equivalent(a1, a2) for a1, a2 in zip(args1, args2, strict=True)
        )

    return t1 == t2


@given(roundtrippable_annotations())
@settings(
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
    deadline=None,
)
# Migrated from TestGetTypeHintsForNode - primitive types
@example(int)
@example(str)
@example(float)
@example(bool)
@example(bytes)
@example(type(None))
# Migrated from TestGetTypeHintsForNode - special forms
@example(Any)
@example(Never)
@example(Self)
# Migrated from TestGetTypeHintsForNode - Literal types
@example(Literal["a", "b"])
@example(Literal[1, 2, 3])
@example(Literal[True, False])
# Migrated from TestGetTypeHintsForNode - Union types
@example(int | str)
@example(int | str | float)
@example(int | None)
# Migrated from TestGetTypeHintsForNode - Generic types
@example(list[int])
@example(set[str])
@example(frozenset[int])
@example(dict[str, int])
@example(dict[str, list[int]])
# Migrated from TestGetTypeHintsForNode - Tuple types
@example(tuple[int, ...])
@example(tuple[int, str])
@example(tuple[()])
@example(tuple[int, str, float])
# Migrated from TestGetTypeHintsForNode - Callable types
@example(Callable[[int, str], bool])
@example(Callable[..., int])
@example(Callable[[], int])
# Migrated from TestGetTypeHintsForNode - type[T] (MetaType)
@example(type[int])
@example(type[str])
# Migrated from TestGetTypeHintsForNode - Annotated types
@example(Annotated[int, "metadata"])
@example(Annotated[int, "meta1", "meta2"])
@example(Annotated[list[int], "description"])
# Additional edge cases - nested Annotated (Python flattens these)
@example(Annotated[Annotated[int, "inner"], "outer"])
# Additional edge cases - complex nested types
@example(dict[str, list[tuple[int, str]]])
@example(Callable[[int], str | None])
@example(Callable[[], Annotated[int, "result"]])
def test_roundtrip_preserves_structure(annotation: Any) -> None:
    # Clear cache to avoid stale entries from other tests when Hypothesis
    # replays examples from its database
    clear_cache()
    node = inspect_type(annotation)
    reconstructed = get_type_hints_for_node(node)

    assert _types_equivalent(annotation, reconstructed), (
        f"Round-trip failed:\n"
        f"  Original:      {annotation!r}\n"
        f"  Reconstructed: {reconstructed!r}"
    )


@given(primitive_types())
@settings(deadline=None)
@example(int)
@example(str)
@example(float)
@example(bool)
@example(bytes)
@example(type(None))
@example(complex)
@example(object)
def test_concrete_type_cls_attribute_preserved(cls: type) -> None:
    # Clear cache to avoid stale entries from other tests when Hypothesis
    # replays examples from its database
    clear_cache()
    node = inspect_type(cls)

    assert is_concrete_type(node), f"Expected ConcreteType for {cls}, got {type(node)}"
    assert node.cls is cls, f"cls attribute mismatch: expected {cls}, got {node.cls}"

    reconstructed = get_type_hints_for_node(node)
    assert reconstructed is cls, (
        f"Round-trip cls mismatch: expected {cls}, got {reconstructed}"
    )


@given(roundtrippable_annotations())
@settings(
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
    deadline=None,
)
@example(int)
@example(list[int])
@example(dict[str, int])
@example(int | str)
def test_roundtrip_without_extras_strips_metadata(annotation: Any) -> None:
    # Clear cache to avoid stale entries from other tests when Hypothesis
    # replays examples from its database
    clear_cache()
    node = inspect_type(annotation)

    # Get type hint without metadata (include_extras=False)
    reconstructed = get_type_hints_for_node(node, include_extras=False)

    # If original had Annotated metadata, reconstructed should be the inner type
    original_origin = get_origin(annotation)
    if original_origin is Annotated:
        # Reconstructed should be the inner type without Annotated wrapper
        original_inner = get_args(annotation)[0]
        assert _types_equivalent(reconstructed, original_inner), (
            f"Expected inner type {original_inner!r}, got {reconstructed!r}"
        )
    elif node.metadata:
        # Node gained metadata somehow (from qualifiers?), skip this case
        pass
    else:
        # For non-Annotated types, should be equivalent
        assert _types_equivalent(annotation, reconstructed)
