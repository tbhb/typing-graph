"""Type annotation graph node hierarchy."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING
from typing_extensions import TypeIs, override

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
    metadata: tuple[object, ...] = field(default=(), kw_only=True)
    qualifiers: "frozenset[Qualifier]" = field(default_factory=frozenset, kw_only=True)

    @abstractmethod
    def children(self) -> "Sequence[TypeNode]":
        """Return child type nodes for graph traversal."""
        ...


def is_type_node(obj: object) -> TypeIs[TypeNode]:
    """Return whether the argument is an instance of TypeNode."""
    return isinstance(obj, TypeNode)


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

    def __post_init__(self) -> None:
        children: list[TypeNode] = list(self.constraints)
        if self.bound:
            children.append(self.bound)
        if self.default:
            children.append(self.default)
        object.__setattr__(self, "_children", tuple(children))

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

    @override
    def children(self) -> "Sequence[TypeNode]":
        if self.default:
            return (self.default,)
        return ()


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

    @override
    def children(self) -> "Sequence[TypeNode]":
        if self.default:
            return (self.default,)
        return ()


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

    def __post_init__(self) -> None:
        object.__setattr__(self, "_children", (*self.prefix, self.param_spec))

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

    @override
    def children(self) -> "Sequence[TypeNode]":
        return (self.target,)


def is_unpack_node(obj: object) -> TypeIs[UnpackNode]:
    """Return whether the argument is an UnpackNode instance."""
    return isinstance(obj, UnpackNode)


@dataclass(slots=True, frozen=True)
class ConcreteType(TypeNode):
    """A non-generic nominal type: int, str, MyClass, etc."""

    cls: type

    @override
    def children(self) -> "Sequence[TypeNode]":
        return ()


def is_concrete_type(obj: object) -> TypeIs[ConcreteType]:
    """Return whether the argument is a ConcreteType instance."""
    return isinstance(obj, ConcreteType)


@dataclass(slots=True, frozen=True)
class GenericTypeNode(TypeNode):
    """An unsubscripted generic (type constructor): list, Dict, etc."""

    cls: type
    type_params: tuple[TypeVarNode | ParamSpecNode | TypeVarTupleNode, ...] = ()

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self.type_params


def is_generic_type(obj: object) -> TypeIs[GenericTypeNode]:
    """Return whether the argument is a GenericType instance."""
    return isinstance(obj, GenericTypeNode)


class SpecialForm(TypeNode, ABC):
    """Base for special typing constructs that aren't concrete types."""


@dataclass(slots=True, frozen=True)
class AnyType(TypeNode):
    """typing.Any - compatible with all types (gradual typing escape hatch)."""

    @override
    def children(self) -> "Sequence[TypeNode]":
        return ()


def is_any_type_node(obj: object) -> TypeIs[AnyType]:
    """Return whether the argument is an AnyType instance."""
    return isinstance(obj, AnyType)


@dataclass(slots=True, frozen=True)
class NeverType(TypeNode):
    """typing.Never / typing.NoReturn - the bottom type (uninhabited)."""

    @override
    def children(self) -> "Sequence[TypeNode]":
        return ()


def is_never_type_node(obj: object) -> TypeIs[NeverType]:
    """Return whether the argument is a NeverType instance."""
    return isinstance(obj, NeverType)


@dataclass(slots=True, frozen=True)
class SelfType(TypeNode):
    """typing.Self - reference to the enclosing class."""

    @override
    def children(self) -> "Sequence[TypeNode]":
        return ()


def is_self_type_node(obj: object) -> TypeIs[SelfType]:
    """Return whether the argument is a SelfType instance."""
    return isinstance(obj, SelfType)


@dataclass(slots=True, frozen=True)
class LiteralStringType(TypeNode):
    """typing.LiteralString - any literal string value (PEP 675)."""

    @override
    def children(self) -> "Sequence[TypeNode]":
        return ()


def is_literal_string_type_node(obj: object) -> TypeIs[LiteralStringType]:
    """Return whether the argument is a LiteralStringType instance."""
    return isinstance(obj, LiteralStringType)


@dataclass(slots=True, frozen=True)
class EllipsisType(TypeNode):
    """The ... used in Callable[..., R] and Tuple[T, ...]."""

    @override
    def children(self) -> "Sequence[TypeNode]":
        return ()


def is_ellipsis_type_node(obj: object) -> TypeIs[EllipsisType]:
    """Return whether the argument is an EllipsisType instance."""
    return isinstance(obj, EllipsisType)


# === Forward References ===


class RefState:
    """Resolution state for forward references."""

    @dataclass(slots=True, frozen=True)
    class Unresolved:
        """Not yet attempted to resolve."""

    @dataclass(slots=True, frozen=True)
    class Resolved:
        """Successfully resolved to a type."""

        node: TypeNode

    @dataclass(slots=True, frozen=True)
    class Failed:
        """Resolution attempted but failed."""

        error: str


