"""Type annotation graph node hierarchy."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, TypeVar
from typing_extensions import TypeIs, override

from ._metadata import MetadataCollection

if TYPE_CHECKING:
    from collections.abc import Sequence

    from typing_inspection.introspection import Qualifier


@dataclass(slots=True, frozen=True)
class SourceLocation:
    """Source code location for a type definition."""

    module: str | None = None
    qualname: str | None = None
    lineno: int | None = None
    file: str | None = None


@dataclass(slots=True, frozen=True)
class TypeNode(ABC):
    """Base class for all type graph nodes.

    Attributes:
        source: Optional source location where this type was defined.
        metadata: Metadata extracted from an enclosing Annotated[T, ...].
            When a type is wrapped in Annotated, the metadata can be hoisted
            to this field during graph construction, allowing the Annotated
            wrapper to be elided while preserving the metadata.
        qualifiers: Type qualifiers (ClassVar, Final, Required, NotRequired,
            ReadOnly, InitVar) extracted from the annotation. Uses the same
            qualifier type as typing_inspection.
    """

    source: SourceLocation | None = field(default=None, kw_only=True)
    metadata: MetadataCollection = field(
        default_factory=lambda: MetadataCollection.EMPTY, kw_only=True
    )
    qualifiers: "frozenset[Qualifier]" = field(default_factory=frozenset, kw_only=True)

    @abstractmethod
    def children(self) -> "Sequence[TypeNode]":
        """Return child type nodes for graph traversal.

        This method provides a faster traversal path when edge metadata
        is not required.
        """
        ...

    @abstractmethod
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        """Return all outgoing edges from this node.

        Forward reference handling: This method MUST NOT trigger forward
        reference resolution. Forward references may cause import cycles
        or execution of arbitrary code. Implementations SHOULD return
        edges to ForwardRefNode instances without resolving them.

        ForwardRefNode behavior: When a ForwardRefNode is unresolved or
        resolution failed, edges() MUST return an empty sequence (no
        RESOLVED edge). Only successfully resolved forward references
        produce a RESOLVED edge to the target node.
        """
        ...

    def resolved(self) -> "TypeNode":
        """Return the terminal resolved type, traversing forward reference chains.

        For non-ForwardRefNode types, returns self unchanged. For ForwardRefNode
        with RefResolved state, traverses the chain to find the terminal
        non-ForwardRefNode type. For unresolvable references (RefUnresolved,
        RefFailed, or cycles), returns self (the unresolvable ForwardRefNode).

        This method only traverses existing RefResolved chains - it does NOT
        trigger resolution of RefUnresolved forward references. To resolve
        forward references, use the graph construction APIs with appropriate
        namespace configuration.

        Returns:
            The terminal resolved TypeNode, or self if this is already a
            concrete (non-ForwardRefNode) type.

        Note:
            ForwardRefNode overrides this method to implement chain traversal.
            To distinguish why self was returned from a ForwardRefNode, check
            the node type and state:

            ```python
            result = node.resolved()
            if result is node and isinstance(node, ForwardRefNode):
                if isinstance(node.state, RefUnresolved):
                    # Resolution was never attempted
                    ...
                elif isinstance(node.state, RefFailed):
                    # Resolution failed: node.state.error has details
                    ...
                else:
                    # Cycle detected (RefResolved but returned self)
                    ...
            ```

            Prefer the method form for chaining: ``node.resolved().children()``.
            Prefer the function form for map/filter:
            ``map(resolve_forward_ref, nodes)``.

        Example:
            Chained usage for immediate attribute access:

            >>> from typing_graph import ConcreteNode
            >>> node = ConcreteNode(cls=int)
            >>> node.resolved() is node
            True
            >>> node.resolved().children()
            ()
        """
        return self


def is_type_node(obj: object) -> TypeIs[TypeNode]:
    """Return whether the argument is an instance of TypeNode."""
    return isinstance(obj, TypeNode)


TypeNodeT = TypeVar("TypeNodeT", bound=TypeNode)
"""TypeVar bound to TypeNode for generic functions over node types."""


class TypeEdgeKind(str, Enum):
    """Semantic relationship between parent and child nodes."""

    # Structural/container edges
    ELEMENT = auto()  # tuple element (positional)
    KEY = auto()  # dict key
    VALUE = auto()  # dict value (dict[K, V] -> V)
    UNION_MEMBER = auto()  # union variant
    ALIAS_TARGET = auto()  # type alias target definition (type X = T -> T)
    INTERSECTION_MEMBER = auto()  # intersection member (Intersection[A, B] -> A, B)

    # Named/attribute edges
    FIELD = auto()  # class/typeddict field
    METHOD = auto()  # class method
    PARAM = auto()  # callable parameter
    RETURN = auto()  # callable return type

    # Secondary/meta-type edges
    ORIGIN = auto()  # The generic origin (list in list[int])
    BOUND = auto()  # TypeVar bound
    CONSTRAINT = auto()  # TypeVar constraint
    DEFAULT = auto()  # TypeParam default
    BASE = auto()  # Class base class
    TYPE_PARAM = auto()  # The TypeVar definition (Generic[T])
    TYPE_ARG = auto()  # The applied type argument (list[int])
    SIGNATURE = auto()  # Function -> Signature
    NARROWS = auto()  # TypeGuard/TypeIs target
    SUPERTYPE = auto()  # NewType supertype
    ANNOTATED_BASE = auto()  # Annotated[T, ...] -> T
    META_OF = auto()  # Type[T] -> T (the type being meta'd)
    TARGET = auto()  # Unpack[T] -> T (the unpacked type)
    PREFIX = auto()  # Concatenate[X, Y, P] -> X, Y (prefix types)
    PARAM_SPEC = auto()  # Concatenate[X, Y, P] -> P (the ParamSpec)
    RESOLVED = auto()  # ForwardRef -> resolved type (when resolved)
    VALUE_TYPE = auto()  # Enum -> value type (int, str, etc.)


@dataclass(frozen=True, slots=True)
class TypeEdge:
    """Metadata describing a graph edge between nodes.

    Two TypeEdges are equal if they have the same (kind, name, index) tuple.
    """

    kind: TypeEdgeKind
    name: str | None = None
    index: int | None = None

    @override
    def __repr__(self) -> str:
        parts = [f"TypeEdgeKind.{self.kind.name}"]
        if self.name is not None:
            parts.append(f"name={self.name!r}")
        if self.index is not None:
            parts.append(f"index={self.index}")
        return f"TypeEdge({', '.join(parts)})"

    @classmethod
    def field(cls, name: str) -> "TypeEdge":
        """Create a FIELD edge with the given name."""
        return cls(TypeEdgeKind.FIELD, name=name)

    @classmethod
    def element(cls, index: int) -> "TypeEdge":
        """Create an ELEMENT edge with the given index."""
        return cls(TypeEdgeKind.ELEMENT, index=index)


@dataclass(frozen=True, slots=True)
class TypeEdgeConnection:
    """A connection from a node to a child node via an edge.

    TypeEdgeConnection provides a named alternative to tuple[TypeEdge, TypeNode],
    improving readability and IDE support for edge iteration.
    """

    edge: TypeEdge
    target: TypeNode

    @override
    def __repr__(self) -> str:
        return f"TypeEdgeConnection({self.edge!r} -> {self.target!r})"


class Variance(Enum):
    """Variance of a type variable."""

    INVARIANT = auto()
    COVARIANT = auto()
    CONTRAVARIANT = auto()


@dataclass(slots=True, frozen=True)
class TypeVarNode(TypeNode):
    """A TypeVar - placeholder for a single type.

    Example:
        T = TypeVar('T')
        T = TypeVar('T', bound=int)
        T = TypeVar('T', int, str)  # constraints
    """

    name: str
    variance: Variance = Variance.INVARIANT
    bound: TypeNode | None = None
    constraints: tuple[TypeNode, ...] = ()
    default: TypeNode | None = None  # PEP 696
    infer_variance: bool = False  # PEP 695 auto-variance
    _children: tuple[TypeNode, ...] = field(
        init=False, repr=False, compare=False, hash=False
    )
    _edges: tuple["TypeEdgeConnection", ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        children: list[TypeNode] = list(self.constraints)
        edges: list[TypeEdgeConnection] = [
            TypeEdgeConnection(TypeEdge(TypeEdgeKind.CONSTRAINT, index=i), c)
            for i, c in enumerate(self.constraints)
        ]
        if self.bound:
            children.append(self.bound)
            edges.append(TypeEdgeConnection(TypeEdge(TypeEdgeKind.BOUND), self.bound))
        if self.default:
            children.append(self.default)
            edges.append(
                TypeEdgeConnection(TypeEdge(TypeEdgeKind.DEFAULT), self.default)
            )
        object.__setattr__(self, "_children", tuple(children))
        object.__setattr__(self, "_edges", tuple(edges))

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return self._edges

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children


def is_type_var_node(obj: object) -> TypeIs[TypeVarNode]:
    """Return whether the argument is a TypeVarNode instance."""
    return isinstance(obj, TypeVarNode)


@dataclass(slots=True, frozen=True)
class ParamSpecNode(TypeNode):
    """A ParamSpec - placeholder for callable parameter lists.

    Example:
        P = ParamSpec('P')
        def decorator(f: Callable[P, R]) -> Callable[P, R]: ...
    """

    name: str
    default: TypeNode | None = None  # PEP 696
    _children: tuple[TypeNode, ...] = field(
        init=False, repr=False, compare=False, hash=False
    )
    _edges: tuple["TypeEdgeConnection", ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        if self.default:
            children: tuple[TypeNode, ...] = (self.default,)
            edges = (TypeEdgeConnection(TypeEdge(TypeEdgeKind.DEFAULT), self.default),)
        else:
            children = ()
            edges = ()
        object.__setattr__(self, "_children", children)
        object.__setattr__(self, "_edges", edges)

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return self._edges

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children


def is_param_spec_node(obj: object) -> TypeIs[ParamSpecNode]:
    """Return whether the argument is a ParamSpecNode instance."""
    return isinstance(obj, ParamSpecNode)


@dataclass(slots=True, frozen=True)
class TypeVarTupleNode(TypeNode):
    """A TypeVarTuple - placeholder for variadic type args (PEP 646).

    Example:
        Ts = TypeVarTuple('Ts')
        def f(*args: *Ts) -> tuple[*Ts]: ...
    """

    name: str
    default: TypeNode | None = None  # PEP 696
    _children: tuple[TypeNode, ...] = field(
        init=False, repr=False, compare=False, hash=False
    )
    _edges: tuple["TypeEdgeConnection", ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        if self.default:
            children: tuple[TypeNode, ...] = (self.default,)
            edges = (TypeEdgeConnection(TypeEdge(TypeEdgeKind.DEFAULT), self.default),)
        else:
            children = ()
            edges = ()
        object.__setattr__(self, "_children", children)
        object.__setattr__(self, "_edges", edges)

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return self._edges

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children


def is_type_var_tuple_node(obj: object) -> TypeIs[TypeVarTupleNode]:
    """Return whether the argument is a TypeVarTupleNode instance."""
    return isinstance(obj, TypeVarTupleNode)


TypeParamNode = TypeVarNode | ParamSpecNode | TypeVarTupleNode
"""Type alias for nodes representing type parameters."""


def is_type_param_node(node: TypeNode) -> TypeIs[TypeParamNode]:
    """Check if a node is a type parameter (TypeVar, ParamSpec, or TypeVarTuple).

    Args:
        node: The TypeNode to check.

    Returns:
        True if the node is a TypeVarNode, ParamSpecNode, or TypeVarTupleNode.
    """
    return (
        is_type_var_node(node)
        or is_param_spec_node(node)
        or is_type_var_tuple_node(node)
    )


@dataclass(slots=True, frozen=True)
class ConcatenateNode(TypeNode):
    """Concatenate[X, Y, P] - prepend args to a ParamSpec (PEP 612).

    Example:
        Callable[Concatenate[int, str, P], R]
    """

    prefix: tuple[TypeNode, ...]
    param_spec: ParamSpecNode
    _children: tuple[TypeNode, ...] = field(
        init=False, repr=False, compare=False, hash=False
    )
    _edges: tuple["TypeEdgeConnection", ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "_children", (*self.prefix, self.param_spec))
        edges: list[TypeEdgeConnection] = [
            TypeEdgeConnection(TypeEdge(TypeEdgeKind.PREFIX, index=i), p)
            for i, p in enumerate(self.prefix)
        ]
        edges.append(
            TypeEdgeConnection(TypeEdge(TypeEdgeKind.PARAM_SPEC), self.param_spec)
        )
        object.__setattr__(self, "_edges", tuple(edges))

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return self._edges

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children


def is_concatenate_node(obj: object) -> TypeIs[ConcatenateNode]:
    """Return whether the argument is a ConcatenateNode instance."""
    return isinstance(obj, ConcatenateNode)


@dataclass(slots=True, frozen=True)
class UnpackNode(TypeNode):
    """Unpack[Ts] or *Ts - unpack a TypeVarTuple (PEP 646).

    Example:
        def f(*args: *Ts) -> tuple[*Ts]: ...
        tuple[int, *Ts, str]
    """

    target: TypeVarTupleNode | TypeNode  # TypeVarTuple or a tuple type
    _children: tuple[TypeNode, ...] = field(
        init=False, repr=False, compare=False, hash=False
    )
    _edges: tuple["TypeEdgeConnection", ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "_children", (self.target,))
        object.__setattr__(
            self,
            "_edges",
            (TypeEdgeConnection(TypeEdge(TypeEdgeKind.TARGET), self.target),),
        )

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return self._edges

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children


def is_unpack_node(obj: object) -> TypeIs[UnpackNode]:
    """Return whether the argument is an UnpackNode instance."""
    return isinstance(obj, UnpackNode)


@dataclass(slots=True, frozen=True)
class ConcreteNode(TypeNode):
    """A non-generic nominal type: int, str, MyClass, etc."""

    cls: type

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return ()

    @override
    def children(self) -> "Sequence[TypeNode]":
        return ()

    @override
    def __str__(self) -> str:
        return self.cls.__name__


def is_concrete_node(obj: object) -> TypeIs[ConcreteNode]:
    """Return whether the argument is a ConcreteNode instance."""
    return isinstance(obj, ConcreteNode)


@dataclass(slots=True, frozen=True)
class GenericTypeNode(TypeNode):
    """An unsubscripted generic (type constructor): list, Dict, etc."""

    cls: type
    type_params: tuple[TypeVarNode | ParamSpecNode | TypeVarTupleNode, ...] = ()
    _edges: tuple["TypeEdgeConnection", ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        edges = tuple(
            TypeEdgeConnection(TypeEdge(TypeEdgeKind.TYPE_PARAM, index=i), tp)
            for i, tp in enumerate(self.type_params)
        )
        object.__setattr__(self, "_edges", edges)

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return self._edges

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self.type_params

    @override
    def __str__(self) -> str:
        return self.cls.__name__


def is_generic_node(obj: object) -> TypeIs[GenericTypeNode]:
    """Return whether the argument is a GenericType instance."""
    return isinstance(obj, GenericTypeNode)


class SpecialForm(TypeNode, ABC):
    """Base for special typing constructs that aren't concrete types."""


