"""Type annotation inspection."""

# pyright: reportAny=false, reportExplicitAny=false, reportUnusedFunction=false

import dataclasses
import functools
import operator
import sys
import types
from collections.abc import Callable
from typing import (
    Annotated,
    Any,
    ForwardRef as TypingForwardRef,
    Literal,
    ParamSpec,
    TypeVar,
    get_args,
    get_origin,
    overload,
)
from typing_extensions import TypeAliasType

from typing_inspection import typing_objects
from typing_inspection.introspection import (
    UNKNOWN,
    AnnotationSource,
    inspect_annotation,
)

from ._config import (
    DEFAULT_CONFIG,
    MISSING,
    EvalMode,
    InspectConfig,
)
from ._context import InspectContext, get_source_location
from ._metadata import MetadataCollection
from ._node import (
    AnyNode,
    CallableNode,
    ConcatenateNode,
    ConcreteNode,
    EllipsisNode,
    ForwardRefNode,
    GenericAliasNode,
    GenericTypeNode,
    LiteralNode,
    LiteralStringNode,
    MetaNode,
    NeverNode,
    NewTypeNode,
    ParamSpecNode,
    RefFailed,
    RefResolved,
    RefUnresolved,
    SelfNode,
    SubscriptedGenericNode,
    TupleNode,
    TypeAliasNode,
    TypeGuardNode,
    TypeIsNode,
    TypeNode,
    TypeParamNode,
    TypeVarNode,
    TypeVarTupleNode,
    UnionNode,
    UnpackNode,
    Variance,
    is_any_node,
    is_callable_node,
    is_concatenate_node,
    is_concrete_node,
    is_ellipsis_node,
    is_forward_ref_node,
    is_generic_node,
    is_literal_node,
    is_meta_node,
    is_never_node,
    is_param_spec_node,
    is_ref_state_resolved,
    is_self_node,
    is_subscripted_generic_node,
    is_tuple_node,
    is_type_param_node,
    is_type_var_node,
    is_type_var_tuple_node,
    is_union_type_node,
)

if sys.version_info >= (3, 11):  # pragma: no cover
    from typing import (  # pyright: ignore[reportUnreachable]
        Never,
        Self,
        TypeVarTuple,
    )
else:  # pragma: no cover
    from typing_extensions import (
        Never,
        Self,
        TypeVarTuple,
    )


_CALLABLE_ARGS_COUNT = 2  # Callable[[params], return_type]
_TUPLE_HOMOGENEOUS_ARGS_COUNT = 2  # tuple[T, ...]


def _make_annotated(base_type: Any, *metadata: object) -> Any:
    """Construct an Annotated type in a version-agnostic way.

    Python 3.14 removed direct access to Annotated.__class_getitem__, so we
    use operator.getitem which works across all Python versions.
    """
    # Annotated supports subscripting at runtime but pyright doesn't see it
    return operator.getitem(Annotated, (base_type, *metadata))  # pyright: ignore[reportCallIssue,reportArgumentType,reportUnknownVariableType]


def _get_type_params(obj: Any) -> tuple[Any, ...]:
    """Safely get type parameters from an object.

    Returns __type_params__ or __parameters__ as a tuple, handling cases where
    these attributes are descriptors (e.g., getset_descriptor in Python 3.14)
    that are not directly iterable. Prefers non-empty results from either attribute.
    """
    for attr in ("__type_params__", "__parameters__"):
        raw = getattr(obj, attr, None)
        if raw is None:
            continue
        # Check if it's actually iterable (not a descriptor)
        try:
            result = tuple(raw)
            # Skip empty tuples and try next attribute
            if result:
                return result
        except TypeError:
            # raw is a descriptor or otherwise not iterable
            continue
    return ()


class _TypeKey:
    """Wrapper to make unhashable types cacheable by identity.

    Generic aliases like list[int] are unhashable, so lru_cache can't use them
    directly as keys. This wrapper makes any type hashable via id().

    The identity comparison in __eq__ (using `is`) solves the id-reuse problem:
    lru_cache holds strong references to keys, so while cached, the original
    object can't be garbage collected. After LRU eviction, if the id is reused
    by a new object, `is` returns False (different objects), causing a cache miss.
    """

    __slots__: tuple[str, ...] = ("obj",)
    obj: Any

    def __init__(self, obj: Any) -> None:
        self.obj = obj

    def __hash__(self) -> int:  # pyright: ignore[reportImplicitOverride]
        return id(self.obj)

    def __eq__(self, other: object) -> bool:  # pyright: ignore[reportImplicitOverride]
        if isinstance(other, _TypeKey):
            return self.obj is other.obj
        return NotImplemented


@functools.cache
def _inspect_type_cached(key: _TypeKey) -> TypeNode:
    """Cached type inspection using default config.

    This is the cached implementation used when config is DEFAULT_CONFIG.
    The _TypeKey wrapper makes unhashable types cacheable.
    """
    _register_dispatch_tables()
    _register_type_inspectors()
    ctx = InspectContext(config=DEFAULT_CONFIG)
    return _inspect_type(key.obj, ctx)


def cache_clear() -> None:
    """Clear the global type inspection cache."""
    _inspect_type_cached.cache_clear()


def cache_info() -> functools._CacheInfo:  # pyright: ignore[reportPrivateUsage]
    """Return type inspection cache statistics.

    Returns a named tuple with hits, misses, maxsize, and currsize.
    Useful for debugging and monitoring cache performance.

    Returns:
        A CacheInfo named tuple with:
        - hits: Number of cache hits
        - misses: Number of cache misses
        - maxsize: Maximum cache size (None means unbounded)
        - currsize: Current number of cached entries
    """
    return _inspect_type_cached.cache_info()


