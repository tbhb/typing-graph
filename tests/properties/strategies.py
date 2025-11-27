# pyright: reportAny=false, reportExplicitAny=false, reportUnknownVariableType=false
# pyright: reportUnknownMemberType=false, reportGeneralTypeIssues=false, reportInvalidTypeForm=false

from collections.abc import Callable
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    ClassVar,
    Final,
    Literal,
    ParamSpec,
    TypeVar,
)
from typing_extensions import LiteralString, Never, Self, TypeVarTuple, Unpack

from hypothesis import strategies as st
from hypothesis.strategies import composite

from typing_graph import EvalMode, InspectConfig

if TYPE_CHECKING:
    from hypothesis.strategies import DrawFn


@composite
def primitive_types(draw: "DrawFn") -> type:
    """Generate simple concrete types."""
    return draw(
        st.sampled_from(
            [
                int,
                str,
                float,
                bool,
                bytes,
                type(None),
                complex,
                object,
            ]
        )
    )


@composite
def none_types(draw: "DrawFn") -> type[None]:
    """Generate None type (NoneType).

    Note: Returns only type(None), not the literal None value, because
    None cannot be used in type union operations (None | X raises TypeError).
    The literal None is handled by inspect_type as equivalent to type(None).
    """
    _ = draw(st.just(True))  # Satisfy composite requirement
    return type(None)


@composite
def literal_types(draw: "DrawFn") -> Any:
    """Generate Literal[...] types from predefined set.

    Note: Dynamic Literal construction is not supported in Python 3.10,
    so we use a predefined set of representative Literal types.
    """
    return draw(
        st.sampled_from(
            [
                Literal[1],
                Literal[2],
                Literal[-1],
                Literal[0],
                Literal["a"],
                Literal["b"],
                Literal["hello"],
                Literal[True],
                Literal[False],
                Literal[1, 2],
                Literal["a", "b"],
                Literal[1, "a"],
                Literal[True, False],
                Literal[1, 2, 3],
                Literal["x", "y", "z"],
            ]
        )
    )


@composite
def special_forms(draw: "DrawFn") -> Any:
    """Generate special typing forms."""
    return draw(
        st.sampled_from(
            [
                Any,
                Never,
                Self,
                LiteralString,
            ]
        )
    )


@composite
def simple_generic_types(draw: "DrawFn", inner_type: st.SearchStrategy[Any]) -> Any:
    """Generate simple generics like list[T], set[T]."""
    origin = draw(st.sampled_from([list, set, frozenset]))
    inner = draw(inner_type)
    return origin[inner]


@composite
def dict_types(
    draw: "DrawFn",
    key_type: st.SearchStrategy[Any],
    value_type: st.SearchStrategy[Any],
) -> Any:
    """Generate dict[K, V] types."""
    key = draw(key_type)
    value = draw(value_type)
    return dict[key, value]


@composite
def optional_types(draw: "DrawFn", inner_type: st.SearchStrategy[Any]) -> Any:
    """Generate Optional[T] (T | None) types."""
    inner = draw(inner_type)
    return inner | None


@composite
def union_types(
    draw: "DrawFn",
    member_strategy: st.SearchStrategy[Any],
    max_members: int = 4,
) -> Any:
    """Generate union types (T | U | V)."""
    import functools
    import operator

    members = draw(
        st.lists(
            member_strategy,
            min_size=2,
            max_size=max_members,
            unique_by=repr,
        )
    )
    return functools.reduce(operator.or_, members)


@composite
def tuple_types(draw: "DrawFn", element_strategy: st.SearchStrategy[Any]) -> Any:
    """Generate tuple types (heterogeneous, homogeneous, empty)."""
    variant = draw(st.sampled_from(["heterogeneous", "homogeneous", "empty"]))

    if variant == "empty":
        return tuple[()]
    if variant == "homogeneous":
        elem = draw(element_strategy)
        return tuple[elem, ...]
    elems = draw(st.lists(element_strategy, min_size=1, max_size=5))
    return tuple.__class_getitem__(tuple(elems))