@dataclass(slots=True, frozen=True)
class AnyNode(TypeNode):
    """typing.Any - compatible with all types (gradual typing escape hatch)."""

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return ()

    @override
    def children(self) -> "Sequence[TypeNode]":
        return ()


def is_any_node(obj: object) -> TypeIs[AnyNode]:
    """Return whether the argument is an AnyNode instance."""
    return isinstance(obj, AnyNode)


@dataclass(slots=True, frozen=True)
class NeverNode(TypeNode):
    """typing.Never / typing.NoReturn - the bottom type (uninhabited)."""

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return ()

    @override
    def children(self) -> "Sequence[TypeNode]":
        return ()


def is_never_node(obj: object) -> TypeIs[NeverNode]:
    """Return whether the argument is a NeverNode instance."""
    return isinstance(obj, NeverNode)


@dataclass(slots=True, frozen=True)
class SelfNode(TypeNode):
    """typing.Self - reference to the enclosing class."""

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return ()

    @override
    def children(self) -> "Sequence[TypeNode]":
        return ()


def is_self_node(obj: object) -> TypeIs[SelfNode]:
    """Return whether the argument is a SelfNode instance."""
    return isinstance(obj, SelfNode)


@dataclass(slots=True, frozen=True)
class LiteralStringNode(TypeNode):
    """typing.LiteralString - any literal string value (PEP 675)."""

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return ()

    @override
    def children(self) -> "Sequence[TypeNode]":
        return ()


