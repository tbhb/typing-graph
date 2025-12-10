# pyright: reportAny=false, reportExplicitAny=false

from collections.abc import Sequence
from dataclasses import dataclass
from enum import IntEnum

from hypothesis import HealthCheck, given, settings, strategies as st
from hypothesis.strategies import DrawFn, composite

from typing_graph._node import (
    AnnotatedNode,
    AnyNode,
    CallableNode,
    ClassNode,
    ConcatenateNode,
    ConcreteNode,
    DataclassFieldDef,
    DataclassNode,
    DiscriminatedUnionNode,
    EllipsisNode,
    EnumNode,
    FieldDef,
    ForwardRefNode,
    FunctionNode,
    GenericAliasNode,
    GenericTypeNode,
    IntersectionNode,
    LiteralNode,
    LiteralStringNode,
    MetaNode,
    MethodSig,
    NamedTupleNode,
    NeverNode,
    NewTypeNode,
    Parameter,
    ParamSpecNode,
    ProtocolNode,
    RefFailed,
    RefResolved,
    RefUnresolved,
    SelfNode,
    SignatureNode,
    SubscriptedGenericNode,
    TupleNode,
    TypeAliasNode,
    TypedDictNode,
    TypeEdgeConnection,
    TypeGuardNode,
    TypeIsNode,
    TypeNode,
    TypeVarNode,
    TypeVarTupleNode,
    UnionNode,
    UnpackNode,
    Variance,
)


@composite
def any_nodes(draw: DrawFn) -> AnyNode:
    _ = draw(st.just(True))
    return AnyNode()


@composite
def never_nodes(draw: DrawFn) -> NeverNode:
    _ = draw(st.just(True))
    return NeverNode()


@composite
def self_nodes(draw: DrawFn) -> SelfNode:
    _ = draw(st.just(True))
    return SelfNode()


@composite
def literal_string_nodes(draw: DrawFn) -> LiteralStringNode:
    _ = draw(st.just(True))
    return LiteralStringNode()


@composite
def ellipsis_nodes(draw: DrawFn) -> EllipsisNode:
    _ = draw(st.just(True))
    return EllipsisNode()


@composite
def literal_nodes(draw: DrawFn) -> LiteralNode:
    values = draw(
        st.lists(
            st.one_of(
                st.integers(-100, 100),
                st.text(min_size=1, max_size=10),
                st.booleans(),
            ),
            min_size=1,
            max_size=5,
        )
    )
    return LiteralNode(values=tuple(values))


@composite
def concrete_nodes(draw: DrawFn) -> ConcreteNode:
    cls = draw(st.sampled_from([int, str, float, bool, bytes, object, type(None)]))
    return ConcreteNode(cls=cls)


@composite
def typevar_nodes(draw: DrawFn) -> TypeVarNode:
    name = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=5))
    variance = draw(st.sampled_from(list(Variance)))
    has_bound = draw(st.booleans())
    has_constraints = draw(st.booleans()) if not has_bound else False
    has_default = draw(st.booleans())

    bound = ConcreteNode(cls=int) if has_bound else None
    constraints: tuple[TypeNode, ...] = ()
    if has_constraints:
        count = draw(st.integers(2, 4))
        constraints = tuple(ConcreteNode(cls=int) for _ in range(count))
    default = ConcreteNode(cls=str) if has_default else None

    return TypeVarNode(
        name=name,
        variance=variance,
        bound=bound,
        constraints=constraints,
        default=default,
    )