class TypeInspector:
    """Callable interface for type inspector functions.

    Type inspectors are registered in a priority order and called sequentially.
    Each inspector examines an annotation and either:
    - Returns a TypeNode if it can handle the annotation
    - Returns None if it cannot handle the annotation (passes to next inspector)
    """

    def __call__(
        self, annotation: Any, ctx: InspectContext
    ) -> TypeNode | None:  # pragma: no cover
        """Inspect an annotation and return a TypeNode, or None if not handled.

        Args:
            annotation: The type annotation to inspect.
            ctx: The inspection context with configuration and state.

        Returns:
            A TypeNode if this inspector handles the annotation, None otherwise.
        """


# Registry of type inspectors - checked in registration order.
# Order matters: more specific checks must come before more general ones.
_TYPE_INSPECTORS: list[Callable[[Any, InspectContext], TypeNode | None]] = []
_inspectors_initialized: bool = False


# Type alias for dispatch functions that receive pre-computed origin/args.
# Returns TypeNode | None to allow dispatch functions to signal "no match".
_OriginDispatchFn = Callable[
    [Any, "InspectContext", Any, tuple[Any, ...]], TypeNode | None
]

# Type alias for predicate functions that check origins
_OriginPredicate = Callable[[Any], bool]

# O(1) dispatch table: maps origin id() to handler
# Only includes origins with NO ordering conflicts
_ORIGIN_DISPATCH: dict[int, _OriginDispatchFn] = {}

# Predicate-based dispatch: list of (predicate, handler) pairs checked in order
# Used for origins that vary across Python versions or need special checks
_PREDICATE_DISPATCHERS: list[tuple[_OriginPredicate, _OriginDispatchFn]] = []

# Initialization flag for dispatch tables
_dispatch_initialized: bool = False


def _register_type_inspectors() -> None:
    """Register all type inspectors in the correct priority order.

    This function explicitly defines the order of type inspectors. Order matters
    because more specific checks must come before more general ones.

    Note: Type qualifiers (ClassVar, Final, Required, NotRequired, ReadOnly) and
    Annotated metadata are handled by typing_inspection.inspect_annotation before
    the dispatcher runs. The extracted qualifiers and metadata are attached to
    the resulting TypeNode.

    The registration order is:
        1. None type - very specific singleton
        2. String annotations (forward refs)
        3. ForwardRefNode objects
        4. Special forms (Any, Never, Self, LiteralString)
        5. Union types (X | Y syntax only)
        6. Literal types
        7. Type[T] / type[T] - MUST come before Callable since `type` is callable
        8. Tuple types
        9. Callable types
        10. Type narrowing (TypeGuard, TypeIs)
        11. Concatenate
        12. Unpack
        13. TypeVarTuple - MUST come before TypeVar (isinstance check overlaps)
        14. TypeVar
        15. ParamSpec
        16. NewType
        17. TypeAliasType (PEP 695)
        18. Subscripted generics
        19. Plain types (classes) - most general, must be last
    """
    global _inspectors_initialized  # noqa: PLW0603
    if _inspectors_initialized:
        return

    # Clear any existing inspectors (safety for reinitialization)
    _TYPE_INSPECTORS.clear()

    # Register in explicit priority order
    # Note: Annotated and qualifier handlers are no longer needed - they are
    # handled by typing_inspection.inspect_annotation before dispatch
    # Non-origin types handled by sequential dispatch (Phase 4 in _dispatch_type).
    # Origin-based types (Union, Literal, tuple, type, Callable, TypeGuard, TypeIs,
    # Concatenate, Unpack, subscripted generics) are handled by the dispatch table.
    _TYPE_INSPECTORS.extend(
        [
            # 1. None type - very specific singleton
            _inspect_none_type,
            # 2-3. Forward references
            _inspect_string_annotation_handler,
            _inspect_forward_ref_handler,
            # 4. Special forms
            _inspect_any_type,
            _inspect_never_type,
            _inspect_self_type,
            _inspect_literal_string_type,
            # 5-7. Type parameters (order matters: TypeVarTuple before TypeVar)
            _inspect_typevartuple_handler,
            _inspect_typevar_handler,
            _inspect_paramspec_handler,
            # 8. NewType
            _inspect_newtype_handler,
            # 9. TypeAliasType (PEP 695)
            _inspect_type_alias_type_handler,
            # 10. Plain types (most general, must be last)
            _inspect_plain_type_handler,
        ]
    )

    _inspectors_initialized = True


def reset_type_inspectors() -> None:
    """Reset type inspectors and dispatch tables to default state (for testing only)."""
    global _inspectors_initialized, _dispatch_initialized  # noqa: PLW0603
    _TYPE_INSPECTORS.clear()
    _inspectors_initialized = False
    _ORIGIN_DISPATCH.clear()
    _PREDICATE_DISPATCHERS.clear()
    _dispatch_initialized = False


def _inspect_none_type(annotation: Any, _ctx: InspectContext) -> TypeNode | None:
    if annotation is None or annotation is type(None):
        return ConcreteNode(cls=type(None))
    return None


def _inspect_string_annotation_handler(
    annotation: Any, ctx: InspectContext
) -> TypeNode | None:
    """Handle string forward references."""
    if isinstance(annotation, str):
        return _inspect_string_annotation(annotation, ctx)
    return None