def is_literal_string_node(obj: object) -> TypeIs[LiteralStringNode]:
    """Return whether the argument is a LiteralStringNode instance."""
    return isinstance(obj, LiteralStringNode)


@dataclass(slots=True, frozen=True)
class EllipsisNode(TypeNode):
    """The ... used in Callable[..., R] and Tuple[T, ...]."""

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return ()

    @override
    def children(self) -> "Sequence[TypeNode]":
        return ()


def is_ellipsis_node(obj: object) -> TypeIs[EllipsisNode]:
    """Return whether the argument is an EllipsisNode instance."""
    return isinstance(obj, EllipsisNode)


@dataclass(slots=True, frozen=True)
class RefUnresolved:
    """Not yet attempted to resolve."""


@dataclass(slots=True, frozen=True)
class RefResolved:
    """Successfully resolved to a type."""

    node: TypeNode


@dataclass(slots=True, frozen=True)
class RefFailed:
    """Resolution attempted but failed."""

    error: str


RefState = RefUnresolved | RefResolved | RefFailed
"""Type alias for forward reference resolution states."""


def is_ref_state_resolved(state: object) -> TypeIs[RefResolved]:
    """Return whether the argument is a RefResolved instance."""
    return isinstance(state, RefResolved)


def is_ref_state_failed(state: object) -> TypeIs[RefFailed]:
    """Return whether the argument is a RefFailed instance."""
    return isinstance(state, RefFailed)