@composite
def paramspec_nodes(draw: DrawFn) -> ParamSpecNode:
    name = draw(st.text(alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ", min_size=1, max_size=3))
    has_default = draw(st.booleans())
    default = ConcreteNode(cls=int) if has_default else None
    return ParamSpecNode(name=name, default=default)


@composite
def typevartuple_nodes(draw: DrawFn) -> TypeVarTupleNode:
    name = draw(st.text(alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ", min_size=1, max_size=3))
    has_default = draw(st.booleans())
    default = ConcreteNode(cls=int) if has_default else None
    return TypeVarTupleNode(name=name, default=default)


@composite
def concatenate_nodes(draw: DrawFn) -> ConcatenateNode:
    prefix_count = draw(st.integers(0, 3))
    prefix = tuple(ConcreteNode(cls=int) for _ in range(prefix_count))
    param_spec = ParamSpecNode(name="P")
    return ConcatenateNode(prefix=prefix, param_spec=param_spec)


@composite
def unpack_nodes(draw: DrawFn) -> UnpackNode:
    target: TypeNode = draw(
        st.one_of(
            st.just(TypeVarTupleNode(name="Ts")),
            st.just(TupleNode(elements=(ConcreteNode(cls=int),), homogeneous=True)),
        )
    )
    return UnpackNode(target=target)


@composite
def generic_type_nodes(draw: DrawFn) -> GenericTypeNode:
    cls = draw(st.sampled_from([list, dict, set, frozenset]))
    type_param_count = draw(st.integers(0, 2))
    type_params: tuple[TypeVarNode | ParamSpecNode | TypeVarTupleNode, ...] = tuple(
        TypeVarNode(name=f"T{i}") for i in range(type_param_count)
    )
    return GenericTypeNode(cls=cls, type_params=type_params)


@composite
def subscripted_generic_nodes(draw: DrawFn) -> SubscriptedGenericNode:
    origin = GenericTypeNode(cls=list, type_params=(TypeVarNode(name="T"),))
    arg_count = draw(st.integers(1, 3))
    args = tuple(ConcreteNode(cls=int) for _ in range(arg_count))
    return SubscriptedGenericNode(origin=origin, args=args)


@composite
def generic_alias_nodes(draw: DrawFn) -> GenericAliasNode:
    name = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10))
    type_param_count = draw(st.integers(0, 2))
    type_params: tuple[TypeVarNode | ParamSpecNode | TypeVarTupleNode, ...] = tuple(
        TypeVarNode(name=f"T{i}") for i in range(type_param_count)
    )
    value = ConcreteNode(cls=int)
    return GenericAliasNode(name=name, type_params=type_params, value=value)


@composite
def type_alias_nodes(draw: DrawFn) -> TypeAliasNode:
    name = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10))
    value = ConcreteNode(cls=int)
    return TypeAliasNode(name=name, value=value)


@composite
def union_nodes(draw: DrawFn) -> UnionNode:
    member_count = draw(st.integers(2, 4))
    members = tuple(ConcreteNode(cls=int) for _ in range(member_count))
    return UnionNode(members=members)


@composite
def discriminated_union_nodes(draw: DrawFn) -> DiscriminatedUnionNode:
    variant_count = draw(st.integers(2, 4))
    variants: dict[object, TypeNode] = {
        f"variant{i}": ConcreteNode(cls=int) for i in range(variant_count)
    }
    return DiscriminatedUnionNode(discriminant="kind", variants=variants)


@composite
def intersection_nodes(draw: DrawFn) -> IntersectionNode:
    member_count = draw(st.integers(2, 4))
    members = tuple(ConcreteNode(cls=int) for _ in range(member_count))
    return IntersectionNode(members=members)


@composite
def callable_nodes(draw: DrawFn) -> CallableNode:
    variant = draw(
        st.sampled_from(["tuple_params", "paramspec", "concatenate", "ellipsis"])
    )
    returns = ConcreteNode(cls=int)

    if variant == "tuple_params":
        param_count = draw(st.integers(0, 3))
        params: (
            tuple[TypeNode, ...] | ParamSpecNode | ConcatenateNode | EllipsisNode
        ) = tuple(ConcreteNode(cls=int) for _ in range(param_count))
    elif variant == "paramspec":
        params = ParamSpecNode(name="P")
    elif variant == "concatenate":
        params = ConcatenateNode(
            prefix=(ConcreteNode(cls=int),), param_spec=ParamSpecNode(name="P")
        )
    else:
        params = EllipsisNode()

    return CallableNode(params=params, returns=returns)


@composite
def tuple_nodes(draw: DrawFn) -> TupleNode:
    variant = draw(st.sampled_from(["heterogeneous", "homogeneous", "empty"]))

    if variant == "empty":
        return TupleNode(elements=(), homogeneous=False)
    if variant == "homogeneous":
        return TupleNode(elements=(ConcreteNode(cls=int),), homogeneous=True)
    elem_count = draw(st.integers(1, 4))
    elements = tuple(ConcreteNode(cls=int) for _ in range(elem_count))
    return TupleNode(elements=elements, homogeneous=False)


@composite
def annotated_nodes(draw: DrawFn) -> AnnotatedNode:
    base = ConcreteNode(cls=int)
    annotation_count = draw(st.integers(1, 3))
    annotations = tuple(f"annotation{i}" for i in range(annotation_count))
    return AnnotatedNode(base=base, annotations=annotations)


@composite
def meta_nodes(draw: DrawFn) -> MetaNode:
    _ = draw(st.just(True))
    of = ConcreteNode(cls=int)
    return MetaNode(of=of)


@composite
def type_guard_nodes(draw: DrawFn) -> TypeGuardNode:
    _ = draw(st.just(True))
    narrows_to = ConcreteNode(cls=int)
    return TypeGuardNode(narrows_to=narrows_to)


@composite
def type_is_nodes(draw: DrawFn) -> TypeIsNode:
    _ = draw(st.just(True))
    narrows_to = ConcreteNode(cls=int)
    return TypeIsNode(narrows_to=narrows_to)