def _inspect_forward_ref_handler(
    annotation: Any, ctx: InspectContext
) -> TypeNode | None:
    """Handle typing.ForwardRefNode objects."""
    if isinstance(annotation, TypingForwardRef):
        return _inspect_forward_ref(annotation, ctx)
    return None


def _inspect_any_type(annotation: Any, _ctx: InspectContext) -> TypeNode | None:
    if annotation is Any:
        return AnyNode()
    return None


def _inspect_never_type(annotation: Any, _ctx: InspectContext) -> TypeNode | None:
    """Handle typing.Never and typing.NoReturn."""
    # NoReturn and Never are semantically equivalent "bottom" types
    if typing_objects.is_never(annotation) or typing_objects.is_noreturn(annotation):
        return NeverNode()
    return None


def _inspect_self_type(annotation: Any, _ctx: InspectContext) -> TypeNode | None:
    """Handle typing.Self."""
    if annotation is Self:
        return SelfNode()
    return None


def _inspect_literal_string_type(
    annotation: Any, _ctx: InspectContext
) -> TypeNode | None:
    """Handle typing.LiteralString (PEP 675)."""
    if typing_objects.is_literalstring(annotation):
        return LiteralStringNode()
    return None


def _inspect_typevartuple_handler(
    annotation: Any, ctx: InspectContext
) -> TypeNode | None:
    """Handle TypeVarTuple.

    MUST come before TypeVar handler because TypeVarTuple instances
    pass isinstance(obj, TypeVar) check.
    """
    # TypeVarTuple may be None in Python 3.10
    if TypeVarTuple is not None and isinstance(annotation, TypeVarTuple):  # pyright: ignore[reportUnnecessaryComparison]
        return _inspect_typevartuple(annotation, ctx)
    return None


def _inspect_typevar_handler(annotation: Any, ctx: InspectContext) -> TypeNode | None:
    """Handle TypeVar."""
    if isinstance(annotation, TypeVar):
        return _inspect_typevar(annotation, ctx)
    return None


def _inspect_paramspec_handler(annotation: Any, ctx: InspectContext) -> TypeNode | None:
    """Handle ParamSpec."""
    if isinstance(annotation, ParamSpec):
        return _inspect_paramspec(annotation, ctx)
    return None


def _inspect_newtype_handler(annotation: Any, ctx: InspectContext) -> TypeNode | None:
    """Handle NewType."""
    if typing_objects.is_newtype(annotation):
        # typing_objects.is_newtype() provides TypeIs narrowing.
        # __supertype__ and __name__ always exist on NewType at runtime,
        # but typing stubs don't expose them. Using getattr for type safety.
        supertype_val: Any = getattr(annotation, "__supertype__", None)
        name_val: str = getattr(annotation, "__name__", "NewType")
        supertype = _inspect_type(supertype_val, ctx.child())
        return NewTypeNode(
            name=name_val,
            supertype=supertype,
            source=get_source_location(annotation, ctx.config),
        )
    return None


def _inspect_type_alias_type_handler(
    annotation: Any, ctx: InspectContext
) -> TypeNode | None:
    """Handle PEP 695 TypeAliasType."""
    # TypeAliasType may be None in Python 3.10
    if TypeAliasType is not None and isinstance(annotation, TypeAliasType):  # pyright: ignore[reportUnnecessaryComparison]
        return _inspect_type_alias_type(annotation, ctx)
    return None


def _inspect_plain_type_handler(
    annotation: Any, ctx: InspectContext
) -> TypeNode | None:
    """Handle plain type objects (classes)."""
    if isinstance(annotation, type):
        return _inspect_plain_type(annotation, ctx)
    return None


# Origin-based dispatch wrapper functions
# These thin wrappers receive pre-computed origin/args to avoid redundant calls


def _dispatch_union(
    _annotation: Any, ctx: InspectContext, _origin: Any, args: tuple[Any, ...]
) -> TypeNode:
    """Dispatch handler for Union types (X | Y syntax)."""
    return _inspect_union(args, ctx)


def _dispatch_typing_union(
    _annotation: Any, ctx: InspectContext, _origin: Any, args: tuple[Any, ...]
) -> TypeNode | None:
    """Dispatch handler for typing.Union types.

    When normalize_unions=True, converts typing.Union to UnionNode.
    When normalize_unions=False, returns None to fall through to
    subscripted generic handling, preserving the native representation.
    """
    if ctx.config.normalize_unions:
        return _inspect_union(args, ctx)
    return None  # Fall through to subscripted generic


def _dispatch_literal(
    _annotation: Any, _ctx: InspectContext, _origin: Any, args: tuple[Any, ...]
) -> TypeNode:
    """Dispatch handler for Literal types."""
    return LiteralNode(values=args)


def _dispatch_meta_type(
    _annotation: Any, ctx: InspectContext, _origin: Any, args: tuple[Any, ...]
) -> TypeNode:
    """Dispatch handler for Type[T] / type[T]."""
    inner = _inspect_type(args[0] if args else Any, ctx.child())
    return MetaNode(of=inner)


def _dispatch_tuple(
    annotation: Any, ctx: InspectContext, _origin: Any, args: tuple[Any, ...]
) -> TypeNode:
    """Dispatch handler for tuple types."""
    return _inspect_tuple(annotation, args, ctx)


def _dispatch_typeguard(
    _annotation: Any, ctx: InspectContext, _origin: Any, args: tuple[Any, ...]
) -> TypeNode:
    """Dispatch handler for TypeGuard[T]."""
    inner = _inspect_type(args[0] if args else Any, ctx.child())
    return TypeGuardNode(narrows_to=inner)