def is_ref_state_resolved(state: object) -> TypeIs[RefState.Resolved]:
    """Return whether the argument is a RefState.Resolved instance."""
    return isinstance(state, RefState.Resolved)


def is_ref_state_failed(state: object) -> TypeIs[RefState.Failed]:
    """Return whether the argument is a RefState.Failed instance."""
    return isinstance(state, RefState.Failed)


def is_ref_state_unresolved(state: object) -> TypeIs[RefState.Unresolved]:
    """Return whether the argument is a RefState.Unresolved instance."""
    return isinstance(state, RefState.Unresolved)


@dataclass(slots=True, frozen=True)
class ForwardRef(TypeNode):
    """A string forward reference like 'MyClass'."""

    ref: str
    state: RefState.Unresolved | RefState.Resolved | RefState.Failed = field(
        default_factory=RefState.Unresolved
    )

    @override
    def children(self) -> "Sequence[TypeNode]":
        if isinstance(self.state, RefState.Resolved):
            return (self.state.node,)
        return ()


def is_forward_ref_node(obj: object) -> TypeIs[ForwardRef]:
    """Return whether the argument is a ForwardRef instance."""
    return isinstance(obj, ForwardRef)


@dataclass(slots=True, frozen=True)
class LiteralNode(TypeNode):
    """Literal[v1, v2, ...] - specific literal values as types."""

    values: tuple[object, ...]

    @override
    def children(self) -> "Sequence[TypeNode]":
        return ()


def is_literal_node(obj: object) -> TypeIs[LiteralNode]:
    """Return whether the argument is a LiteralNode instance."""
    return isinstance(obj, LiteralNode)


@dataclass(slots=True, frozen=True)
class SubscriptedGeneric(TypeNode):
    """Generic with type args applied: List[int], Dict[str, T], etc."""

    origin: TypeNode  # GenericType or another SubscriptedGeneric
    args: tuple[TypeNode, ...]
    _children: tuple[TypeNode, ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "_children", (self.origin, *self.args))

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children


def is_subscripted_generic_node(obj: object) -> TypeIs[SubscriptedGeneric]:
    """Return whether the argument is a SubscriptedGeneric instance."""
    return isinstance(obj, SubscriptedGeneric)


@dataclass(slots=True, frozen=True)
class GenericAlias(TypeNode):
    """Parameterized type alias: type Vector[T] = list[T] (PEP 695)."""

    name: str
    type_params: tuple[TypeVarNode | ParamSpecNode | TypeVarTupleNode, ...]
    value: TypeNode  # The aliased type (may reference type_params)
    _children: tuple[TypeNode, ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "_children", (*self.type_params, self.value))

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children


def is_generic_alias_node(obj: object) -> TypeIs[GenericAlias]:
    """Return whether the argument is a GenericAlias instance."""
    return isinstance(obj, GenericAlias)


@dataclass(slots=True, frozen=True)
class TypeAliasNode(TypeNode):
    """typing.TypeAlias or PEP 695 type statement runtime object."""

    name: str
    value: TypeNode

    @override
    def children(self) -> "Sequence[TypeNode]":
        return (self.value,)


def is_type_alias_node(obj: object) -> TypeIs[TypeAliasNode]:
    """Return whether the argument is a TypeAliasNode instance."""
    return isinstance(obj, TypeAliasNode)


@dataclass(slots=True, frozen=True)
class UnionTypeNode(TypeNode):
    """A | B (non-discriminated)."""

    members: tuple[TypeNode, ...]

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self.members


def is_union_type_node(obj: object) -> TypeIs[UnionTypeNode]:
    """Return whether the argument is a UnionType instance."""
    return isinstance(obj, UnionTypeNode)


@dataclass(slots=True, frozen=True)
class DiscriminatedUnion(TypeNode):
    """A union discriminated by a literal field value.

    Example:
        Dog = TypedDict('Dog', {'kind': Literal['dog'], 'bark': int})
        Cat = TypedDict('Cat', {'kind': Literal['cat'], 'meow': int})
        Pet = Dog | Cat  # discriminated on 'kind'
    """

    discriminant: str  # The field name used to discriminate
    variants: dict[object, TypeNode]  # Literal value -> variant type
    _children: tuple[TypeNode, ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "_children", tuple(self.variants.values()))

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children


def is_discriminated_union_node(obj: object) -> TypeIs[DiscriminatedUnion]:
    """Return whether the argument is a DiscriminatedUnion instance."""
    return isinstance(obj, DiscriminatedUnion)