@composite
def forward_ref_nodes(draw: DrawFn) -> ForwardRefNode:
    ref = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10))
    state_variant = draw(st.sampled_from(["unresolved", "resolved", "failed"]))

    if state_variant == "unresolved":
        return ForwardRefNode(ref=ref, state=RefUnresolved())
    if state_variant == "resolved":
        return ForwardRefNode(ref=ref, state=RefResolved(node=ConcreteNode(cls=int)))
    return ForwardRefNode(ref=ref, state=RefFailed(error="Test error"))


@composite
def field_defs(draw: DrawFn) -> FieldDef:
    name = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10))
    return FieldDef(name=name, type=ConcreteNode(cls=int), required=draw(st.booleans()))


@composite
def typed_dict_nodes(draw: DrawFn) -> TypedDictNode:
    name = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10))
    field_count = draw(st.integers(0, 4))
    fields = tuple(
        FieldDef(name=f"field{i}", type=ConcreteNode(cls=int))
        for i in range(field_count)
    )
    return TypedDictNode(
        name=name,
        fields=fields,
        total=draw(st.booleans()),
        closed=draw(st.booleans()),
    )


@composite
def named_tuple_nodes(draw: DrawFn) -> NamedTupleNode:
    name = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10))
    field_count = draw(st.integers(0, 4))
    fields = tuple(
        FieldDef(name=f"field{i}", type=ConcreteNode(cls=int))
        for i in range(field_count)
    )
    return NamedTupleNode(name=name, fields=fields)


@composite
def dataclass_field_defs(draw: DrawFn) -> DataclassFieldDef:
    name = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10))
    return DataclassFieldDef(
        name=name,
        type=ConcreteNode(cls=int),
        required=draw(st.booleans()),
        init=draw(st.booleans()),
        repr=draw(st.booleans()),
        compare=draw(st.booleans()),
        kw_only=draw(st.booleans()),
    )


@dataclass
class _SampleDataclass:
    x: int


@composite
def dataclass_nodes(draw: DrawFn) -> DataclassNode:
    field_count = draw(st.integers(0, 4))
    fields = tuple(
        DataclassFieldDef(name=f"field{i}", type=ConcreteNode(cls=int))
        for i in range(field_count)
    )
    return DataclassNode(
        cls=_SampleDataclass,
        fields=fields,
        frozen=draw(st.booleans()),
        slots=draw(st.booleans()),
        kw_only=draw(st.booleans()),
    )


class _SampleEnum(IntEnum):
    A = 1
    B = 2


@composite
def enum_nodes(draw: DrawFn) -> EnumNode:
    _ = draw(st.just(True))
    members = (("A", 1), ("B", 2))
    return EnumNode(cls=_SampleEnum, value_type=ConcreteNode(cls=int), members=members)


@composite
def new_type_nodes(draw: DrawFn) -> NewTypeNode:
    name = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10))
    supertype = ConcreteNode(cls=int)
    return NewTypeNode(name=name, supertype=supertype)


@composite
def parameters(draw: DrawFn) -> Parameter:
    name = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10))
    kind = draw(
        st.sampled_from(
            [
                "POSITIONAL_ONLY",
                "POSITIONAL_OR_KEYWORD",
                "VAR_POSITIONAL",
                "KEYWORD_ONLY",
                "VAR_KEYWORD",
            ]
        )
    )
    return Parameter(
        name=name,
        type=ConcreteNode(cls=int),
        kind=kind,
        has_default=draw(st.booleans()),
    )


@composite
def signature_nodes(draw: DrawFn) -> SignatureNode:
    param_count = draw(st.integers(0, 3))
    params = tuple(
        Parameter(name=f"p{i}", type=ConcreteNode(cls=int)) for i in range(param_count)
    )
    type_param_count = draw(st.integers(0, 2))
    type_params: tuple[TypeVarNode | ParamSpecNode | TypeVarTupleNode, ...] = tuple(
        TypeVarNode(name=f"T{i}") for i in range(type_param_count)
    )
    returns = ConcreteNode(cls=int)
    return SignatureNode(parameters=params, returns=returns, type_params=type_params)


@composite
def method_sigs(draw: DrawFn) -> MethodSig:
    name = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10))
    signature = SignatureNode(
        parameters=(Parameter(name="self", type=SelfNode()),),
        returns=ConcreteNode(cls=int),
    )
    return MethodSig(
        name=name,
        signature=signature,
        is_classmethod=draw(st.booleans()),
        is_staticmethod=draw(st.booleans()),
        is_property=draw(st.booleans()),
    )