def is_ref_state_unresolved(state: object) -> TypeIs[RefUnresolved]:
    """Return whether the argument is a RefUnresolved instance."""
    return isinstance(state, RefUnresolved)


@dataclass(slots=True, frozen=True)
class ForwardRefNode(TypeNode):
    """A string forward reference like 'MyClass'."""

    ref: str
    state: RefState = field(default_factory=RefUnresolved)
    _children: tuple[TypeNode, ...] = field(
        init=False, repr=False, compare=False, hash=False
    )
    _edges: tuple["TypeEdgeConnection", ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        if isinstance(self.state, RefResolved):
            children: tuple[TypeNode, ...] = (self.state.node,)
            edges = (
                TypeEdgeConnection(TypeEdge(TypeEdgeKind.RESOLVED), self.state.node),
            )
        else:
            children = ()
            edges = ()
        object.__setattr__(self, "_children", children)
        object.__setattr__(self, "_edges", edges)

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return self._edges

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children

    @override
    def __str__(self) -> str:
        if isinstance(self.state, RefResolved):
            return f"ForwardRef({self.ref!r}) -> {self.state.node}"
        if isinstance(self.state, RefFailed):
            return f"ForwardRef({self.ref!r}) [failed: {self.state.error}]"
        return f"ForwardRef({self.ref!r})"

    @override
    def resolved(self) -> "TypeNode":
        """Return the terminal resolved type, traversing forward reference chains.

        Traverses chains of resolved forward references until reaching either:
        - A non-ForwardRefNode type (the terminal resolution)
        - An unresolvable ForwardRefNode (RefUnresolved or RefFailed state)
        - A cycle (detected via identity tracking)

        This method only traverses existing RefResolved chains - it does NOT
        trigger resolution of RefUnresolved forward references. To resolve
        forward references, use the graph construction APIs with appropriate
        namespace configuration.

        Returns:
            The terminal resolved TypeNode, or self if unresolvable.

        Note:
            When self is returned, the reason can be determined by checking:
            - RefUnresolved state: resolution was never attempted
            - RefFailed state: resolution failed (check state.error)
            - RefResolved state: cycle detected in reference chain

        Example:
            Single resolution step:

            >>> from typing_graph import ConcreteNode, ForwardRefNode, RefResolved
            >>> target = ConcreteNode(cls=int)
            >>> ref = ForwardRefNode(ref="int", state=RefResolved(node=target))
            >>> ref.resolved() is target
            True

            Chain traversal:

            >>> inner = ForwardRefNode(ref="int", state=RefResolved(node=target))
            >>> outer = ForwardRefNode(ref="Inner", state=RefResolved(node=inner))
            >>> outer.resolved() is target
            True
        """
        seen: set[int] = set()
        current: TypeNode = self
        while isinstance(current, ForwardRefNode):
            node_id = id(current)
            if node_id in seen:
                return current  # Cycle detected
            seen.add(node_id)
            if isinstance(current.state, RefResolved):
                current = current.state.node
            else:
                return current  # Unresolvable (RefUnresolved or RefFailed)
        return current


def is_forward_ref_node(obj: object) -> TypeIs[ForwardRefNode]:
    """Return whether the argument is a ForwardRefNode instance."""
    return isinstance(obj, ForwardRefNode)


@dataclass(slots=True, frozen=True)
class LiteralNode(TypeNode):
    """Literal[v1, v2, ...] - specific literal values as types."""

    values: tuple[object, ...]

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return ()

    @override
    def children(self) -> "Sequence[TypeNode]":
        return ()


def is_literal_node(obj: object) -> TypeIs[LiteralNode]:
    """Return whether the argument is a LiteralNode instance."""
    return isinstance(obj, LiteralNode)


@dataclass(slots=True, frozen=True)
class SubscriptedGenericNode(TypeNode):
    """Generic with type args applied: List[int], Dict[str, T], etc."""

    origin: TypeNode  # GenericType or another SubscriptedGenericNode
    args: tuple[TypeNode, ...]
    _children: tuple[TypeNode, ...] = field(
        init=False, repr=False, compare=False, hash=False
    )
    _edges: tuple["TypeEdgeConnection", ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "_children", (self.origin, *self.args))
        edges: list[TypeEdgeConnection] = [
            TypeEdgeConnection(TypeEdge(TypeEdgeKind.ORIGIN), self.origin)
        ]
        edges.extend(
            TypeEdgeConnection(TypeEdge(TypeEdgeKind.TYPE_ARG, index=i), arg)
            for i, arg in enumerate(self.args)
        )
        object.__setattr__(self, "_edges", tuple(edges))

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return self._edges

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children

    @override
    def __str__(self) -> str:
        args_str = ", ".join(str(arg) for arg in self.args)
        return f"{self.origin}[{args_str}]"


def is_subscripted_generic_node(obj: object) -> TypeIs[SubscriptedGenericNode]:
    """Return whether the argument is a SubscriptedGenericNode instance."""
    return isinstance(obj, SubscriptedGenericNode)


@dataclass(slots=True, frozen=True)
class GenericAliasNode(TypeNode):
    """Parameterized type alias: type Vector[T] = list[T] (PEP 695)."""

    name: str
    type_params: tuple[TypeVarNode | ParamSpecNode | TypeVarTupleNode, ...]
    value: TypeNode  # The aliased type (may reference type_params)
    _children: tuple[TypeNode, ...] = field(
        init=False, repr=False, compare=False, hash=False
    )
    _edges: tuple["TypeEdgeConnection", ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "_children", (*self.type_params, self.value))
        edges: list[TypeEdgeConnection] = [
            TypeEdgeConnection(TypeEdge(TypeEdgeKind.TYPE_PARAM, index=i), tp)
            for i, tp in enumerate(self.type_params)
        ]
        edges.append(
            TypeEdgeConnection(TypeEdge(TypeEdgeKind.ALIAS_TARGET), self.value)
        )
        object.__setattr__(self, "_edges", tuple(edges))

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return self._edges

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children


def is_generic_alias_node(obj: object) -> TypeIs[GenericAliasNode]:
    """Return whether the argument is a GenericAliasNode instance."""
    return isinstance(obj, GenericAliasNode)


@dataclass(slots=True, frozen=True)
class TypeAliasNode(TypeNode):
    """typing.TypeAlias or PEP 695 type statement runtime object."""

    name: str
    value: TypeNode
    _children: tuple[TypeNode, ...] = field(
        init=False, repr=False, compare=False, hash=False
    )
    _edges: tuple["TypeEdgeConnection", ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "_children", (self.value,))
        object.__setattr__(
            self,
            "_edges",
            (TypeEdgeConnection(TypeEdge(TypeEdgeKind.ALIAS_TARGET), self.value),),
        )

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return self._edges

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children


def is_type_alias_node(obj: object) -> TypeIs[TypeAliasNode]:
    """Return whether the argument is a TypeAliasNode instance."""
    return isinstance(obj, TypeAliasNode)


@dataclass(slots=True, frozen=True)
class UnionNode(TypeNode):
    """A | B union type."""

    members: tuple[TypeNode, ...]
    _edges: tuple["TypeEdgeConnection", ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        edges = tuple(
            TypeEdgeConnection(TypeEdge(TypeEdgeKind.UNION_MEMBER, index=i), m)
            for i, m in enumerate(self.members)
        )
        object.__setattr__(self, "_edges", edges)

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return self._edges

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self.members

    @override
    def __str__(self) -> str:
        return " | ".join(str(m) for m in self.members)


def is_union_type_node(obj: object) -> TypeIs[UnionNode]:
    """Return whether the argument is a UnionNode instance."""
    return isinstance(obj, UnionNode)


@dataclass(slots=True, frozen=True)
class IntersectionNode(TypeNode):
    """Intersection of types (not yet in typing, but used by type checkers)."""

    members: tuple[TypeNode, ...]
    _edges: tuple["TypeEdgeConnection", ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        edges = tuple(
            TypeEdgeConnection(TypeEdge(TypeEdgeKind.INTERSECTION_MEMBER, index=i), m)
            for i, m in enumerate(self.members)
        )
        object.__setattr__(self, "_edges", edges)

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return self._edges

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self.members


def is_intersection_node(obj: object) -> TypeIs[IntersectionNode]:
    """Return whether the argument is an IntersectionNode instance."""
    return isinstance(obj, IntersectionNode)


@dataclass(slots=True, frozen=True)
class CallableNode(TypeNode):
    """Callable[[P1, P2], R] or Callable[P, R] or Callable[..., R]."""

    params: tuple[TypeNode, ...] | ParamSpecNode | ConcatenateNode | EllipsisNode
    returns: TypeNode
    _children: tuple[TypeNode, ...] = field(
        init=False, repr=False, compare=False, hash=False
    )
    _edges: tuple["TypeEdgeConnection", ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        if isinstance(self.params, tuple):
            children = (*self.params, self.returns)
            # When params is a tuple, use indexed PARAM edges
            edges: list[TypeEdgeConnection] = [
                TypeEdgeConnection(TypeEdge(TypeEdgeKind.PARAM, index=i), p)
                for i, p in enumerate(self.params)
            ]
        else:
            children = (self.params, self.returns)
            # Single node (ParamSpec, Concatenate, Ellipsis) - no index
            edges = [TypeEdgeConnection(TypeEdge(TypeEdgeKind.PARAM), self.params)]
        edges.append(TypeEdgeConnection(TypeEdge(TypeEdgeKind.RETURN), self.returns))
        object.__setattr__(self, "_children", children)
        object.__setattr__(self, "_edges", tuple(edges))

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return self._edges

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children


def is_callable_node(obj: object) -> TypeIs[CallableNode]:
    """Return whether the argument is a CallableNode instance."""
    return isinstance(obj, CallableNode)


@dataclass(slots=True, frozen=True)
class TupleNode(TypeNode):
    """Tuple types in various forms.

    Examples:
        tuple[int, str]      - heterogeneous (elements=(int, str), homogeneous=False)
        tuple[int, ...]      - homogeneous (elements=(int,), homogeneous=True)
        tuple[int, *Ts, str] - variadic (contains UnpackNode)
        tuple[()]            - empty tuple (elements=(), homogeneous=False)
    """

    elements: tuple[TypeNode, ...]
    homogeneous: bool = False  # True for tuple[T, ...]
    _edges: tuple["TypeEdgeConnection", ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        edges = tuple(
            TypeEdgeConnection(TypeEdge(TypeEdgeKind.ELEMENT, index=i), e)
            for i, e in enumerate(self.elements)
        )
        object.__setattr__(self, "_edges", edges)

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return self._edges

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self.elements

    @override
    def __str__(self) -> str:
        if self.homogeneous and self.elements:
            return f"tuple[{self.elements[0]}, ...]"
        if not self.elements:
            return "tuple[()]"
        return f"tuple[{', '.join(str(e) for e in self.elements)}]"


def is_tuple_node(obj: object) -> TypeIs[TupleNode]:
    """Return whether the argument is a TupleNode instance."""
    return isinstance(obj, TupleNode)


@dataclass(slots=True, frozen=True)
class AnnotatedNode(TypeNode):
    """Annotated[T, metadata, ...].

    Note: During graph construction, you may choose to hoist metadata to the
    inner type's `metadata` field and elide the AnnotatedNode wrapper. This
    node represents the un-elided form.
    """

    base: TypeNode
    # Note: metadata is on base TypeNode, but annotations here are the raw
    # Annotated arguments, which may include type-system extensions
    annotations: tuple[object, ...] = ()
    _children: tuple[TypeNode, ...] = field(
        init=False, repr=False, compare=False, hash=False
    )
    _edges: tuple["TypeEdgeConnection", ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "_children", (self.base,))
        object.__setattr__(
            self,
            "_edges",
            (TypeEdgeConnection(TypeEdge(TypeEdgeKind.ANNOTATED_BASE), self.base),),
        )

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return self._edges

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children


def is_annotated_node(obj: object) -> TypeIs[AnnotatedNode]:
    """Return whether the argument is an AnnotatedNode instance."""
    return isinstance(obj, AnnotatedNode)


@dataclass(slots=True, frozen=True)
class MetaNode(TypeNode):
    """Type[T] or type[T] - the class object itself, not an instance."""

    of: TypeNode
    _children: tuple[TypeNode, ...] = field(
        init=False, repr=False, compare=False, hash=False
    )
    _edges: tuple["TypeEdgeConnection", ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "_children", (self.of,))
        object.__setattr__(
            self,
            "_edges",
            (TypeEdgeConnection(TypeEdge(TypeEdgeKind.META_OF), self.of),),
        )

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return self._edges

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children


def is_meta_node(obj: object) -> TypeIs[MetaNode]:
    """Return whether the argument is a MetaNode instance."""
    return isinstance(obj, MetaNode)


@dataclass(slots=True, frozen=True)
class TypeGuardNode(TypeNode):
    """typing.TypeGuard[T] - narrows type in true branch (PEP 647)."""

    narrows_to: TypeNode
    _children: tuple[TypeNode, ...] = field(
        init=False, repr=False, compare=False, hash=False
    )
    _edges: tuple["TypeEdgeConnection", ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "_children", (self.narrows_to,))
        object.__setattr__(
            self,
            "_edges",
            (TypeEdgeConnection(TypeEdge(TypeEdgeKind.NARROWS), self.narrows_to),),
        )

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return self._edges

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children


def is_type_guard_node(obj: object) -> TypeIs[TypeGuardNode]:
    """Return whether the argument is a TypeGuardNode instance."""
    return isinstance(obj, TypeGuardNode)


@dataclass(slots=True, frozen=True)
class TypeIsNode(TypeNode):
    """typing.TypeIs[T] - narrows type bidirectionally (PEP 742)."""

    narrows_to: TypeNode
    _children: tuple[TypeNode, ...] = field(
        init=False, repr=False, compare=False, hash=False
    )
    _edges: tuple["TypeEdgeConnection", ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "_children", (self.narrows_to,))
        object.__setattr__(
            self,
            "_edges",
            (TypeEdgeConnection(TypeEdge(TypeEdgeKind.NARROWS), self.narrows_to),),
        )

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return self._edges

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children


def is_type_is_node(obj: object) -> TypeIs[TypeIsNode]:
    """Return whether the argument is a TypeIsNode instance."""
    return isinstance(obj, TypeIsNode)


@dataclass(slots=True, frozen=True)
class FieldDef:
    """A named field with a type (not a TypeNode itself)."""

    name: str
    type: TypeNode
    required: bool = True
    metadata: MetadataCollection = field(
        default_factory=lambda: MetadataCollection.EMPTY
    )  # Metadata from Annotated on this field


class StructuredNode(TypeNode, ABC):
    """Base for types with named, typed fields."""

    @abstractmethod
    def get_fields(self) -> tuple[FieldDef, ...]:
        """Return the field definitions."""
        ...


def is_structured_node(obj: object) -> TypeIs[StructuredNode]:
    """Return whether the argument is a StructuredNode instance."""
    return isinstance(obj, StructuredNode)


@dataclass(slots=True, frozen=True)
class TypedDictNode(StructuredNode):
    """TypedDict with named fields."""

    name: str
    fields: tuple[FieldDef, ...]
    total: bool = True
    closed: bool = False  # PEP 728
    _children: tuple[TypeNode, ...] = field(
        init=False, repr=False, compare=False, hash=False
    )
    _edges: tuple["TypeEdgeConnection", ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "_children", tuple(f.type for f in self.fields))
        edges = tuple(
            TypeEdgeConnection(TypeEdge(TypeEdgeKind.FIELD, name=f.name), f.type)
            for f in self.fields
        )
        object.__setattr__(self, "_edges", edges)

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return self._edges

    @override
    def get_fields(self) -> tuple[FieldDef, ...]:
        return self.fields

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children


def is_typed_dict_node(obj: object) -> TypeIs[TypedDictNode]:
    """Return whether the argument is a TypedDictNode instance."""
    return isinstance(obj, TypedDictNode)


@dataclass(slots=True, frozen=True)
class NamedTupleNode(StructuredNode):
    """NamedTuple with named fields."""

    name: str
    fields: tuple[FieldDef, ...]
    _children: tuple[TypeNode, ...] = field(
        init=False, repr=False, compare=False, hash=False
    )
    _edges: tuple["TypeEdgeConnection", ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "_children", tuple(f.type for f in self.fields))
        edges = tuple(
            TypeEdgeConnection(TypeEdge(TypeEdgeKind.FIELD, name=f.name), f.type)
            for f in self.fields
        )
        object.__setattr__(self, "_edges", edges)

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return self._edges

    @override
    def get_fields(self) -> tuple[FieldDef, ...]:
        return self.fields

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children


def is_named_tuple_node(obj: object) -> TypeIs[NamedTupleNode]:
    """Return whether the argument is a NamedTupleNode instance."""
    return isinstance(obj, NamedTupleNode)


@dataclass(slots=True, frozen=True)
class DataclassFieldDef(FieldDef):
    """Extended field definition for dataclasses."""

    default: object | None = None
    default_factory: bool = False  # True if default is a factory
    init: bool = True
    repr: bool = True
    compare: bool = True
    kw_only: bool = False
    hash: bool | None = None


@dataclass(slots=True, frozen=True)
class DataclassNode(StructuredNode):
    """A dataclass with typed fields and configuration."""

    cls: type
    fields: tuple[DataclassFieldDef, ...]
    frozen: bool = False
    slots: bool = False
    kw_only: bool = False
    match_args: bool = True
    order: bool = False
    _children: tuple[TypeNode, ...] = field(
        init=False, repr=False, compare=False, hash=False
    )
    _edges: tuple["TypeEdgeConnection", ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "_children", tuple(f.type for f in self.fields))
        edges = tuple(
            TypeEdgeConnection(TypeEdge(TypeEdgeKind.FIELD, name=f.name), f.type)
            for f in self.fields
        )
        object.__setattr__(self, "_edges", edges)

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return self._edges

    @override
    def get_fields(self) -> tuple[FieldDef, ...]:
        return self.fields

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children


def is_dataclass_node(obj: object) -> TypeIs[DataclassNode]:
    """Return whether the argument is a DataclassNode instance."""
    return isinstance(obj, DataclassNode)


@dataclass(slots=True, frozen=True)
class EnumNode(TypeNode):
    """An Enum with typed members."""

    cls: type
    value_type: TypeNode  # The type of enum values (int, str, etc.)
    members: tuple[tuple[str, object], ...]  # (name, value) pairs
    _children: tuple[TypeNode, ...] = field(
        init=False, repr=False, compare=False, hash=False
    )
    _edges: tuple["TypeEdgeConnection", ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "_children", (self.value_type,))
        object.__setattr__(
            self,
            "_edges",
            (TypeEdgeConnection(TypeEdge(TypeEdgeKind.VALUE_TYPE), self.value_type),),
        )

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return self._edges

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children


def is_enum_node(obj: object) -> TypeIs[EnumNode]:
    """Return whether the argument is an EnumNode instance."""
    return isinstance(obj, EnumNode)


@dataclass(slots=True, frozen=True)
class NewTypeNode(TypeNode):
    """NewType('Name', base) - a distinct type alias for type checking."""

    name: str
    supertype: TypeNode
    _children: tuple[TypeNode, ...] = field(
        init=False, repr=False, compare=False, hash=False
    )
    _edges: tuple["TypeEdgeConnection", ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "_children", (self.supertype,))
        object.__setattr__(
            self,
            "_edges",
            (TypeEdgeConnection(TypeEdge(TypeEdgeKind.SUPERTYPE), self.supertype),),
        )

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return self._edges

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children


def is_new_type_node(obj: object) -> TypeIs[NewTypeNode]:
    """Return whether the argument is a NewTypeNode instance."""
    return isinstance(obj, NewTypeNode)


@dataclass(slots=True, frozen=True)
class Parameter:
    """A callable parameter (not a TypeNode itself)."""

    name: str
    type: TypeNode
    kind: str = "POSITIONAL_OR_KEYWORD"  # matches inspect.Parameter.Kind names
    default: object | None = None
    has_default: bool = False
    metadata: MetadataCollection = field(
        default_factory=lambda: MetadataCollection.EMPTY
    )


@dataclass(slots=True, frozen=True)
class SignatureNode(TypeNode):
    """A full callable signature with named parameters.

    More detailed than CallableNode - includes parameter names, kinds, defaults.
    Use for introspecting actual functions/methods.
    """

    parameters: tuple[Parameter, ...]
    returns: TypeNode
    type_params: tuple[TypeVarNode | ParamSpecNode | TypeVarTupleNode, ...] = ()
    _children: tuple[TypeNode, ...] = field(
        init=False, repr=False, compare=False, hash=False
    )
    _edges: tuple["TypeEdgeConnection", ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        children: list[TypeNode] = [p.type for p in self.parameters]
        children.append(self.returns)
        children.extend(self.type_params)
        object.__setattr__(self, "_children", tuple(children))

        edges: list[TypeEdgeConnection] = [
            TypeEdgeConnection(TypeEdge(TypeEdgeKind.PARAM, name=p.name), p.type)
            for p in self.parameters
        ]
        edges.append(TypeEdgeConnection(TypeEdge(TypeEdgeKind.RETURN), self.returns))
        edges.extend(
            TypeEdgeConnection(TypeEdge(TypeEdgeKind.TYPE_PARAM, index=i), tp)
            for i, tp in enumerate(self.type_params)
        )
        object.__setattr__(self, "_edges", tuple(edges))

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return self._edges

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children


def is_signature_node(obj: object) -> TypeIs[SignatureNode]:
    """Return whether the argument is a SignatureNode instance."""
    return isinstance(obj, SignatureNode)


@dataclass(slots=True, frozen=True)
class MethodSig:
    """A method signature (not a TypeNode itself)."""

    name: str
    signature: SignatureNode | CallableNode
    is_classmethod: bool = False
    is_staticmethod: bool = False
    is_property: bool = False


def is_method_sig(obj: object) -> TypeIs[MethodSig]:
    """Return whether the argument is a MethodSig instance."""
    return isinstance(obj, MethodSig)


@dataclass(slots=True, frozen=True)
class ProtocolNode(TypeNode):
    """Protocol defining structural interface."""

    name: str
    methods: tuple[MethodSig, ...]
    attributes: tuple[FieldDef, ...] = ()
    is_runtime_checkable: bool = False
    _children: tuple[TypeNode, ...] = field(
        init=False, repr=False, compare=False, hash=False
    )
    _edges: tuple["TypeEdgeConnection", ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        children: list[TypeNode] = [mt.signature for mt in self.methods]
        children.extend(a.type for a in self.attributes)
        object.__setattr__(self, "_children", tuple(children))

        edges: list[TypeEdgeConnection] = [
            TypeEdgeConnection(
                TypeEdge(TypeEdgeKind.METHOD, name=mt.name), mt.signature
            )
            for mt in self.methods
        ]
        edges.extend(
            TypeEdgeConnection(TypeEdge(TypeEdgeKind.FIELD, name=a.name), a.type)
            for a in self.attributes
        )
        object.__setattr__(self, "_edges", tuple(edges))

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return self._edges

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children


def is_protocol_node(obj: object) -> TypeIs[ProtocolNode]:
    """Return whether the argument is a ProtocolNode instance."""
    return isinstance(obj, ProtocolNode)


@dataclass(slots=True, frozen=True)
class FunctionNode(TypeNode):
    """A function with full type information.

    Use this for introspecting actual function definitions, not just
    callable type annotations.
    """

    name: str
    signature: SignatureNode
    is_async: bool = False
    is_generator: bool = False
    decorators: tuple[str, ...] = ()  # Decorator names for reference
    _children: tuple[TypeNode, ...] = field(
        init=False, repr=False, compare=False, hash=False
    )
    _edges: tuple["TypeEdgeConnection", ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "_children", (self.signature,))
        object.__setattr__(
            self,
            "_edges",
            (TypeEdgeConnection(TypeEdge(TypeEdgeKind.SIGNATURE), self.signature),),
        )

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return self._edges

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children


def is_function_node(obj: object) -> TypeIs[FunctionNode]:
    """Return whether the argument is a FunctionNode instance."""
    return isinstance(obj, FunctionNode)


@dataclass(slots=True, frozen=True)
class ClassNode(TypeNode):
    """A class with full type information.

    This is a meta-node representing the class definition itself, including
    its type parameters, bases, and members.
    """

    cls: type
    name: str
    type_params: tuple[TypeVarNode | ParamSpecNode | TypeVarTupleNode, ...] = ()
    bases: tuple[TypeNode, ...] = ()
    methods: tuple[MethodSig, ...] = ()
    class_vars: tuple[FieldDef, ...] = ()
    instance_vars: tuple[FieldDef, ...] = ()
    is_abstract: bool = False
    is_final: bool = False
    _children: tuple[TypeNode, ...] = field(
        init=False, repr=False, compare=False, hash=False
    )
    _edges: tuple["TypeEdgeConnection", ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        children: list[TypeNode] = list(self.type_params)
        children.extend(self.bases)
        children.extend(mt.signature for mt in self.methods)
        children.extend(v.type for v in self.class_vars)
        children.extend(v.type for v in self.instance_vars)
        object.__setattr__(self, "_children", tuple(children))

        edges: list[TypeEdgeConnection] = [
            TypeEdgeConnection(TypeEdge(TypeEdgeKind.TYPE_PARAM, index=i), tp)
            for i, tp in enumerate(self.type_params)
        ]
        edges.extend(
            TypeEdgeConnection(TypeEdge(TypeEdgeKind.BASE, index=i), base)
            for i, base in enumerate(self.bases)
        )
        edges.extend(
            TypeEdgeConnection(
                TypeEdge(TypeEdgeKind.METHOD, name=mt.name), mt.signature
            )
            for mt in self.methods
        )
        edges.extend(
            TypeEdgeConnection(TypeEdge(TypeEdgeKind.FIELD, name=v.name), v.type)
            for v in self.class_vars
        )
        edges.extend(
            TypeEdgeConnection(TypeEdge(TypeEdgeKind.FIELD, name=v.name), v.type)
            for v in self.instance_vars
        )
        object.__setattr__(self, "_edges", tuple(edges))

    @override
    def edges(self) -> "Sequence[TypeEdgeConnection]":
        return self._edges

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children


def is_class_node(obj: object) -> TypeIs[ClassNode]:
    """Return whether the argument is a ClassNode instance."""
    return isinstance(obj, ClassNode)