def _dispatch_typeis(
    _annotation: Any, ctx: InspectContext, _origin: Any, args: tuple[Any, ...]
) -> TypeNode:
    """Dispatch handler for TypeIs[T]."""
    inner = _inspect_type(args[0] if args else Any, ctx.child())
    return TypeIsNode(narrows_to=inner)


def _dispatch_concatenate(
    _annotation: Any, ctx: InspectContext, _origin: Any, args: tuple[Any, ...]
) -> TypeNode | None:
    """Dispatch handler for Concatenate[X, Y, P]."""
    *prefix_types, param_spec = args
    prefix = tuple(_inspect_type(t, ctx.child()) for t in prefix_types)
    ps_node = _inspect_type(param_spec, ctx.child())
    if is_param_spec_node(ps_node):
        return ConcatenateNode(prefix=prefix, param_spec=ps_node)
    return None  # pragma: no cover - Concatenate always ends with ParamSpec


def _dispatch_unpack(
    _annotation: Any, ctx: InspectContext, _origin: Any, args: tuple[Any, ...]
) -> TypeNode:
    """Dispatch handler for Unpack[Ts]."""
    target = _inspect_type(args[0] if args else Any, ctx.child())
    return UnpackNode(target=target)


def _dispatch_callable(
    _annotation: Any, ctx: InspectContext, _origin: Any, args: tuple[Any, ...]
) -> TypeNode:
    """Dispatch handler for Callable types."""
    return _inspect_callable(args, ctx)


def _dispatch_subscripted_generic(
    annotation: Any, ctx: InspectContext, origin: Any, args: tuple[Any, ...]
) -> TypeNode:
    """Dispatch handler for generic subscripted types (list[int], etc.)."""
    return _inspect_subscripted_generic(annotation, origin, args, ctx)


def _is_callable_origin(origin: Any) -> bool:
    """Check if origin represents a Callable type.

    Excludes `type` since Type[T] is handled separately in O(1) dispatch.
    """
    if origin is type:
        return False  # Type[T] handled by _dispatch_meta_type
    return origin is Callable or (
        isinstance(origin, type) and issubclass(origin, Callable)
    )


def _register_dispatch_tables() -> None:
    """Register origin-based and predicate-based dispatch tables.

    This function sets up the O(1) dispatch table for origins with stable
    identities and the ordered predicate list for origins that vary across
    Python versions.

    The dispatch order ensures:
    - Type[T] is checked before Callable (via O(1) table)
    - TypeGuard/TypeIs/Concatenate/Unpack use predicate checks
    - Callable is last in predicates (has issubclass check)
    """
    global _dispatch_initialized  # noqa: PLW0603
    if _dispatch_initialized:
        return

    _ORIGIN_DISPATCH.clear()
    _PREDICATE_DISPATCHERS.clear()

    # O(1) dispatch: stable origins with no ordering conflicts
    _ORIGIN_DISPATCH.update(
        {
            id(types.UnionType): _dispatch_union,
            id(Literal): _dispatch_literal,
            id(type): _dispatch_meta_type,  # MUST be here, not in predicates
            id(tuple): _dispatch_tuple,
        }
    )

    # Predicate dispatch: version-variable origins + Callable (in order)
    _PREDICATE_DISPATCHERS.extend(
        [
            # typing.Union normalization (must be before subscripted generic fallback)
            (typing_objects.is_union, _dispatch_typing_union),
            (typing_objects.is_typeguard, _dispatch_typeguard),
            (typing_objects.is_typeis, _dispatch_typeis),
            (typing_objects.is_concatenate, _dispatch_concatenate),
            (typing_objects.is_unpack, _dispatch_unpack),
            (_is_callable_origin, _dispatch_callable),  # Callable last (excludes type)
        ]
    )

    _dispatch_initialized = True


def _dispatch_type(unwrapped_type: Any, ctx: InspectContext) -> TypeNode | None:
    """Dispatch to the appropriate handler for a type.

    Uses a four-phase dispatch strategy:
    1. O(1) origin-based dispatch for stable origins (Union, Literal, type, tuple)
    2. Predicate-based dispatch for version-variable origins (TypeGuard, Callable, etc.)
    3. Generic subscripted fallback for remaining origins (list[int], dict[K, V], etc.)
    4. Sequential dispatch for non-origin types (TypeVar, Any, plain classes, etc.)

    Args:
        unwrapped_type: The type after unwrapping qualifiers and Annotated.
        ctx: The inspection context.

    Returns:
        A TypeNode if a handler matched, or None if no handler matched.
    """
    origin = get_origin(unwrapped_type)

    if origin is not None:
        args = get_args(unwrapped_type)

        # Phase 1: O(1) origin-based dispatch for stable origins
        dispatcher = _ORIGIN_DISPATCH.get(id(origin))
        if dispatcher is not None:
            result = dispatcher(unwrapped_type, ctx, origin, args)
            if result is not None:
                return result

        # Phase 2: Predicate-based dispatch for version-variable origins
        for predicate, handler in _PREDICATE_DISPATCHERS:
            if predicate(origin):
                result = handler(unwrapped_type, ctx, origin, args)
                if result is not None:
                    return result

        # Phase 3: Generic subscripted fallback for remaining origins
        return _dispatch_subscripted_generic(unwrapped_type, ctx, origin, args)

    # Phase 4: Sequential dispatch for non-origin types
    for inspector in _TYPE_INSPECTORS:
        result = inspector(unwrapped_type, ctx)
        if result is not None:
            return result

    return None