@composite
def protocol_nodes(draw: DrawFn) -> ProtocolNode:
    name = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10))
    method_count = draw(st.integers(0, 3))
    methods = tuple(
        MethodSig(
            name=f"method{i}",
            signature=SignatureNode(
                parameters=(Parameter(name="self", type=SelfNode()),),
                returns=ConcreteNode(cls=int),
            ),
        )
        for i in range(method_count)
    )
    attr_count = draw(st.integers(0, 2))
    attributes = tuple(
        FieldDef(name=f"attr{i}", type=ConcreteNode(cls=int)) for i in range(attr_count)
    )
    return ProtocolNode(
        name=name,
        methods=methods,
        attributes=attributes,
        is_runtime_checkable=draw(st.booleans()),
    )


@composite
def function_nodes(draw: DrawFn) -> FunctionNode:
    name = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10))
    signature = SignatureNode(
        parameters=(Parameter(name="x", type=ConcreteNode(cls=int)),),
        returns=ConcreteNode(cls=str),
    )
    return FunctionNode(
        name=name,
        signature=signature,
        is_async=draw(st.booleans()),
        is_generator=draw(st.booleans()),
    )


class _SampleClass:
    pass


@composite
def class_nodes(draw: DrawFn) -> ClassNode:
    name = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10))
    type_param_count = draw(st.integers(0, 2))
    type_params: tuple[TypeVarNode | ParamSpecNode | TypeVarTupleNode, ...] = tuple(
        TypeVarNode(name=f"T{i}") for i in range(type_param_count)
    )
    base_count = draw(st.integers(0, 2))
    bases = tuple(ConcreteNode(cls=object) for _ in range(base_count))
    method_count = draw(st.integers(0, 2))
    methods = tuple(
        MethodSig(
            name=f"method{i}",
            signature=SignatureNode(
                parameters=(Parameter(name="self", type=SelfNode()),),
                returns=ConcreteNode(cls=int),
            ),
        )
        for i in range(method_count)
    )
    class_var_count = draw(st.integers(0, 2))
    class_vars = tuple(
        FieldDef(name=f"class_var{i}", type=ConcreteNode(cls=int))
        for i in range(class_var_count)
    )
    instance_var_count = draw(st.integers(0, 2))
    instance_vars = tuple(
        FieldDef(name=f"instance_var{i}", type=ConcreteNode(cls=int))
        for i in range(instance_var_count)
    )
    return ClassNode(
        cls=_SampleClass,
        name=name,
        type_params=type_params,
        bases=bases,
        methods=methods,
        class_vars=class_vars,
        instance_vars=instance_vars,
        is_abstract=draw(st.booleans()),
        is_final=draw(st.booleans()),
    )


def verify_edges_children_consistency(node: TypeNode) -> None:
    """Verify that [conn.target for conn in edges()] == list(children())."""
    edge_targets = [conn.target for conn in node.edges()]
    children_list = list(node.children())
    assert edge_targets == children_list, (
        f"edges() and children() inconsistent for {type(node).__name__}:\n"
        f"  edges targets: {edge_targets}\n"
        f"  children: {children_list}"
    )


def verify_edges_returns_sequence(node: TypeNode) -> None:
    """Verify that edges() returns a Sequence[TypeEdgeConnection]."""
    edges = node.edges()
    assert isinstance(edges, Sequence), (
        f"edges() should return Sequence, got {type(edges)}"
    )
    for conn in edges:
        assert isinstance(conn, TypeEdgeConnection), (
            f"edges() element should be TypeEdgeConnection, got {type(conn)}"
        )


def verify_children_returns_sequence(node: TypeNode) -> None:
    """Verify that children() returns a Sequence[TypeNode]."""
    children = node.children()
    assert isinstance(children, Sequence), (
        f"children() should return Sequence, got {type(children)}"
    )
    for child in children:
        assert isinstance(child, TypeNode), (
            f"children() element should be TypeNode, got {type(child)}"
        )


def verify_edges_cached_identity(node: TypeNode) -> None:
    """Verify that edges() returns the same object on repeated calls."""
    edges1 = node.edges()
    edges2 = node.edges()
    assert edges1 is edges2, (
        f"edges() should return same object for {type(node).__name__}"
    )


# Nodes that don't cache children() - they compute a new tuple each call
# These nodes return `(self.attr,)` or use conditional logic, creating new tuples
NODES_WITHOUT_CACHED_CHILDREN: tuple[type[TypeNode], ...] = (
    ParamSpecNode,
    TypeVarTupleNode,
    UnpackNode,
    TypeAliasNode,
    AnnotatedNode,
    MetaNode,
    TypeGuardNode,
    TypeIsNode,
    ForwardRefNode,
    EnumNode,
    NewTypeNode,
    FunctionNode,
)


def verify_children_cached_identity(node: TypeNode) -> None:
    """Verify that children() returns the same object on repeated calls.

    Note: Some node types don't cache children() and are excluded from this check.
    """
    # Skip caching check for nodes that compute children on each call
    if isinstance(node, NODES_WITHOUT_CACHED_CHILDREN):
        return

    children1 = node.children()
    children2 = node.children()
    assert children1 is children2, (
        f"children() should return same object for {type(node).__name__}"
    )