@composite
def callable_types(draw: "DrawFn", type_strategy: st.SearchStrategy[Any]) -> Any:
    """Generate Callable types."""
    variant = draw(st.sampled_from(["params", "ellipsis", "empty"]))
    return_type = draw(type_strategy)

    if variant == "ellipsis":
        return Callable[..., return_type]
    if variant == "empty":
        return Callable[[], return_type]
    params = draw(st.lists(type_strategy, min_size=1, max_size=4))
    # Use __class_getitem__ for dynamic Callable construction
    # (exists at runtime but not in type stubs)
    callable_getitem = Callable.__class_getitem__  # pyright: ignore[reportAttributeAccessIssue]
    return callable_getitem((params, return_type))


@composite
def qualified_types(draw: "DrawFn", inner_strategy: st.SearchStrategy[Any]) -> Any:
    """Generate ClassVar[T], Final[T] qualified types."""
    qualifier = draw(st.sampled_from([ClassVar, Final]))
    inner = draw(inner_strategy)
    return qualifier[inner]


@composite
def meta_types(draw: "DrawFn", inner_strategy: st.SearchStrategy[Any]) -> Any:
    """Generate type[T] types."""
    inner = draw(inner_strategy)
    return type[inner]


def type_annotations() -> st.SearchStrategy[Any]:
    """Generate arbitrary type annotations with controlled recursion.

    Uses st.recursive() for clean depth management with max_leaves=15
    to avoid pathological complexity.

    Note: ClassVar and Final (qualified_types) are NOT included in the recursive
    strategy because they cannot be nested or used in unions. They are top-level
    only type qualifiers. They can be tested separately with specific @example
    decorators.
    """
    base = st.one_of(
        primitive_types(),
        none_types(),
        literal_types(),
        special_forms(),
    )

    return st.recursive(
        base,
        lambda children: st.one_of(
            simple_generic_types(children),
            dict_types(children, children),
            optional_types(children),
            union_types(children),
            tuple_types(children),
            callable_types(children),
            meta_types(children),
        ),
        max_leaves=15,
    )


# =============================================================================
# Annotated Type Strategies
# =============================================================================


@composite
def metadata_items(draw: "DrawFn") -> Any:
    """Generate metadata items for Annotated types."""
    return draw(
        st.one_of(
            st.text(min_size=1, max_size=20),
            st.integers(-100, 100),
            st.booleans(),
        )
    )


@composite
def annotated_types(draw: "DrawFn", inner_strategy: st.SearchStrategy[Any]) -> Any:
    """Generate Annotated[T, ...] types."""
    inner = draw(inner_strategy)
    metadata_count = draw(st.integers(min_value=1, max_value=3))
    metadata = tuple(draw(metadata_items()) for _ in range(metadata_count))
    # Use __class_getitem__ for dynamic Annotated construction
    # (exists at runtime but not in type stubs)
    annotated_getitem = Annotated.__class_getitem__  # pyright: ignore[reportAttributeAccessIssue]
    return annotated_getitem((inner, *metadata))


@composite
def nested_annotated_types(
    draw: "DrawFn", inner_strategy: st.SearchStrategy[Any]
) -> Any:
    """Generate nested Annotated[Annotated[T, x], y] types."""
    # Use __class_getitem__ for dynamic Annotated construction
    # (exists at runtime but not in type stubs)
    annotated_getitem = Annotated.__class_getitem__  # pyright: ignore[reportAttributeAccessIssue]
    base = draw(inner_strategy)
    meta1 = tuple(draw(st.lists(st.text(max_size=10), min_size=1, max_size=2)))
    intermediate = annotated_getitem((base, *meta1))
    meta2 = tuple(draw(st.lists(st.integers(-50, 50), min_size=1, max_size=2)))
    return annotated_getitem((intermediate, *meta2))