@dataclass(slots=True, frozen=True)
class IntersectionType(TypeNode):
    """Intersection of types (not yet in typing, but used by type checkers)."""

    members: tuple[TypeNode, ...]

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self.members


def is_intersection_type_node(obj: object) -> TypeIs[IntersectionType]:
    """Return whether the argument is an IntersectionType instance."""
    return isinstance(obj, IntersectionType)


@dataclass(slots=True, frozen=True)
class CallableType(TypeNode):
    """Callable[[P1, P2], R] or Callable[P, R] or Callable[..., R]."""

    params: tuple[TypeNode, ...] | ParamSpecNode | ConcatenateNode | EllipsisType
    returns: TypeNode
    _children: tuple[TypeNode, ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        if isinstance(self.params, tuple):
            children = (*self.params, self.returns)
        else:
            children = (self.params, self.returns)
        object.__setattr__(self, "_children", children)

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children


def is_callable_type_node(obj: object) -> TypeIs[CallableType]:
    """Return whether the argument is a CallableType instance."""
    return isinstance(obj, CallableType)


@dataclass(slots=True, frozen=True)
class TupleType(TypeNode):
    """Tuple types in various forms.

    Examples:
        tuple[int, str]      - heterogeneous (elements=(int, str), homogeneous=False)
        tuple[int, ...]      - homogeneous (elements=(int,), homogeneous=True)
        tuple[int, *Ts, str] - variadic (contains UnpackNode)
        tuple[()]            - empty tuple (elements=(), homogeneous=False)
    """

    elements: tuple[TypeNode, ...]
    homogeneous: bool = False  # True for tuple[T, ...]

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self.elements


def is_tuple_type_node(obj: object) -> TypeIs[TupleType]:
    """Return whether the argument is a TupleType instance."""
    return isinstance(obj, TupleType)


@dataclass(slots=True, frozen=True)
class AnnotatedType(TypeNode):
    """Annotated[T, metadata, ...].

    Note: During graph construction, you may choose to hoist metadata to the
    inner type's `metadata` field and elide the AnnotatedType wrapper. This
    node represents the un-elided form.
    """

    base: TypeNode
    # Note: metadata is on base TypeNode, but annotations here are the raw
    # Annotated arguments, which may include type-system extensions
    annotations: tuple[object, ...] = ()

    @override
    def children(self) -> "Sequence[TypeNode]":
        return (self.base,)


def is_annotated_type_node(obj: object) -> TypeIs[AnnotatedType]:
    """Return whether the argument is an AnnotatedType instance."""
    return isinstance(obj, AnnotatedType)


@dataclass(slots=True, frozen=True)
class MetaType(TypeNode):
    """Type[T] or type[T] - the class object itself, not an instance."""

    of: TypeNode

    @override
    def children(self) -> "Sequence[TypeNode]":
        return (self.of,)


def is_meta_type_node(obj: object) -> TypeIs[MetaType]:
    """Return whether the argument is a MetaType instance."""
    return isinstance(obj, MetaType)


@dataclass(slots=True, frozen=True)
class TypeGuardType(TypeNode):
    """typing.TypeGuard[T] - narrows type in true branch (PEP 647)."""

    narrows_to: TypeNode

    @override
    def children(self) -> "Sequence[TypeNode]":
        return (self.narrows_to,)


def is_type_guard_type_node(obj: object) -> TypeIs[TypeGuardType]:
    """Return whether the argument is a TypeGuardType instance."""
    return isinstance(obj, TypeGuardType)


@dataclass(slots=True, frozen=True)
class TypeIsType(TypeNode):
    """typing.TypeIs[T] - narrows type bidirectionally (PEP 742)."""

    narrows_to: TypeNode

    @override
    def children(self) -> "Sequence[TypeNode]":
        return (self.narrows_to,)


def is_type_is_type_node(obj: object) -> TypeIs[TypeIsType]:
    """Return whether the argument is a TypeIsType instance."""
    return isinstance(obj, TypeIsType)


@dataclass(slots=True, frozen=True)
class FieldDef:
    """A named field with a type (not a TypeNode itself)."""

    name: str
    type: TypeNode
    required: bool = True
    metadata: tuple[object, ...] = ()  # Metadata from Annotated on this field


class StructuredType(TypeNode, ABC):
    """Base for types with named, typed fields."""

    @abstractmethod
    def get_fields(self) -> tuple[FieldDef, ...]:
        """Return the field definitions."""
        ...


def is_structured_type_node(obj: object) -> TypeIs[StructuredType]:
    """Return whether the argument is a StructuredType instance."""
    return isinstance(obj, StructuredType)


@dataclass(slots=True, frozen=True)
class TypedDictType(StructuredType):
    """TypedDict with named fields."""

    name: str
    fields: tuple[FieldDef, ...]
    total: bool = True
    closed: bool = False  # PEP 728
    _children: tuple[TypeNode, ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "_children", tuple(f.type for f in self.fields))

    @override
    def get_fields(self) -> tuple[FieldDef, ...]:
        return self.fields

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children


def is_typed_dict_type_node(obj: object) -> TypeIs[TypedDictType]:
    """Return whether the argument is a TypedDictType instance."""
    return isinstance(obj, TypedDictType)


@dataclass(slots=True, frozen=True)
class NamedTupleType(StructuredType):
    """NamedTuple with named fields."""

    name: str
    fields: tuple[FieldDef, ...]
    _children: tuple[TypeNode, ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "_children", tuple(f.type for f in self.fields))

    @override
    def get_fields(self) -> tuple[FieldDef, ...]:
        return self.fields

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children


def is_named_tuple_type_node(obj: object) -> TypeIs[NamedTupleType]:
    """Return whether the argument is a NamedTupleType instance."""
    return isinstance(obj, NamedTupleType)


# === Dataclass ===


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
class DataclassType(StructuredType):
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

    def __post_init__(self) -> None:
        object.__setattr__(self, "_children", tuple(f.type for f in self.fields))

    @override
    def get_fields(self) -> tuple[FieldDef, ...]:
        return self.fields

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children


def is_dataclass_type_node(obj: object) -> TypeIs[DataclassType]:
    """Return whether the argument is a DataclassType instance."""
    return isinstance(obj, DataclassType)


@dataclass(slots=True, frozen=True)
class EnumType(TypeNode):
    """An Enum with typed members."""

    cls: type
    value_type: TypeNode  # The type of enum values (int, str, etc.)
    members: tuple[tuple[str, object], ...]  # (name, value) pairs

    @override
    def children(self) -> "Sequence[TypeNode]":
        return (self.value_type,)


def is_enum_type_node(obj: object) -> TypeIs[EnumType]:
    """Return whether the argument is an EnumType instance."""
    return isinstance(obj, EnumType)


@dataclass(slots=True, frozen=True)
class NewTypeNode(TypeNode):
    """NewType('Name', base) - a distinct type alias for type checking."""

    name: str
    supertype: TypeNode

    @override
    def children(self) -> "Sequence[TypeNode]":
        return (self.supertype,)


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
    metadata: tuple[object, ...] = ()


@dataclass(slots=True, frozen=True)
class SignatureNode(TypeNode):
    """A full callable signature with named parameters.

    More detailed than CallableType - includes parameter names, kinds, defaults.
    Use for introspecting actual functions/methods.
    """

    parameters: tuple[Parameter, ...]
    returns: TypeNode
    type_params: tuple[TypeVarNode | ParamSpecNode | TypeVarTupleNode, ...] = ()
    _children: tuple[TypeNode, ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        children: list[TypeNode] = [p.type for p in self.parameters]
        children.append(self.returns)
        children.extend(self.type_params)
        object.__setattr__(self, "_children", tuple(children))

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
    signature: SignatureNode | CallableType
    is_classmethod: bool = False
    is_staticmethod: bool = False
    is_property: bool = False


def is_method_sig(obj: object) -> TypeIs[MethodSig]:
    """Return whether the argument is a MethodSig instance."""
    return isinstance(obj, MethodSig)


@dataclass(slots=True, frozen=True)
class ProtocolType(TypeNode):
    """Protocol defining structural interface."""

    name: str
    methods: tuple[MethodSig, ...]
    attributes: tuple[FieldDef, ...] = ()
    is_runtime_checkable: bool = False
    _children: tuple[TypeNode, ...] = field(
        init=False, repr=False, compare=False, hash=False
    )

    def __post_init__(self) -> None:
        children: list[TypeNode] = [mt.signature for mt in self.methods]
        children.extend(a.type for a in self.attributes)
        object.__setattr__(self, "_children", tuple(children))

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children


def is_protocol_type_node(obj: object) -> TypeIs[ProtocolType]:
    """Return whether the argument is a ProtocolType instance."""
    return isinstance(obj, ProtocolType)


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

    @override
    def children(self) -> "Sequence[TypeNode]":
        return (self.signature,)


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

    def __post_init__(self) -> None:
        children: list[TypeNode] = list(self.type_params)
        children.extend(self.bases)
        children.extend(mt.signature for mt in self.methods)
        children.extend(v.type for v in self.class_vars)
        children.extend(v.type for v in self.instance_vars)
        object.__setattr__(self, "_children", tuple(children))

    @override
    def children(self) -> "Sequence[TypeNode]":
        return self._children


def is_class_node(obj: object) -> TypeIs[ClassNode]:
    """Return whether the argument is a ClassNode instance."""
    return isinstance(obj, ClassNode)