class TestAnyNodeProperties:
    @given(any_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: AnyNode) -> None:
        verify_edges_children_consistency(node)

    @given(any_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: AnyNode) -> None:
        verify_edges_returns_sequence(node)

    @given(any_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: AnyNode) -> None:
        verify_children_returns_sequence(node)

    @given(any_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: AnyNode) -> None:
        verify_edges_cached_identity(node)

    @given(any_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: AnyNode) -> None:
        verify_children_cached_identity(node)


class TestNeverNodeProperties:
    @given(never_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: NeverNode) -> None:
        verify_edges_children_consistency(node)

    @given(never_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: NeverNode) -> None:
        verify_edges_returns_sequence(node)

    @given(never_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: NeverNode) -> None:
        verify_children_returns_sequence(node)

    @given(never_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: NeverNode) -> None:
        verify_edges_cached_identity(node)

    @given(never_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: NeverNode) -> None:
        verify_children_cached_identity(node)


class TestSelfNodeProperties:
    @given(self_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: SelfNode) -> None:
        verify_edges_children_consistency(node)

    @given(self_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: SelfNode) -> None:
        verify_edges_returns_sequence(node)

    @given(self_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: SelfNode) -> None:
        verify_children_returns_sequence(node)

    @given(self_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: SelfNode) -> None:
        verify_edges_cached_identity(node)

    @given(self_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: SelfNode) -> None:
        verify_children_cached_identity(node)


class TestLiteralStringNodeProperties:
    @given(literal_string_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: LiteralStringNode) -> None:
        verify_edges_children_consistency(node)

    @given(literal_string_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: LiteralStringNode) -> None:
        verify_edges_returns_sequence(node)

    @given(literal_string_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: LiteralStringNode) -> None:
        verify_children_returns_sequence(node)

    @given(literal_string_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: LiteralStringNode) -> None:
        verify_edges_cached_identity(node)

    @given(literal_string_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: LiteralStringNode) -> None:
        verify_children_cached_identity(node)


class TestEllipsisNodeProperties:
    @given(ellipsis_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: EllipsisNode) -> None:
        verify_edges_children_consistency(node)

    @given(ellipsis_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: EllipsisNode) -> None:
        verify_edges_returns_sequence(node)

    @given(ellipsis_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: EllipsisNode) -> None:
        verify_children_returns_sequence(node)

    @given(ellipsis_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: EllipsisNode) -> None:
        verify_edges_cached_identity(node)

    @given(ellipsis_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: EllipsisNode) -> None:
        verify_children_cached_identity(node)


class TestLiteralNodeProperties:
    @given(literal_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: LiteralNode) -> None:
        verify_edges_children_consistency(node)

    @given(literal_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: LiteralNode) -> None:
        verify_edges_returns_sequence(node)

    @given(literal_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: LiteralNode) -> None:
        verify_children_returns_sequence(node)

    @given(literal_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: LiteralNode) -> None:
        verify_edges_cached_identity(node)

    @given(literal_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: LiteralNode) -> None:
        verify_children_cached_identity(node)


class TestConcreteNodeProperties:
    @given(concrete_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: ConcreteNode) -> None:
        verify_edges_children_consistency(node)

    @given(concrete_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: ConcreteNode) -> None:
        verify_edges_returns_sequence(node)

    @given(concrete_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: ConcreteNode) -> None:
        verify_children_returns_sequence(node)

    @given(concrete_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: ConcreteNode) -> None:
        verify_edges_cached_identity(node)

    @given(concrete_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: ConcreteNode) -> None:
        verify_children_cached_identity(node)


class TestTypeVarNodeProperties:
    @given(typevar_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: TypeVarNode) -> None:
        verify_edges_children_consistency(node)

    @given(typevar_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: TypeVarNode) -> None:
        verify_edges_returns_sequence(node)

    @given(typevar_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: TypeVarNode) -> None:
        verify_children_returns_sequence(node)

    @given(typevar_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: TypeVarNode) -> None:
        verify_edges_cached_identity(node)

    @given(typevar_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: TypeVarNode) -> None:
        verify_children_cached_identity(node)


class TestParamSpecNodeProperties:
    @given(paramspec_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: ParamSpecNode) -> None:
        verify_edges_children_consistency(node)

    @given(paramspec_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: ParamSpecNode) -> None:
        verify_edges_returns_sequence(node)

    @given(paramspec_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: ParamSpecNode) -> None:
        verify_children_returns_sequence(node)

    @given(paramspec_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: ParamSpecNode) -> None:
        verify_edges_cached_identity(node)

    @given(paramspec_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: ParamSpecNode) -> None:
        verify_children_cached_identity(node)