# =============================================================================
# Configuration Strategies
# =============================================================================


@composite
def inspect_configs(draw: "DrawFn") -> InspectConfig:
    """Generate valid InspectConfig instances.

    Note: globalns and localns are left as None since generating valid
    namespaces is complex and these are typically provided by the caller.
    """
    return InspectConfig(
        eval_mode=draw(st.sampled_from(list(EvalMode))),
        max_depth=draw(st.none() | st.integers(min_value=1, max_value=20)),
        include_private=draw(st.booleans()),
        include_inherited=draw(st.booleans()),
        include_methods=draw(st.booleans()),
        include_class_vars=draw(st.booleans()),
        include_instance_vars=draw(st.booleans()),
        hoist_metadata=draw(st.booleans()),
        include_source_locations=draw(st.booleans()),
    )


# =============================================================================
# Round-Trippable Annotation Strategies
# =============================================================================


def roundtrippable_annotations() -> st.SearchStrategy[Any]:
    """Generate types that can round-trip through get_type_hints_for_node.

    Excludes types that cannot be recreated at runtime without the original
    object:
    - TypeVar, ParamSpec, TypeVarTuple (require original object)
    - Callable with ParamSpec (ParamSpec cannot be recreated)
    - Callable with Concatenate (requires ParamSpec)
    - NewType (requires original callable)
    - ClassVar, Final (top-level only, not nestable)

    Uses st.recursive() for clean depth management with max_leaves=15.
    """
    base = st.one_of(
        primitive_types(),
        none_types(),
        literal_types(),
        # Note: Any, Never, Self round-trip correctly.
        # LiteralString has platform-specific behavior so is excluded.
        st.sampled_from([Any, Never, Self]),
    )

    return st.recursive(
        base,
        lambda children: st.one_of(
            simple_generic_types(children),
            dict_types(children, children),
            optional_types(children),
            union_types(children),
            tuple_types(children),
            # Callable with explicit params only (no ParamSpec)
            roundtrippable_callable_types(children),
            annotated_types(children),
            meta_types(children),
        ),
        max_leaves=15,
    )


@composite
def roundtrippable_callable_types(
    draw: "DrawFn", type_strategy: st.SearchStrategy[Any]
) -> Any:
    """Generate Callable types that can round-trip (no ParamSpec/Concatenate)."""
    variant = draw(st.sampled_from(["params", "ellipsis", "empty"]))
    return_type = draw(type_strategy)

    if variant == "ellipsis":
        return Callable[..., return_type]
    if variant == "empty":
        return Callable[[], return_type]
    params = draw(st.lists(type_strategy, min_size=1, max_size=4))
    # Use __class_getitem__ for dynamic Callable construction
    # (exists at runtime but not in type stubs)
    callable_getitem = Callable.__class_getitem__  # pyright: ignore[reportAttributeAccessIssue]
    return callable_getitem((params, return_type))


# =============================================================================
# Type Parameter Strategies
# =============================================================================


class _TypeParamCounter:
    """Counter for generating unique type parameter names.

    Uses a mutable container to avoid PLW0603 global statement warnings.
    """

    _counter: int = 0

    @classmethod
    def next_typevar_name(cls) -> str:
        """Generate a unique TypeVar name to avoid conflicts."""
        cls._counter += 1
        return f"T{cls._counter}"

    @classmethod
    def next_paramspec_name(cls) -> str:
        """Generate a unique ParamSpec name to avoid conflicts."""
        cls._counter += 1
        return f"P{cls._counter}"

    @classmethod
    def next_typevartuple_name(cls) -> str:
        """Generate a unique TypeVarTuple name to avoid conflicts."""
        cls._counter += 1
        return f"Ts{cls._counter}"