def inspect_type(
    annotation: Any,
    *,
    config: InspectConfig | None = None,
    use_cache: bool = True,
) -> TypeNode:
    """Inspect any type annotation and return the corresponding TypeNode.

    This is the primary workhorse function. It handles:
    - Concrete types (int, str, MyClass)
    - Generic types (list, Dict, List[int], Dict[str, T])
    - Special forms (Any, Union, Optional, Literal, etc.)
    - Type variables (TypeVar, ParamSpec, TypeVarTuple)
    - Callable types
    - Annotated types
    - Forward references (strings or ForwardRefNode objects)

    Args:
        annotation: Any valid type annotation.
        config: Introspection configuration. Uses defaults if None.
        use_cache: Whether to use the global cache (default True).
            Note: Cache is only used when config is None or DEFAULT_CONFIG.

    Returns:
        A TypeNode representing the annotation's structure.
    """
    _register_type_inspectors()

    config = config if config is not None else DEFAULT_CONFIG

    # Use lru_cache only with default config (custom configs may need
    # different forward ref resolution via globalns/localns)
    if use_cache and config is DEFAULT_CONFIG:
        return _inspect_type_cached(_TypeKey(annotation))

    ctx = InspectContext(config=config)
    return _inspect_type(annotation, ctx)


def _inspect_type(annotation: Any, ctx: InspectContext) -> TypeNode:
    """Internal implementation of type inspection using registered inspectors.

    This function first uses typing_inspection.inspect_annotation to unwrap
    type qualifiers (ClassVar, Final, Required, NotRequired, ReadOnly, InitVar)
    and Annotated metadata. Then it dispatches the unwrapped type to registered
    handlers. The qualifiers and metadata are attached to the resulting TypeNode.

    The dispatcher pattern provides:
    - Open/Closed Principle: New type handlers can be added without modifying
      this function
    - Single Responsibility: Each handler focuses on one type category
    - Testability: Individual handlers can be unit tested in isolation
    - Extensibility: Third-party code could add custom handlers

    Args:
        annotation: The type annotation to inspect.
        ctx: The inspection context with configuration and state.

    Returns:
        A TypeNode representing the annotation's structure.
    """
    # Ensure dispatch tables and inspectors are registered
    _register_dispatch_tables()
    _register_type_inspectors()

    if not ctx.check_max_depth_exceeded():
        return ForwardRefNode(
            ref=str(annotation),
            state=RefFailed("Max depth exceeded"),
        )

    ann_id = id(annotation)
    if ann_id in ctx.seen:
        return ctx.seen[ann_id]

    # Use typing_inspection to unwrap qualifiers and metadata
    inspected = inspect_annotation(
        annotation,
        annotation_source=AnnotationSource.ANY,
        unpack_type_aliases="skip",
    )

    # Get the unwrapped type, qualifiers, and metadata
    unwrapped_type = inspected.type
    qualifiers = frozenset(inspected.qualifiers)
    metadata = MetadataCollection.of(inspected.metadata)

    # Handle UNKNOWN sentinel (bare qualifiers like `x: Final`)
    if unwrapped_type is UNKNOWN:
        result = AnyNode(qualifiers=qualifiers, metadata=metadata)
        ctx.seen[ann_id] = result
        return result

    # Dispatch to appropriate handler
    result = _dispatch_type(unwrapped_type, ctx)

    # Handle result or return failure
    if result is not None:
        # Attach qualifiers and metadata to the result
        if qualifiers or metadata:
            result = dataclasses.replace(
                result,
                qualifiers=result.qualifiers | qualifiers,
                metadata=result.metadata + metadata,
            )
        ctx.seen[ann_id] = result
        return result

    return ForwardRefNode(
        ref=str(annotation),
        state=RefFailed(f"Unknown annotation type: {type(annotation)}"),
        qualifiers=qualifiers,
        metadata=metadata,
    )


def _inspect_string_annotation(ref: str, ctx: InspectContext) -> TypeNode:
    """Handle string annotations."""
    if ctx.config.eval_mode == EvalMode.STRINGIFIED:
        return ForwardRefNode(ref=ref, state=RefUnresolved())

    if ref in ctx.resolving:
        # Recursive reference - return unresolved to break cycle
        return ForwardRefNode(ref=ref, state=RefUnresolved())

    ctx.resolving.add(ref)
    try:
        globalns = ctx.config.globalns or {}
        localns = ctx.config.localns or {}

        try:
            resolved = eval(ref, globalns, localns)  # noqa: S307
            resolved_node = _inspect_type(resolved, ctx.child())
            return ForwardRefNode(ref=ref, state=RefResolved(node=resolved_node))
        except Exception as e:
            if ctx.config.eval_mode == EvalMode.EAGER:
                msg = f"Cannot resolve forward reference '{ref}': {e}"
                raise NameError(msg) from e
            return ForwardRefNode(ref=ref, state=RefFailed(str(e)))
    finally:
        ctx.resolving.discard(ref)