class TestTypeVarTupleNodeProperties:
    @given(typevartuple_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: TypeVarTupleNode) -> None:
        verify_edges_children_consistency(node)

    @given(typevartuple_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: TypeVarTupleNode) -> None:
        verify_edges_returns_sequence(node)

    @given(typevartuple_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: TypeVarTupleNode) -> None:
        verify_children_returns_sequence(node)

    @given(typevartuple_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: TypeVarTupleNode) -> None:
        verify_edges_cached_identity(node)

    @given(typevartuple_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: TypeVarTupleNode) -> None:
        verify_children_cached_identity(node)


class TestConcatenateNodeProperties:
    @given(concatenate_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: ConcatenateNode) -> None:
        verify_edges_children_consistency(node)

    @given(concatenate_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: ConcatenateNode) -> None:
        verify_edges_returns_sequence(node)

    @given(concatenate_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: ConcatenateNode) -> None:
        verify_children_returns_sequence(node)

    @given(concatenate_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: ConcatenateNode) -> None:
        verify_edges_cached_identity(node)

    @given(concatenate_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: ConcatenateNode) -> None:
        verify_children_cached_identity(node)


class TestUnpackNodeProperties:
    @given(unpack_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: UnpackNode) -> None:
        verify_edges_children_consistency(node)

    @given(unpack_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: UnpackNode) -> None:
        verify_edges_returns_sequence(node)

    @given(unpack_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: UnpackNode) -> None:
        verify_children_returns_sequence(node)

    @given(unpack_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: UnpackNode) -> None:
        verify_edges_cached_identity(node)

    @given(unpack_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: UnpackNode) -> None:
        verify_children_cached_identity(node)


class TestGenericTypeNodeProperties:
    @given(generic_type_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: GenericTypeNode) -> None:
        verify_edges_children_consistency(node)

    @given(generic_type_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: GenericTypeNode) -> None:
        verify_edges_returns_sequence(node)

    @given(generic_type_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: GenericTypeNode) -> None:
        verify_children_returns_sequence(node)

    @given(generic_type_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: GenericTypeNode) -> None:
        verify_edges_cached_identity(node)

    @given(generic_type_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: GenericTypeNode) -> None:
        verify_children_cached_identity(node)


class TestSubscriptedGenericNodeProperties:
    @given(subscripted_generic_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: SubscriptedGenericNode) -> None:
        verify_edges_children_consistency(node)

    @given(subscripted_generic_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: SubscriptedGenericNode) -> None:
        verify_edges_returns_sequence(node)

    @given(subscripted_generic_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: SubscriptedGenericNode) -> None:
        verify_children_returns_sequence(node)

    @given(subscripted_generic_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: SubscriptedGenericNode) -> None:
        verify_edges_cached_identity(node)

    @given(subscripted_generic_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: SubscriptedGenericNode) -> None:
        verify_children_cached_identity(node)


class TestGenericAliasNodeProperties:
    @given(generic_alias_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: GenericAliasNode) -> None:
        verify_edges_children_consistency(node)

    @given(generic_alias_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: GenericAliasNode) -> None:
        verify_edges_returns_sequence(node)

    @given(generic_alias_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: GenericAliasNode) -> None:
        verify_children_returns_sequence(node)

    @given(generic_alias_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: GenericAliasNode) -> None:
        verify_edges_cached_identity(node)

    @given(generic_alias_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: GenericAliasNode) -> None:
        verify_children_cached_identity(node)


class TestTypeAliasNodeProperties:
    @given(type_alias_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: TypeAliasNode) -> None:
        verify_edges_children_consistency(node)

    @given(type_alias_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: TypeAliasNode) -> None:
        verify_edges_returns_sequence(node)

    @given(type_alias_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: TypeAliasNode) -> None:
        verify_children_returns_sequence(node)

    @given(type_alias_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: TypeAliasNode) -> None:
        verify_edges_cached_identity(node)

    @given(type_alias_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: TypeAliasNode) -> None:
        verify_children_cached_identity(node)


class TestUnionNodeProperties:
    @given(union_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: UnionNode) -> None:
        verify_edges_children_consistency(node)

    @given(union_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: UnionNode) -> None:
        verify_edges_returns_sequence(node)

    @given(union_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: UnionNode) -> None:
        verify_children_returns_sequence(node)

    @given(union_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: UnionNode) -> None:
        verify_edges_cached_identity(node)

    @given(union_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: UnionNode) -> None:
        verify_children_cached_identity(node)