@composite
def typevar_instances(draw: "DrawFn") -> TypeVar:
    """Generate TypeVar instances with various configurations.

    Generates TypeVars with:
    - Unique names to avoid conflicts during testing
    - Various variance configurations (invariant, covariant, contravariant)
    - Optional bound types
    - Optional constraint types (mutually exclusive with bound)
    """
    name = _TypeParamCounter.next_typevar_name()

    # Draw variance configuration
    covariant = draw(st.booleans())
    # Contravariant only if not covariant (mutual exclusion)
    contravariant = False if covariant else draw(st.booleans())

    # Draw bound or constraints (mutually exclusive)
    has_bound = draw(st.booleans())
    if has_bound:
        bound = draw(st.sampled_from([int, str, float, object]))
        return TypeVar(
            name, bound=bound, covariant=covariant, contravariant=contravariant
        )

    has_constraints = draw(st.booleans())
    if has_constraints:
        constraints = draw(
            st.lists(
                st.sampled_from([int, str, float, bool]),
                min_size=2,
                max_size=3,
                unique=True,
            )
        )
        return TypeVar(
            name, *constraints, covariant=covariant, contravariant=contravariant
        )

    return TypeVar(name, covariant=covariant, contravariant=contravariant)


@composite
def paramspec_instances(draw: "DrawFn") -> ParamSpec:
    """Generate ParamSpec instances with unique names."""
    _ = draw(st.just(True))  # Satisfy composite requirement
    name = _TypeParamCounter.next_paramspec_name()
    return ParamSpec(name)


@composite
def typevartuple_instances(draw: "DrawFn") -> TypeVarTuple:
    """Generate TypeVarTuple instances with unique names."""
    _ = draw(st.just(True))  # Satisfy composite requirement
    name = _TypeParamCounter.next_typevartuple_name()
    return TypeVarTuple(name)


@composite
def unpack_types(draw: "DrawFn") -> Any:
    """Generate Unpack[TypeVarTuple] types.

    Note: Unpack requires a TypeVarTuple as its argument.
    """
    tvt = draw(typevartuple_instances())
    return Unpack[tvt]


def type_param_annotations() -> st.SearchStrategy[Any]:
    """Generate type parameter annotations (TypeVar, ParamSpec, TypeVarTuple).

    These types are special - they cannot round-trip through get_type_hints_for_node
    because they require the original object to be preserved.
    """
    return st.one_of(
        typevar_instances(),
        paramspec_instances(),
        typevartuple_instances(),
    )


# =============================================================================
# Extended Type Annotations (including type parameters)
# =============================================================================


def extended_type_annotations() -> st.SearchStrategy[Any]:
    """Generate all type annotations including type parameters.

    This is a more comprehensive strategy than type_annotations() that includes
    TypeVar, ParamSpec, and TypeVarTuple. Use this for testing inspect_type()
    on the full range of possible type annotations.

    Note: TypeVar, ParamSpec, and TypeVarTuple cannot be used in unions (the |
    operator raises TypeError). They can only appear as leaf types or in specific
    contexts like generic class parameters.

    Note: Many of these types cannot round-trip through get_type_hints_for_node.
    """
    # Base types that can be used in unions
    unionable_base = st.one_of(
        primitive_types(),
        none_types(),
        literal_types(),
        special_forms(),
    )

    # Build recursive types from unionable base only
    # Type parameters are added at the top level, not recursively
    recursive_types = st.recursive(
        unionable_base,
        lambda children: st.one_of(
            simple_generic_types(children),
            dict_types(children, children),
            optional_types(children),
            union_types(children),
            tuple_types(children),
            callable_types(children),
            meta_types(children),
        ),
        max_leaves=15,
    )

    # Type parameters as standalone types (not in unions or nested generics)
    type_params = st.one_of(
        typevar_instances(),
        paramspec_instances(),
        typevartuple_instances(),
    )

    # Return either a recursive type or a standalone type parameter
    return st.one_of(recursive_types, type_params)