def _inspect_forward_ref(ref: TypingForwardRef, ctx: InspectContext) -> TypeNode:
    """Handle typing.ForwardRefNode objects."""
    ref_str = ref.__forward_arg__

    if ctx.config.eval_mode == EvalMode.STRINGIFIED:
        return ForwardRefNode(ref=ref_str, state=RefUnresolved())

    if ref_str in ctx.resolving:
        return ForwardRefNode(ref=ref_str, state=RefUnresolved())

    ctx.resolving.add(ref_str)
    try:
        globalns = ctx.config.globalns or {}
        localns = ctx.config.localns or {}

        try:
            # Try to evaluate the ForwardRefNode
            # The API changed across Python versions:
            # - 3.14+: _evaluate deprecated, use evaluate_forward_ref
            # - 3.13: _evaluate requires type_params + recursive_guard kwargs
            # - 3.12: _evaluate requires recursive_guard kwarg (no type_params)
            # - 3.10-3.11: _evaluate takes recursive_guard as positional
            if sys.version_info >= (3, 14):
                from typing import evaluate_forward_ref  # noqa: PLC0415, I001  # pyright: ignore[reportUnreachable]

                resolved = evaluate_forward_ref(ref, globals=globalns, locals=localns)
            elif sys.version_info >= (3, 13):
                resolved = ref._evaluate(  # noqa: SLF001  # pyright: ignore[reportUnreachable]
                    globalns, localns, type_params=(), recursive_guard=frozenset()
                )
            elif sys.version_info >= (3, 12):
                resolved = ref._evaluate(  # noqa: SLF001  # pyright: ignore[reportUnreachable]
                    globalns, localns, recursive_guard=frozenset()
                )
            elif hasattr(ref, "_evaluate"):
                resolved = ref._evaluate(globalns, localns, frozenset())  # noqa: SLF001
            else:  # pragma: no cover - all supported Python versions have _evaluate
                resolved = eval(ref_str, globalns, localns)  # noqa: S307

            # _evaluate returns the resolved type or raises; it never returns None
            resolved_node = _inspect_type(resolved, ctx.child())
            state = RefResolved(node=resolved_node)
            return ForwardRefNode(ref=ref_str, state=state)
        except Exception as e:
            if ctx.config.eval_mode == EvalMode.EAGER:
                msg = f"Cannot resolve forward reference '{ref_str}': {e}"
                raise NameError(msg) from e
            return ForwardRefNode(ref=ref_str, state=RefFailed(str(e)))
    finally:
        ctx.resolving.discard(ref_str)


def _inspect_union(args: tuple[Any, ...], ctx: InspectContext) -> TypeNode:
    """Handle Union types."""
    members = tuple(_inspect_type(arg, ctx.child()) for arg in args)
    return UnionNode(members=members)


def _inspect_callable(args: tuple[Any, ...], ctx: InspectContext) -> TypeNode:
    """Handle Callable types."""
    if not args:
        # Bare Callable
        return CallableNode(params=(), returns=AnyNode())

    if len(args) == _CALLABLE_ARGS_COUNT:
        param_spec, return_type = args

        # Handle Callable[..., R]
        if param_spec is ...:
            return CallableNode(
                params=EllipsisNode(),
                returns=_inspect_type(return_type, ctx.child()),
            )

        # Handle Callable[P, R] where P is ParamSpec
        if isinstance(param_spec, ParamSpec):
            return CallableNode(
                params=_inspect_paramspec(param_spec, ctx),
                returns=_inspect_type(return_type, ctx.child()),
            )

        # Handle Callable[Concatenate[...], R]
        param_origin = get_origin(param_spec)
        if param_origin is not None and "Concatenate" in str(param_origin):
            concat_node = _inspect_type(param_spec, ctx.child())
            # pragma: no branch - Concatenate always produces ConcatenateNode
            if is_concatenate_node(concat_node):
                return CallableNode(
                    params=concat_node,
                    returns=_inspect_type(return_type, ctx.child()),
                )

        # Handle Callable[[P1, P2, ...], R]
        if isinstance(param_spec, list):
            # param_spec narrowed from Unknown to list[Any] by isinstance check
            param_list: list[Any] = param_spec  # pyright: ignore[reportUnknownVariableType]
            params = tuple(_inspect_type(p, ctx.child()) for p in param_list)
            return CallableNode(
                params=params,
                returns=_inspect_type(return_type, ctx.child()),
            )

    return CallableNode(params=(), returns=AnyNode())


def _inspect_tuple(
    annotation: Any, args: tuple[Any, ...], ctx: InspectContext
) -> TypeNode:
    """Handle tuple types."""
    # Check for tuple[()] - empty tuple (string repr contains 'tuple[()]')
    # We check this first because get_args(tuple[()]) returns () which
    # would otherwise be treated as an unparameterized tuple
    if not args and "tuple[()]" in str(annotation):
        return TupleNode(elements=(), homogeneous=False)

    if not args:
        # tuple with no args means tuple[Any, ...]
        return TupleNode(elements=(AnyNode(),), homogeneous=True)

    # Check for tuple[T, ...] - homogeneous
    if len(args) == _TUPLE_HOMOGENEOUS_ARGS_COUNT and args[1] is ...:
        elem_type = _inspect_type(args[0], ctx.child())
        return TupleNode(elements=(elem_type,), homogeneous=True)

    # Heterogeneous tuple
    elements = tuple(_inspect_type(arg, ctx.child()) for arg in args)
    return TupleNode(elements=elements, homogeneous=False)


def _extract_type_param_default(
    type_param: TypeVar | ParamSpec | TypeVarTuple, ctx: InspectContext
) -> TypeNode | None:
    """Extract the default value from a type parameter (PEP 696).

    PEP 696 (Python 3.13+) allows type parameters to have default values via
    the `__default__` attribute. This function checks for the attribute and
    inspects it if present, returning None if no valid default exists.

    Args:
        type_param: A type parameter (TypeVar, ParamSpec, or TypeVarTuple).
        ctx: The inspection context for recursive inspection.

    Returns:
        The inspected default type node, or None if no default is set.
    """
    default_attr = getattr(type_param, "__default__", MISSING)
    if (
        default_attr is not MISSING
        and default_attr is not None
        and not typing_objects.is_nodefault(default_attr)
    ):
        return _inspect_type(default_attr, ctx.child())
    return None