class TestDiscriminatedUnionNodeProperties:
    @given(discriminated_union_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: DiscriminatedUnionNode) -> None:
        verify_edges_children_consistency(node)

    @given(discriminated_union_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: DiscriminatedUnionNode) -> None:
        verify_edges_returns_sequence(node)

    @given(discriminated_union_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: DiscriminatedUnionNode) -> None:
        verify_children_returns_sequence(node)

    @given(discriminated_union_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: DiscriminatedUnionNode) -> None:
        verify_edges_cached_identity(node)

    @given(discriminated_union_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: DiscriminatedUnionNode) -> None:
        verify_children_cached_identity(node)


class TestIntersectionNodeProperties:
    @given(intersection_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: IntersectionNode) -> None:
        verify_edges_children_consistency(node)

    @given(intersection_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: IntersectionNode) -> None:
        verify_edges_returns_sequence(node)

    @given(intersection_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: IntersectionNode) -> None:
        verify_children_returns_sequence(node)

    @given(intersection_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: IntersectionNode) -> None:
        verify_edges_cached_identity(node)

    @given(intersection_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: IntersectionNode) -> None:
        verify_children_cached_identity(node)


class TestCallableNodeProperties:
    @given(callable_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: CallableNode) -> None:
        verify_edges_children_consistency(node)

    @given(callable_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: CallableNode) -> None:
        verify_edges_returns_sequence(node)

    @given(callable_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: CallableNode) -> None:
        verify_children_returns_sequence(node)

    @given(callable_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: CallableNode) -> None:
        verify_edges_cached_identity(node)

    @given(callable_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: CallableNode) -> None:
        verify_children_cached_identity(node)


class TestTupleNodeProperties:
    @given(tuple_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: TupleNode) -> None:
        verify_edges_children_consistency(node)

    @given(tuple_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: TupleNode) -> None:
        verify_edges_returns_sequence(node)

    @given(tuple_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: TupleNode) -> None:
        verify_children_returns_sequence(node)

    @given(tuple_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: TupleNode) -> None:
        verify_edges_cached_identity(node)

    @given(tuple_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: TupleNode) -> None:
        verify_children_cached_identity(node)


class TestAnnotatedNodeProperties:
    @given(annotated_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: AnnotatedNode) -> None:
        verify_edges_children_consistency(node)

    @given(annotated_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: AnnotatedNode) -> None:
        verify_edges_returns_sequence(node)

    @given(annotated_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: AnnotatedNode) -> None:
        verify_children_returns_sequence(node)

    @given(annotated_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: AnnotatedNode) -> None:
        verify_edges_cached_identity(node)

    @given(annotated_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: AnnotatedNode) -> None:
        verify_children_cached_identity(node)


class TestMetaNodeProperties:
    @given(meta_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: MetaNode) -> None:
        verify_edges_children_consistency(node)

    @given(meta_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: MetaNode) -> None:
        verify_edges_returns_sequence(node)

    @given(meta_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: MetaNode) -> None:
        verify_children_returns_sequence(node)

    @given(meta_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: MetaNode) -> None:
        verify_edges_cached_identity(node)

    @given(meta_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: MetaNode) -> None:
        verify_children_cached_identity(node)


class TestTypeGuardNodeProperties:
    @given(type_guard_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: TypeGuardNode) -> None:
        verify_edges_children_consistency(node)

    @given(type_guard_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: TypeGuardNode) -> None:
        verify_edges_returns_sequence(node)

    @given(type_guard_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: TypeGuardNode) -> None:
        verify_children_returns_sequence(node)

    @given(type_guard_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: TypeGuardNode) -> None:
        verify_edges_cached_identity(node)

    @given(type_guard_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: TypeGuardNode) -> None:
        verify_children_cached_identity(node)


class TestTypeIsNodeProperties:
    @given(type_is_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: TypeIsNode) -> None:
        verify_edges_children_consistency(node)

    @given(type_is_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: TypeIsNode) -> None:
        verify_edges_returns_sequence(node)

    @given(type_is_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: TypeIsNode) -> None:
        verify_children_returns_sequence(node)

    @given(type_is_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: TypeIsNode) -> None:
        verify_edges_cached_identity(node)

    @given(type_is_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: TypeIsNode) -> None:
        verify_children_cached_identity(node)


class TestForwardRefNodeProperties:
    @given(forward_ref_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: ForwardRefNode) -> None:
        verify_edges_children_consistency(node)

    @given(forward_ref_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: ForwardRefNode) -> None:
        verify_edges_returns_sequence(node)

    @given(forward_ref_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: ForwardRefNode) -> None:
        verify_children_returns_sequence(node)

    @given(forward_ref_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: ForwardRefNode) -> None:
        verify_edges_cached_identity(node)

    @given(forward_ref_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: ForwardRefNode) -> None:
        verify_children_cached_identity(node)


class TestTypedDictNodeProperties:
    @given(typed_dict_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: TypedDictNode) -> None:
        verify_edges_children_consistency(node)

    @given(typed_dict_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: TypedDictNode) -> None:
        verify_edges_returns_sequence(node)

    @given(typed_dict_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: TypedDictNode) -> None:
        verify_children_returns_sequence(node)

    @given(typed_dict_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: TypedDictNode) -> None:
        verify_edges_cached_identity(node)

    @given(typed_dict_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: TypedDictNode) -> None:
        verify_children_cached_identity(node)


class TestNamedTupleNodeProperties:
    @given(named_tuple_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: NamedTupleNode) -> None:
        verify_edges_children_consistency(node)

    @given(named_tuple_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: NamedTupleNode) -> None:
        verify_edges_returns_sequence(node)

    @given(named_tuple_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: NamedTupleNode) -> None:
        verify_children_returns_sequence(node)

    @given(named_tuple_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: NamedTupleNode) -> None:
        verify_edges_cached_identity(node)

    @given(named_tuple_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: NamedTupleNode) -> None:
        verify_children_cached_identity(node)


class TestDataclassNodeProperties:
    @given(dataclass_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: DataclassNode) -> None:
        verify_edges_children_consistency(node)

    @given(dataclass_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: DataclassNode) -> None:
        verify_edges_returns_sequence(node)

    @given(dataclass_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: DataclassNode) -> None:
        verify_children_returns_sequence(node)

    @given(dataclass_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: DataclassNode) -> None:
        verify_edges_cached_identity(node)

    @given(dataclass_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: DataclassNode) -> None:
        verify_children_cached_identity(node)


class TestEnumNodeProperties:
    @given(enum_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: EnumNode) -> None:
        verify_edges_children_consistency(node)

    @given(enum_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: EnumNode) -> None:
        verify_edges_returns_sequence(node)

    @given(enum_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: EnumNode) -> None:
        verify_children_returns_sequence(node)

    @given(enum_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: EnumNode) -> None:
        verify_edges_cached_identity(node)

    @given(enum_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: EnumNode) -> None:
        verify_children_cached_identity(node)


class TestNewTypeNodeProperties:
    @given(new_type_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: NewTypeNode) -> None:
        verify_edges_children_consistency(node)

    @given(new_type_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: NewTypeNode) -> None:
        verify_edges_returns_sequence(node)

    @given(new_type_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: NewTypeNode) -> None:
        verify_children_returns_sequence(node)

    @given(new_type_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: NewTypeNode) -> None:
        verify_edges_cached_identity(node)

    @given(new_type_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: NewTypeNode) -> None:
        verify_children_cached_identity(node)


class TestSignatureNodeProperties:
    @given(signature_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: SignatureNode) -> None:
        verify_edges_children_consistency(node)

    @given(signature_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: SignatureNode) -> None:
        verify_edges_returns_sequence(node)

    @given(signature_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: SignatureNode) -> None:
        verify_children_returns_sequence(node)

    @given(signature_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: SignatureNode) -> None:
        verify_edges_cached_identity(node)

    @given(signature_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: SignatureNode) -> None:
        verify_children_cached_identity(node)


class TestProtocolNodeProperties:
    @given(protocol_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: ProtocolNode) -> None:
        verify_edges_children_consistency(node)

    @given(protocol_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: ProtocolNode) -> None:
        verify_edges_returns_sequence(node)

    @given(protocol_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: ProtocolNode) -> None:
        verify_children_returns_sequence(node)

    @given(protocol_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: ProtocolNode) -> None:
        verify_edges_cached_identity(node)

    @given(protocol_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: ProtocolNode) -> None:
        verify_children_cached_identity(node)


class TestFunctionNodeProperties:
    @given(function_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: FunctionNode) -> None:
        verify_edges_children_consistency(node)

    @given(function_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: FunctionNode) -> None:
        verify_edges_returns_sequence(node)

    @given(function_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: FunctionNode) -> None:
        verify_children_returns_sequence(node)

    @given(function_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: FunctionNode) -> None:
        verify_edges_cached_identity(node)

    @given(function_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: FunctionNode) -> None:
        verify_children_cached_identity(node)


class TestClassNodeProperties:
    @given(class_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_children_consistency(self, node: ClassNode) -> None:
        verify_edges_children_consistency(node)

    @given(class_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_returns_sequence(self, node: ClassNode) -> None:
        verify_edges_returns_sequence(node)

    @given(class_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_returns_sequence(self, node: ClassNode) -> None:
        verify_children_returns_sequence(node)

    @given(class_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_edges_cached_identity(self, node: ClassNode) -> None:
        verify_edges_cached_identity(node)

    @given(class_nodes())
    @settings(deadline=None, suppress_health_check=[HealthCheck.too_slow])
    def test_children_cached_identity(self, node: ClassNode) -> None:
        verify_children_cached_identity(node)