def _inspect_typevar(tv: TypeVar, ctx: InspectContext) -> TypeVarNode:
    """Handle TypeVar."""
    # Determine variance
    if tv.__covariant__:
        variance = Variance.COVARIANT
    elif tv.__contravariant__:
        variance = Variance.CONTRAVARIANT
    else:
        variance = Variance.INVARIANT

    # Get bound
    bound = None
    if tv.__bound__ is not None:
        bound = _inspect_type(tv.__bound__, ctx.child())

    # Get constraints
    constraints = tuple(_inspect_type(c, ctx.child()) for c in tv.__constraints__)

    # Get default (PEP 696, Python 3.13+)
    default = _extract_type_param_default(tv, ctx)

    # Check for infer_variance (PEP 695)
    infer_variance = getattr(tv, "__infer_variance__", False)

    return TypeVarNode(
        name=tv.__name__,
        variance=variance,
        bound=bound,
        constraints=constraints,
        default=default,
        infer_variance=infer_variance,
    )


def _inspect_paramspec(ps: ParamSpec, ctx: InspectContext) -> ParamSpecNode:
    """Handle ParamSpec."""
    default = _extract_type_param_default(ps, ctx)
    return ParamSpecNode(name=ps.__name__, default=default)


def _inspect_typevartuple(tvt: TypeVarTuple, ctx: InspectContext) -> TypeVarTupleNode:
    """Handle TypeVarTuple."""
    default = _extract_type_param_default(tvt, ctx)
    return TypeVarTupleNode(name=tvt.__name__, default=default)


def _inspect_type_alias_type(alias: Any, ctx: InspectContext) -> GenericAliasNode:
    """Handle PEP 695 TypeAliasType."""
    name = alias.__name__

    # Get type parameters - __type_params__ always exists on TypeAliasType
    # after isinstance check in the caller. This loop only executes on Python 3.12+
    # since TypeAliasType with type params requires PEP 695 syntax (type Alias[T] = ...)
    type_params: list[TypeParamNode] = []
    # pragma: no cover - requires Python 3.12+ PEP 695 syntax
    for tp in alias.__type_params__:
        tp_node = _inspect_type(tp, ctx.child())
        if is_type_param_node(tp_node):
            type_params.append(tp_node)

    # Get the aliased value
    value = _inspect_type(alias.__value__, ctx.child())

    return GenericAliasNode(
        name=name,
        type_params=tuple(type_params),
        value=value,
        source=get_source_location(alias, ctx.config),
    )


def _inspect_subscripted_generic(
    annotation: Any,
    origin: type,
    args: tuple[Any, ...],
    ctx: InspectContext,
) -> TypeNode:
    """Handle subscripted generic types like List[int], Dict[str, int]."""
    # Get type parameters of the origin if it's a generic
    type_params: list[TypeParamNode] = []
    for tp in _get_type_params(origin):
        tp_node = _inspect_type(tp, ctx.child())
        if is_type_param_node(tp_node):
            type_params.append(tp_node)

    origin_node = GenericTypeNode(
        cls=origin,
        type_params=tuple(type_params),
        source=get_source_location(origin, ctx.config),
    )

    arg_nodes = tuple(_inspect_type(arg, ctx.child()) for arg in args)

    return SubscriptedGenericNode(
        origin=origin_node,
        args=arg_nodes,
        source=get_source_location(annotation, ctx.config),
    )


def _inspect_plain_type(cls: type, ctx: InspectContext) -> TypeNode:
    """Handle plain type objects."""
    # Check if it's a generic type
    if hasattr(cls, "__class_getitem__"):
        type_params: list[TypeParamNode] = []
        for tp in _get_type_params(cls):
            tp_node = _inspect_type(tp, ctx.child())
            if is_type_param_node(tp_node):
                type_params.append(tp_node)

        if type_params:
            return GenericTypeNode(
                cls=cls,
                type_params=tuple(type_params),
                source=get_source_location(cls, ctx.config),
            )

    return ConcreteNode(
        cls=cls,
        source=get_source_location(cls, ctx.config),
    )


@overload
def inspect_type_param(  # pragma: no cover - overload signature
    param: TypeVar,
    *,
    config: InspectConfig | None = None,
) -> TypeVarNode: ...


@overload
def inspect_type_param(  # pragma: no cover - overload signature
    param: ParamSpec,
    *,
    config: InspectConfig | None = None,
) -> ParamSpecNode: ...


@overload
def inspect_type_param(  # pragma: no cover - overload signature
    param: TypeVarTuple,
    *,
    config: InspectConfig | None = None,
) -> TypeVarTupleNode: ...


def inspect_type_param(
    param: TypeVar | ParamSpec | TypeVarTuple,
    *,
    config: InspectConfig | None = None,
) -> TypeVarNode | ParamSpecNode | TypeVarTupleNode:
    """Inspect a type parameter.

    Args:
        param: A TypeVar, ParamSpec, or TypeVarTuple to inspect.
        config: Introspection configuration. Uses defaults if None.

    Returns:
        The corresponding TypeParamNode (TypeVarNode, ParamSpecNode,
        or TypeVarTupleNode).

    Raises:
        TypeError: If param is not a known type parameter type.
    """
    config = config if config is not None else DEFAULT_CONFIG
    ctx = InspectContext(config=config)

    # Check TypeVarTuple BEFORE TypeVar because TypeVarTuple is a TypeVar subclass
    # on some Python versions
    if isinstance(param, TypeVarTuple):
        return _inspect_typevartuple(param, ctx)
    if isinstance(param, ParamSpec):
        return _inspect_paramspec(param, ctx)
    # After TypeVarTuple and ParamSpec, TypeVar remains
    return _inspect_typevar(param, ctx)


def inspect_type_alias(
    alias: Any,
    *,
    name: str | None = None,
    config: InspectConfig | None = None,
) -> GenericAliasNode | TypeAliasNode:
    """Inspect a type alias.

    Args:
        alias: The type alias to inspect.
        name: Optional name for the alias (used for simple aliases).
        config: Introspection configuration. Uses defaults if None.

    Returns:
        A GenericAliasNode for PEP 695 TypeAliasType, or TypeAliasNode for
        simple type aliases.
    """
    config = config if config is not None else DEFAULT_CONFIG
    ctx = InspectContext(config=config)

    # PEP 695 TypeAliasType (may be None in Python 3.10)
    if TypeAliasType is not None and isinstance(alias, TypeAliasType):  # pyright: ignore[reportUnnecessaryComparison]
        return _inspect_type_alias_type(alias, ctx)

    # Simple type alias
    value = _inspect_type(alias, ctx.child())
    alias_name = name or getattr(alias, "__name__", "TypeAlias")

    return TypeAliasNode(
        name=alias_name,
        value=value,
    )


def resolve_forward_ref(
    ref: str | TypingForwardRef,
    *,
    globalns: dict[str, Any] | None = None,
    localns: dict[str, Any] | None = None,
) -> TypeNode:
    """Resolve a forward reference to a TypeNode.

    Warning:
        Forward reference resolution uses Python's eval() function.
        Do not use this function with untrusted type annotations,
        as malicious forward references could execute arbitrary code.

    Args:
        ref: A string or ForwardRefNode to resolve.
        globalns: Global namespace for resolution.
        localns: Local namespace for resolution.

    Returns:
        A TypeNode representing the resolved reference.

    Raises:
        NameError: If the forward reference cannot be resolved in the
            provided namespaces.
    """
    config = InspectConfig(
        eval_mode=EvalMode.EAGER,
        globalns=globalns,
        localns=localns,
    )
    ctx = InspectContext(config=config)

    if isinstance(ref, str):
        return _inspect_string_annotation(ref, ctx)
    return _inspect_forward_ref(ref, ctx)


def to_runtime_type(  # noqa: PLR0912, PLR0915 - Inherently complex type dispatch
    node: TypeNode,
    *,
    include_extras: bool = True,
) -> Any:
    """Convert a TypeNode back to runtime type hints.

    This is the reverse operation of inspect_type.

    Args:
        node: The TypeNode to convert.
        include_extras: Whether to include metadata as Annotated (default True).

    Returns:
        A runtime type annotation corresponding to the node.

    Raises:
        TypeError: If the node is a TypeVarNode, ParamSpecNode,
            TypeVarTupleNode, or a CallableNode with ParamSpec parameters.
            These types cannot be reconstructed because the original
            TypeVar/ParamSpec objects are not preserved.
    """
    result: Any

    if is_concrete_node(node) or is_generic_node(node):
        result = node.cls
    elif is_any_node(node):
        result = Any
    elif is_never_node(node):
        result = Never
    elif is_self_node(node):
        result = Self
    elif is_meta_node(node):
        inner = to_runtime_type(node.of)
        result = type[inner]
    elif is_literal_node(node):
        result = Literal[node.values]
    elif is_union_type_node(node):
        member_types = tuple(to_runtime_type(m) for m in node.members)
        result = functools.reduce(operator.or_, member_types)
    elif is_subscripted_generic_node(node):
        origin = to_runtime_type(node.origin)
        args = tuple(to_runtime_type(a) for a in node.args)
        result = origin[args] if args else origin
    elif is_tuple_node(node):
        if node.homogeneous:
            elem = to_runtime_type(node.elements[0])
            # tuple[T, ...] for homogeneous
            result = tuple.__class_getitem__((elem, ...))
        elif not node.elements:
            # tuple[()] for empty tuple
            result = tuple.__class_getitem__(())
        else:
            elems = tuple(to_runtime_type(e) for e in node.elements)
            result = tuple.__class_getitem__(elems)
    elif is_callable_node(node):
        returns = to_runtime_type(node.returns)
        if isinstance(node.params, tuple):
            params = [to_runtime_type(p) for p in node.params]
            # __class_getitem__ exists at runtime but isn't in type stubs;
            # using getattr avoids type errors (noqa: B009 - intentional)
            class_getitem = getattr(Callable, "__class_getitem__")  # noqa: B009
            result = class_getitem((params, returns))
        elif is_ellipsis_node(node.params):
            result = Callable[..., returns]
        else:
            # ParamSpec or Concatenate can't be recreated at runtime without the
            # original ParamSpec object, which we don't have.
            params_type = type(node.params).__name__
            msg = f"Cannot convert {params_type} back to runtime type hint"
            raise TypeError(msg)
    elif (
        is_type_var_node(node)
        or is_param_spec_node(node)
        or is_type_var_tuple_node(node)
    ):
        # TypeVar, ParamSpec, and TypeVarTuple can't be recreated without the
        # original object, which we don't have.
        msg = f"Cannot convert {type(node).__name__} back to runtime type hint"
        raise TypeError(msg)
    elif is_forward_ref_node(node):
        if is_ref_state_resolved(node.state):
            result = to_runtime_type(node.state.node)
        else:
            result = TypingForwardRef(node.ref)
    else:
        result = Any

    if include_extras and node.metadata:
        result = _make_annotated(result, *node.metadata)

    return result
