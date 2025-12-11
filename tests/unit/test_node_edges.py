from enum import IntEnum

from typing_graph._node import (
    AnnotatedNode,
    AnyNode,
    CallableNode,
    ClassNode,
    ConcatenateNode,
    ConcreteNode,
    DataclassFieldDef,
    DataclassNode,
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
    TypeEdge,
    TypeEdgeConnection,
    TypeEdgeKind,
    TypeGuardNode,
    TypeIsNode,
    TypeVarNode,
    TypeVarTupleNode,
    UnionNode,
    UnpackNode,
)


class TestAnyNodeEdges:
    def test_edges_returns_empty_sequence(self):
        node = AnyNode()
        assert node.edges() == ()

    def test_edges_matches_children(self):
        node = AnyNode()
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self):
        node = AnyNode()
        assert node.edges() is node.edges()


class TestNeverNodeEdges:
    def test_edges_returns_empty_sequence(self):
        node = NeverNode()
        assert node.edges() == ()

    def test_edges_matches_children(self):
        node = NeverNode()
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self):
        node = NeverNode()
        assert node.edges() is node.edges()


class TestSelfNodeEdges:
    def test_edges_returns_empty_sequence(self):
        node = SelfNode()
        assert node.edges() == ()

    def test_edges_matches_children(self):
        node = SelfNode()
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self):
        node = SelfNode()
        assert node.edges() is node.edges()


class TestLiteralStringNodeEdges:
    def test_edges_returns_empty_sequence(self):
        node = LiteralStringNode()
        assert node.edges() == ()

    def test_edges_matches_children(self):
        node = LiteralStringNode()
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self):
        node = LiteralStringNode()
        assert node.edges() is node.edges()


class TestEllipsisNodeEdges:
    def test_edges_returns_empty_sequence(self):
        node = EllipsisNode()
        assert node.edges() == ()

    def test_edges_matches_children(self):
        node = EllipsisNode()
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self):
        node = EllipsisNode()
        assert node.edges() is node.edges()


class TestLiteralNodeEdges:
    def test_edges_returns_empty_sequence(self):
        node = LiteralNode(values=(1, 2, "hello"))
        assert node.edges() == ()

    def test_edges_matches_children(self):
        node = LiteralNode(values=(True, False))
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self):
        node = LiteralNode(values=("a", "b"))
        assert node.edges() is node.edges()


class TestConcreteNodeEdges:
    def test_edges_returns_empty_sequence(self, int_node: ConcreteNode):
        assert int_node.edges() == ()

    def test_edges_matches_children(self, str_node: ConcreteNode):
        assert [c.target for c in str_node.edges()] == list(str_node.children())

    def test_edges_cached(self, float_node: ConcreteNode):
        assert float_node.edges() is float_node.edges()


class TestTypeVarNodeEdges:
    def test_edges_with_bound_only(self, int_node: ConcreteNode):
        node = TypeVarNode(name="T", bound=int_node)
        edges = node.edges()
        assert len(edges) == 1
        assert edges[0].edge.kind == TypeEdgeKind.BOUND
        assert edges[0].target is int_node

    def test_edges_with_constraints(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        node = TypeVarNode(name="T", constraints=(int_node, str_node))
        edges = node.edges()
        assert len(edges) == 2
        assert edges[0].edge.kind == TypeEdgeKind.CONSTRAINT
        assert edges[0].edge.index == 0
        assert edges[0].target is int_node
        assert edges[1].edge.kind == TypeEdgeKind.CONSTRAINT
        assert edges[1].edge.index == 1
        assert edges[1].target is str_node

    def test_edges_with_default(self, int_node: ConcreteNode, str_node: ConcreteNode):
        node = TypeVarNode(name="T", bound=int_node, default=str_node)
        edges = node.edges()
        assert len(edges) == 2
        assert edges[0].edge.kind == TypeEdgeKind.BOUND
        assert edges[0].target is int_node
        assert edges[1].edge.kind == TypeEdgeKind.DEFAULT
        assert edges[1].target is str_node

    def test_edges_no_bound_no_constraints(self):
        node = TypeVarNode(name="T")
        assert node.edges() == ()

    def test_edges_matches_children(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        node = TypeVarNode(name="T", constraints=(int_node, str_node))
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self, int_node: ConcreteNode):
        node = TypeVarNode(name="T", bound=int_node)
        assert node.edges() is node.edges()

    def test_edges_with_constraints_bound_and_default(
        self, int_node: ConcreteNode, str_node: ConcreteNode, float_node: ConcreteNode
    ):
        node = TypeVarNode(
            name="T", constraints=(int_node, str_node), default=float_node
        )
        edges = node.edges()
        assert len(edges) == 3
        constraint_edges = [e for e in edges if e.edge.kind == TypeEdgeKind.CONSTRAINT]
        default_edges = [e for e in edges if e.edge.kind == TypeEdgeKind.DEFAULT]
        assert len(constraint_edges) == 2
        assert len(default_edges) == 1
        assert default_edges[0].target is float_node


class TestParamSpecNodeEdges:
    def test_edges_without_default(self):
        node = ParamSpecNode(name="P")
        assert node.edges() == ()

    def test_edges_with_default(self, int_node: ConcreteNode):
        node = ParamSpecNode(name="P", default=int_node)
        edges = node.edges()
        assert len(edges) == 1
        assert edges[0].edge.kind == TypeEdgeKind.DEFAULT
        assert edges[0].target is int_node

    def test_edges_matches_children(self, str_node: ConcreteNode):
        node = ParamSpecNode(name="P", default=str_node)
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self, int_node: ConcreteNode):
        node = ParamSpecNode(name="P", default=int_node)
        assert node.edges() is node.edges()


class TestTypeVarTupleNodeEdges:
    def test_edges_without_default(self):
        node = TypeVarTupleNode(name="Ts")
        assert node.edges() == ()

    def test_edges_with_default(self, int_node: ConcreteNode):
        default_tuple = TupleNode(elements=(int_node,))
        node = TypeVarTupleNode(name="Ts", default=default_tuple)
        edges = node.edges()
        assert len(edges) == 1
        assert edges[0].edge.kind == TypeEdgeKind.DEFAULT
        assert edges[0].target is default_tuple

    def test_edges_matches_children(self, str_node: ConcreteNode):
        default_tuple = TupleNode(elements=(str_node,))
        node = TypeVarTupleNode(name="Ts", default=default_tuple)
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self, int_node: ConcreteNode):
        default_tuple = TupleNode(elements=(int_node,))
        node = TypeVarTupleNode(name="Ts", default=default_tuple)
        assert node.edges() is node.edges()


class TestGenericTypeNodeEdges:
    def test_edges_without_type_params(self):
        node = GenericTypeNode(cls=list)
        assert node.edges() == ()

    def test_edges_with_type_params(self, typevar_t: TypeVarNode):
        typevar_u = TypeVarNode(name="U")
        node = GenericTypeNode(cls=dict, type_params=(typevar_t, typevar_u))
        edges = node.edges()
        assert len(edges) == 2
        assert edges[0].edge.kind == TypeEdgeKind.TYPE_PARAM
        assert edges[0].edge.index == 0
        assert edges[0].target is typevar_t
        assert edges[1].edge.kind == TypeEdgeKind.TYPE_PARAM
        assert edges[1].edge.index == 1
        assert edges[1].target is typevar_u

    def test_edges_matches_children(self, typevar_t: TypeVarNode):
        node = GenericTypeNode(cls=list, type_params=(typevar_t,))
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self, typevar_t: TypeVarNode):
        node = GenericTypeNode(cls=list, type_params=(typevar_t,))
        assert node.edges() is node.edges()


class TestSubscriptedGenericNodeEdges:
    def test_edges_returns_origin_and_type_args(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        origin = GenericTypeNode(cls=dict)
        node = SubscriptedGenericNode(origin=origin, args=(int_node, str_node))
        edges = node.edges()
        assert len(edges) == 3
        assert edges[0].edge.kind == TypeEdgeKind.ORIGIN
        assert edges[0].target is origin
        assert edges[1].edge.kind == TypeEdgeKind.TYPE_ARG
        assert edges[1].edge.index == 0
        assert edges[1].target is int_node
        assert edges[2].edge.kind == TypeEdgeKind.TYPE_ARG
        assert edges[2].edge.index == 1
        assert edges[2].target is str_node

    def test_edges_with_single_type_arg(self, int_node: ConcreteNode):
        origin = GenericTypeNode(cls=list)
        node = SubscriptedGenericNode(origin=origin, args=(int_node,))
        edges = node.edges()
        assert len(edges) == 2
        assert edges[0].edge.kind == TypeEdgeKind.ORIGIN
        assert edges[1].edge.kind == TypeEdgeKind.TYPE_ARG
        assert edges[1].edge.index == 0

    def test_edges_matches_children(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        origin = GenericTypeNode(cls=dict)
        node = SubscriptedGenericNode(origin=origin, args=(int_node, str_node))
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self, int_node: ConcreteNode):
        origin = GenericTypeNode(cls=list)
        node = SubscriptedGenericNode(origin=origin, args=(int_node,))
        assert node.edges() is node.edges()


class TestTypeAliasNodeEdges:
    def test_edges_returns_alias_target(self, int_node: ConcreteNode):
        node = TypeAliasNode(name="IntAlias", value=int_node)
        edges = node.edges()
        assert len(edges) == 1
        assert edges[0].edge.kind == TypeEdgeKind.ALIAS_TARGET
        assert edges[0].target is int_node

    def test_edges_matches_children(self, str_node: ConcreteNode):
        node = TypeAliasNode(name="StrAlias", value=str_node)
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self, int_node: ConcreteNode):
        node = TypeAliasNode(name="Alias", value=int_node)
        assert node.edges() is node.edges()


class TestGenericAliasNodeEdges:
    def test_edges_returns_type_params_and_alias_target(
        self, typevar_t: TypeVarNode, int_node: ConcreteNode
    ):
        typevar_u = TypeVarNode(name="U")
        node = GenericAliasNode(
            name="MyAlias", type_params=(typevar_t, typevar_u), value=int_node
        )
        edges = node.edges()
        assert len(edges) == 3
        assert edges[0].edge.kind == TypeEdgeKind.TYPE_PARAM
        assert edges[0].edge.index == 0
        assert edges[0].target is typevar_t
        assert edges[1].edge.kind == TypeEdgeKind.TYPE_PARAM
        assert edges[1].edge.index == 1
        assert edges[1].target is typevar_u
        assert edges[2].edge.kind == TypeEdgeKind.ALIAS_TARGET
        assert edges[2].target is int_node

    def test_edges_with_single_type_param(
        self, typevar_t: TypeVarNode, str_node: ConcreteNode
    ):
        node = GenericAliasNode(name="Vector", type_params=(typevar_t,), value=str_node)
        edges = node.edges()
        assert len(edges) == 2
        assert edges[0].edge.kind == TypeEdgeKind.TYPE_PARAM
        assert edges[1].edge.kind == TypeEdgeKind.ALIAS_TARGET

    def test_edges_matches_children(
        self, typevar_t: TypeVarNode, int_node: ConcreteNode
    ):
        node = GenericAliasNode(name="Alias", type_params=(typevar_t,), value=int_node)
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self, typevar_t: TypeVarNode, int_node: ConcreteNode):
        node = GenericAliasNode(name="Alias", type_params=(typevar_t,), value=int_node)
        assert node.edges() is node.edges()


class TestUnionNodeEdges:
    def test_edges_returns_union_members(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        node = UnionNode(members=(int_node, str_node))
        edges = node.edges()
        assert len(edges) == 2
        assert edges[0].edge.kind == TypeEdgeKind.UNION_MEMBER
        assert edges[0].edge.index == 0
        assert edges[0].target is int_node
        assert edges[1].edge.kind == TypeEdgeKind.UNION_MEMBER
        assert edges[1].edge.index == 1
        assert edges[1].target is str_node

    def test_edges_with_three_members(
        self, int_node: ConcreteNode, str_node: ConcreteNode, float_node: ConcreteNode
    ):
        node = UnionNode(members=(int_node, str_node, float_node))
        edges = node.edges()
        assert len(edges) == 3
        for i, edge in enumerate(edges):
            assert edge.edge.kind == TypeEdgeKind.UNION_MEMBER
            assert edge.edge.index == i

    def test_edges_matches_children(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        node = UnionNode(members=(int_node, str_node))
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self, int_node: ConcreteNode, str_node: ConcreteNode):
        node = UnionNode(members=(int_node, str_node))
        assert node.edges() is node.edges()


class TestIntersectionNodeEdges:
    def test_edges_returns_intersection_members(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        node = IntersectionNode(members=(int_node, str_node))
        edges = node.edges()
        assert len(edges) == 2
        assert edges[0].edge.kind == TypeEdgeKind.INTERSECTION_MEMBER
        assert edges[0].edge.index == 0
        assert edges[0].target is int_node
        assert edges[1].edge.kind == TypeEdgeKind.INTERSECTION_MEMBER
        assert edges[1].edge.index == 1
        assert edges[1].target is str_node

    def test_edges_matches_children(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        node = IntersectionNode(members=(int_node, str_node))
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self, int_node: ConcreteNode, str_node: ConcreteNode):
        node = IntersectionNode(members=(int_node, str_node))
        assert node.edges() is node.edges()


class TestTupleNodeEdges:
    def test_edges_returns_element_edges(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        node = TupleNode(elements=(int_node, str_node))
        edges = node.edges()
        assert len(edges) == 2
        assert edges[0].edge.kind == TypeEdgeKind.ELEMENT
        assert edges[0].edge.index == 0
        assert edges[0].target is int_node
        assert edges[1].edge.kind == TypeEdgeKind.ELEMENT
        assert edges[1].edge.index == 1
        assert edges[1].target is str_node

    def test_edges_empty_tuple(self):
        node = TupleNode(elements=())
        assert node.edges() == ()

    def test_edges_homogeneous_tuple(self, int_node: ConcreteNode):
        node = TupleNode(elements=(int_node,), homogeneous=True)
        edges = node.edges()
        assert len(edges) == 1
        assert edges[0].edge.kind == TypeEdgeKind.ELEMENT
        assert edges[0].edge.index == 0

    def test_edges_matches_children(
        self, int_node: ConcreteNode, str_node: ConcreteNode, float_node: ConcreteNode
    ):
        node = TupleNode(elements=(int_node, str_node, float_node))
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self, int_node: ConcreteNode):
        node = TupleNode(elements=(int_node,))
        assert node.edges() is node.edges()


class TestAnnotatedNodeEdges:
    def test_edges_returns_annotated_base(self, int_node: ConcreteNode):
        node = AnnotatedNode(base=int_node, annotations=("some_metadata",))
        edges = node.edges()
        assert len(edges) == 1
        assert edges[0].edge.kind == TypeEdgeKind.ANNOTATED_BASE
        assert edges[0].target is int_node

    def test_edges_matches_children(self, str_node: ConcreteNode):
        node = AnnotatedNode(base=str_node, annotations=(42,))
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self, int_node: ConcreteNode):
        node = AnnotatedNode(base=int_node)
        assert node.edges() is node.edges()


class TestCallableNodeEdges:
    def test_edges_with_tuple_params(
        self, int_node: ConcreteNode, str_node: ConcreteNode, float_node: ConcreteNode
    ):
        node = CallableNode(params=(int_node, str_node), returns=float_node)
        edges = node.edges()
        assert len(edges) == 3
        assert edges[0].edge.kind == TypeEdgeKind.PARAM
        assert edges[0].edge.index == 0
        assert edges[0].target is int_node
        assert edges[1].edge.kind == TypeEdgeKind.PARAM
        assert edges[1].edge.index == 1
        assert edges[1].target is str_node
        assert edges[2].edge.kind == TypeEdgeKind.RETURN
        assert edges[2].target is float_node

    def test_edges_with_paramspec(
        self, paramspec_p: ParamSpecNode, int_node: ConcreteNode
    ):
        node = CallableNode(params=paramspec_p, returns=int_node)
        edges = node.edges()
        assert len(edges) == 2
        assert edges[0].edge.kind == TypeEdgeKind.PARAM
        assert edges[0].edge.index is None
        assert edges[0].target is paramspec_p
        assert edges[1].edge.kind == TypeEdgeKind.RETURN
        assert edges[1].target is int_node

    def test_edges_with_ellipsis(self, int_node: ConcreteNode):
        ellipsis_node = EllipsisNode()
        node = CallableNode(params=ellipsis_node, returns=int_node)
        edges = node.edges()
        assert len(edges) == 2
        assert edges[0].edge.kind == TypeEdgeKind.PARAM
        assert edges[0].edge.index is None
        assert edges[0].target is ellipsis_node
        assert edges[1].edge.kind == TypeEdgeKind.RETURN

    def test_edges_with_concatenate(
        self, paramspec_p: ParamSpecNode, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        concat = ConcatenateNode(prefix=(int_node,), param_spec=paramspec_p)
        node = CallableNode(params=concat, returns=str_node)
        edges = node.edges()
        assert len(edges) == 2
        assert edges[0].edge.kind == TypeEdgeKind.PARAM
        assert edges[0].edge.index is None
        assert edges[0].target is concat
        assert edges[1].edge.kind == TypeEdgeKind.RETURN

    def test_edges_with_empty_params(self, int_node: ConcreteNode):
        node = CallableNode(params=(), returns=int_node)
        edges = node.edges()
        assert len(edges) == 1
        assert edges[0].edge.kind == TypeEdgeKind.RETURN

    def test_edges_matches_children(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        node = CallableNode(params=(int_node,), returns=str_node)
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self, int_node: ConcreteNode, str_node: ConcreteNode):
        node = CallableNode(params=(int_node,), returns=str_node)
        assert node.edges() is node.edges()


class TestConcatenateNodeEdges:
    def test_edges_returns_prefix_and_paramspec(
        self,
        int_node: ConcreteNode,
        str_node: ConcreteNode,
        paramspec_p: ParamSpecNode,
    ):
        node = ConcatenateNode(prefix=(int_node, str_node), param_spec=paramspec_p)
        edges = node.edges()
        assert len(edges) == 3
        assert edges[0].edge.kind == TypeEdgeKind.PREFIX
        assert edges[0].edge.index == 0
        assert edges[0].target is int_node
        assert edges[1].edge.kind == TypeEdgeKind.PREFIX
        assert edges[1].edge.index == 1
        assert edges[1].target is str_node
        assert edges[2].edge.kind == TypeEdgeKind.PARAM_SPEC
        assert edges[2].target is paramspec_p

    def test_edges_with_single_prefix(
        self, int_node: ConcreteNode, paramspec_p: ParamSpecNode
    ):
        node = ConcatenateNode(prefix=(int_node,), param_spec=paramspec_p)
        edges = node.edges()
        assert len(edges) == 2
        assert edges[0].edge.kind == TypeEdgeKind.PREFIX
        assert edges[0].edge.index == 0
        assert edges[1].edge.kind == TypeEdgeKind.PARAM_SPEC

    def test_edges_with_empty_prefix(self, paramspec_p: ParamSpecNode):
        node = ConcatenateNode(prefix=(), param_spec=paramspec_p)
        edges = node.edges()
        assert len(edges) == 1
        assert edges[0].edge.kind == TypeEdgeKind.PARAM_SPEC
        assert edges[0].target is paramspec_p

    def test_edges_matches_children(
        self, int_node: ConcreteNode, paramspec_p: ParamSpecNode
    ):
        node = ConcatenateNode(prefix=(int_node,), param_spec=paramspec_p)
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self, int_node: ConcreteNode, paramspec_p: ParamSpecNode):
        node = ConcatenateNode(prefix=(int_node,), param_spec=paramspec_p)
        assert node.edges() is node.edges()


class TestUnpackNodeEdges:
    def test_edges_returns_target(self, typevartuple_ts: TypeVarTupleNode):
        node = UnpackNode(target=typevartuple_ts)
        edges = node.edges()
        assert len(edges) == 1
        assert edges[0].edge.kind == TypeEdgeKind.TARGET
        assert edges[0].target is typevartuple_ts

    def test_edges_with_tuple_target(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        tuple_node = TupleNode(elements=(int_node, str_node))
        node = UnpackNode(target=tuple_node)
        edges = node.edges()
        assert len(edges) == 1
        assert edges[0].edge.kind == TypeEdgeKind.TARGET
        assert edges[0].target is tuple_node

    def test_edges_matches_children(self, typevartuple_ts: TypeVarTupleNode):
        node = UnpackNode(target=typevartuple_ts)
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self, typevartuple_ts: TypeVarTupleNode):
        node = UnpackNode(target=typevartuple_ts)
        assert node.edges() is node.edges()


class TestSignatureNodeEdges:
    def test_edges_returns_params_return_and_type_params(
        self,
        int_node: ConcreteNode,
        str_node: ConcreteNode,
        typevar_t: TypeVarNode,
    ):
        params = (
            Parameter(name="x", type=int_node),
            Parameter(name="y", type=str_node),
        )
        node = SignatureNode(
            parameters=params, returns=int_node, type_params=(typevar_t,)
        )
        edges = node.edges()
        assert len(edges) == 4
        assert edges[0].edge.kind == TypeEdgeKind.PARAM
        assert edges[0].edge.name == "x"
        assert edges[0].target is int_node
        assert edges[1].edge.kind == TypeEdgeKind.PARAM
        assert edges[1].edge.name == "y"
        assert edges[1].target is str_node
        assert edges[2].edge.kind == TypeEdgeKind.RETURN
        assert edges[2].target is int_node
        assert edges[3].edge.kind == TypeEdgeKind.TYPE_PARAM
        assert edges[3].edge.index == 0
        assert edges[3].target is typevar_t

    def test_edges_without_type_params(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        params = (Parameter(name="arg", type=int_node),)
        node = SignatureNode(parameters=params, returns=str_node)
        edges = node.edges()
        assert len(edges) == 2
        assert edges[0].edge.kind == TypeEdgeKind.PARAM
        assert edges[0].edge.name == "arg"
        assert edges[1].edge.kind == TypeEdgeKind.RETURN

    def test_edges_without_params(self, int_node: ConcreteNode):
        node = SignatureNode(parameters=(), returns=int_node)
        edges = node.edges()
        assert len(edges) == 1
        assert edges[0].edge.kind == TypeEdgeKind.RETURN

    def test_edges_matches_children(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        params = (Parameter(name="x", type=int_node),)
        node = SignatureNode(parameters=params, returns=str_node)
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self, int_node: ConcreteNode):
        node = SignatureNode(parameters=(), returns=int_node)
        assert node.edges() is node.edges()


class TestFunctionNodeEdges:
    def test_edges_returns_signature(self, int_node: ConcreteNode):
        sig = SignatureNode(parameters=(), returns=int_node)
        node = FunctionNode(name="my_func", signature=sig)
        edges = node.edges()
        assert len(edges) == 1
        assert edges[0].edge.kind == TypeEdgeKind.SIGNATURE
        assert edges[0].target is sig

    def test_edges_matches_children(self, str_node: ConcreteNode):
        sig = SignatureNode(parameters=(), returns=str_node)
        node = FunctionNode(name="f", signature=sig)
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self, int_node: ConcreteNode):
        sig = SignatureNode(parameters=(), returns=int_node)
        node = FunctionNode(name="f", signature=sig)
        assert node.edges() is node.edges()


class TestTypeGuardNodeEdges:
    def test_edges_returns_narrows(self, int_node: ConcreteNode):
        node = TypeGuardNode(narrows_to=int_node)
        edges = node.edges()
        assert len(edges) == 1
        assert edges[0].edge.kind == TypeEdgeKind.NARROWS
        assert edges[0].target is int_node

    def test_edges_matches_children(self, str_node: ConcreteNode):
        node = TypeGuardNode(narrows_to=str_node)
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self, int_node: ConcreteNode):
        node = TypeGuardNode(narrows_to=int_node)
        assert node.edges() is node.edges()


class TestTypeIsNodeEdges:
    def test_edges_returns_narrows(self, int_node: ConcreteNode):
        node = TypeIsNode(narrows_to=int_node)
        edges = node.edges()
        assert len(edges) == 1
        assert edges[0].edge.kind == TypeEdgeKind.NARROWS
        assert edges[0].target is int_node

    def test_edges_matches_children(self, str_node: ConcreteNode):
        node = TypeIsNode(narrows_to=str_node)
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self, int_node: ConcreteNode):
        node = TypeIsNode(narrows_to=int_node)
        assert node.edges() is node.edges()


class TestMetaNodeEdges:
    def test_edges_returns_meta_of(self, int_node: ConcreteNode):
        node = MetaNode(of=int_node)
        edges = node.edges()
        assert len(edges) == 1
        assert edges[0].edge.kind == TypeEdgeKind.META_OF
        assert edges[0].target is int_node

    def test_edges_matches_children(self, str_node: ConcreteNode):
        node = MetaNode(of=str_node)
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self, int_node: ConcreteNode):
        node = MetaNode(of=int_node)
        assert node.edges() is node.edges()


class TestNewTypeNodeEdges:
    def test_edges_returns_supertype(self, int_node: ConcreteNode):
        node = NewTypeNode(name="UserId", supertype=int_node)
        edges = node.edges()
        assert len(edges) == 1
        assert edges[0].edge.kind == TypeEdgeKind.SUPERTYPE
        assert edges[0].target is int_node

    def test_edges_matches_children(self, str_node: ConcreteNode):
        node = NewTypeNode(name="Name", supertype=str_node)
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self, int_node: ConcreteNode):
        node = NewTypeNode(name="Id", supertype=int_node)
        assert node.edges() is node.edges()


class TestForwardRefNodeEdges:
    def test_edges_unresolved_returns_empty(self):
        node = ForwardRefNode(ref="MyClass", state=RefUnresolved())
        assert node.edges() == ()

    def test_edges_failed_returns_empty(self):
        node = ForwardRefNode(ref="Missing", state=RefFailed(error="Not found"))
        assert node.edges() == ()

    def test_edges_resolved_returns_resolved_edge(self, int_node: ConcreteNode):
        node = ForwardRefNode(ref="int", state=RefResolved(node=int_node))
        edges = node.edges()
        assert len(edges) == 1
        assert edges[0].edge.kind == TypeEdgeKind.RESOLVED
        assert edges[0].target is int_node

    def test_edges_matches_children_unresolved(self):
        node = ForwardRefNode(ref="Unresolved")
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_matches_children_resolved(self, str_node: ConcreteNode):
        node = ForwardRefNode(ref="str", state=RefResolved(node=str_node))
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self, int_node: ConcreteNode):
        node = ForwardRefNode(ref="int", state=RefResolved(node=int_node))
        assert node.edges() is node.edges()


class TestTypedDictNodeEdges:
    def test_edges_returns_field_edges(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        fields = (
            FieldDef(name="id", type=int_node),
            FieldDef(name="name", type=str_node),
        )
        node = TypedDictNode(name="Person", fields=fields)
        edges = node.edges()
        assert len(edges) == 2
        assert edges[0].edge.kind == TypeEdgeKind.FIELD
        assert edges[0].edge.name == "id"
        assert edges[0].target is int_node
        assert edges[1].edge.kind == TypeEdgeKind.FIELD
        assert edges[1].edge.name == "name"
        assert edges[1].target is str_node

    def test_edges_empty_fields(self):
        node = TypedDictNode(name="Empty", fields=())
        assert node.edges() == ()

    def test_edges_matches_children(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        fields = (FieldDef(name="x", type=int_node), FieldDef(name="y", type=str_node))
        node = TypedDictNode(name="Point", fields=fields)
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self, int_node: ConcreteNode):
        fields = (FieldDef(name="value", type=int_node),)
        node = TypedDictNode(name="TD", fields=fields)
        assert node.edges() is node.edges()


class TestNamedTupleNodeEdges:
    def test_edges_returns_field_edges(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        fields = (
            FieldDef(name="x", type=int_node),
            FieldDef(name="y", type=str_node),
        )
        node = NamedTupleNode(name="Point", fields=fields)
        edges = node.edges()
        assert len(edges) == 2
        assert edges[0].edge.kind == TypeEdgeKind.FIELD
        assert edges[0].edge.name == "x"
        assert edges[0].target is int_node
        assert edges[1].edge.kind == TypeEdgeKind.FIELD
        assert edges[1].edge.name == "y"
        assert edges[1].target is str_node

    def test_edges_empty_fields(self):
        node = NamedTupleNode(name="Empty", fields=())
        assert node.edges() == ()

    def test_edges_matches_children(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        fields = (FieldDef(name="a", type=int_node), FieldDef(name="b", type=str_node))
        node = NamedTupleNode(name="NT", fields=fields)
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self, int_node: ConcreteNode):
        fields = (FieldDef(name="val", type=int_node),)
        node = NamedTupleNode(name="NT", fields=fields)
        assert node.edges() is node.edges()


class TestDataclassNodeEdges:
    def test_edges_returns_field_edges(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        class MyDataclass:
            pass

        fields = (
            DataclassFieldDef(name="id", type=int_node),
            DataclassFieldDef(name="name", type=str_node),
        )
        node = DataclassNode(cls=MyDataclass, fields=fields)
        edges = node.edges()
        assert len(edges) == 2
        assert edges[0].edge.kind == TypeEdgeKind.FIELD
        assert edges[0].edge.name == "id"
        assert edges[0].target is int_node
        assert edges[1].edge.kind == TypeEdgeKind.FIELD
        assert edges[1].edge.name == "name"
        assert edges[1].target is str_node

    def test_edges_empty_fields(self):
        class EmptyDC:
            pass

        node = DataclassNode(cls=EmptyDC, fields=())
        assert node.edges() == ()

    def test_edges_matches_children(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        class DC:
            pass

        fields = (
            DataclassFieldDef(name="x", type=int_node),
            DataclassFieldDef(name="y", type=str_node),
        )
        node = DataclassNode(cls=DC, fields=fields)
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self, int_node: ConcreteNode):
        class DC:
            pass

        fields = (DataclassFieldDef(name="val", type=int_node),)
        node = DataclassNode(cls=DC, fields=fields)
        assert node.edges() is node.edges()


class TestEnumNodeEdges:
    def test_edges_returns_value_type(self, int_node: ConcreteNode):
        class Status(IntEnum):
            ACTIVE = 1
            INACTIVE = 0

        node = EnumNode(
            cls=Status,
            value_type=int_node,
            members=(("ACTIVE", 1), ("INACTIVE", 0)),
        )
        edges = node.edges()
        assert len(edges) == 1
        assert edges[0].edge.kind == TypeEdgeKind.VALUE_TYPE
        assert edges[0].target is int_node

    def test_edges_matches_children(self, str_node: ConcreteNode):
        class StrEnum:
            pass

        node = EnumNode(cls=StrEnum, value_type=str_node, members=(("A", "a"),))
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self, int_node: ConcreteNode):
        class E:
            pass

        node = EnumNode(cls=E, value_type=int_node, members=())
        assert node.edges() is node.edges()


class TestProtocolNodeEdges:
    def test_edges_returns_methods_and_fields(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        sig = SignatureNode(parameters=(), returns=int_node)
        methods = (MethodSig(name="get_id", signature=sig),)
        attributes = (FieldDef(name="name", type=str_node),)
        node = ProtocolNode(name="Identifiable", methods=methods, attributes=attributes)
        edges = node.edges()
        assert len(edges) == 2
        assert edges[0].edge.kind == TypeEdgeKind.METHOD
        assert edges[0].edge.name == "get_id"
        assert edges[0].target is sig
        assert edges[1].edge.kind == TypeEdgeKind.FIELD
        assert edges[1].edge.name == "name"
        assert edges[1].target is str_node

    def test_edges_methods_only(self, int_node: ConcreteNode):
        sig = SignatureNode(parameters=(), returns=int_node)
        methods = (MethodSig(name="method", signature=sig),)
        node = ProtocolNode(name="Proto", methods=methods)
        edges = node.edges()
        assert len(edges) == 1
        assert edges[0].edge.kind == TypeEdgeKind.METHOD
        assert edges[0].edge.name == "method"

    def test_edges_attributes_only(self, str_node: ConcreteNode):
        attributes = (FieldDef(name="attr", type=str_node),)
        node = ProtocolNode(name="Proto", methods=(), attributes=attributes)
        edges = node.edges()
        assert len(edges) == 1
        assert edges[0].edge.kind == TypeEdgeKind.FIELD
        assert edges[0].edge.name == "attr"

    def test_edges_empty_protocol(self):
        node = ProtocolNode(name="EmptyProto", methods=())
        assert node.edges() == ()

    def test_edges_matches_children(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        sig = SignatureNode(parameters=(), returns=int_node)
        methods = (MethodSig(name="m", signature=sig),)
        attributes = (FieldDef(name="a", type=str_node),)
        node = ProtocolNode(name="P", methods=methods, attributes=attributes)
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self, int_node: ConcreteNode):
        sig = SignatureNode(parameters=(), returns=int_node)
        methods = (MethodSig(name="m", signature=sig),)
        node = ProtocolNode(name="P", methods=methods)
        assert node.edges() is node.edges()


class TestClassNodeEdges:
    def test_edges_returns_type_params_bases_methods_and_fields(
        self,
        typevar_t: TypeVarNode,
        int_node: ConcreteNode,
        str_node: ConcreteNode,
        float_node: ConcreteNode,
    ):
        class MyClass:
            pass

        sig = SignatureNode(parameters=(), returns=int_node)
        methods = (MethodSig(name="process", signature=sig),)
        class_vars = (FieldDef(name="class_attr", type=str_node),)
        instance_vars = (FieldDef(name="instance_attr", type=float_node),)
        base_node = ConcreteNode(cls=object)

        node = ClassNode(
            cls=MyClass,
            name="MyClass",
            type_params=(typevar_t,),
            bases=(base_node,),
            methods=methods,
            class_vars=class_vars,
            instance_vars=instance_vars,
        )
        edges = node.edges()
        assert len(edges) == 5

        assert edges[0].edge.kind == TypeEdgeKind.TYPE_PARAM
        assert edges[0].edge.index == 0
        assert edges[0].target is typevar_t

        assert edges[1].edge.kind == TypeEdgeKind.BASE
        assert edges[1].edge.index == 0
        assert edges[1].target is base_node

        assert edges[2].edge.kind == TypeEdgeKind.METHOD
        assert edges[2].edge.name == "process"
        assert edges[2].target is sig

        assert edges[3].edge.kind == TypeEdgeKind.FIELD
        assert edges[3].edge.name == "class_attr"
        assert edges[3].target is str_node

        assert edges[4].edge.kind == TypeEdgeKind.FIELD
        assert edges[4].edge.name == "instance_attr"
        assert edges[4].target is float_node

    def test_edges_minimal_class(self):
        class MinimalClass:
            pass

        node = ClassNode(cls=MinimalClass, name="MinimalClass")
        assert node.edges() == ()

    def test_edges_with_multiple_bases(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        class MultiBaseClass:
            pass

        node = ClassNode(
            cls=MultiBaseClass,
            name="MultiBaseClass",
            bases=(int_node, str_node),
        )
        edges = node.edges()
        assert len(edges) == 2
        assert edges[0].edge.kind == TypeEdgeKind.BASE
        assert edges[0].edge.index == 0
        assert edges[1].edge.kind == TypeEdgeKind.BASE
        assert edges[1].edge.index == 1

    def test_edges_with_multiple_type_params(
        self, typevar_t: TypeVarNode, paramspec_p: ParamSpecNode
    ):
        class GenericClass:
            pass

        node = ClassNode(
            cls=GenericClass,
            name="GenericClass",
            type_params=(typevar_t, paramspec_p),
        )
        edges = node.edges()
        assert len(edges) == 2
        assert edges[0].edge.kind == TypeEdgeKind.TYPE_PARAM
        assert edges[0].edge.index == 0
        assert edges[0].target is typevar_t
        assert edges[1].edge.kind == TypeEdgeKind.TYPE_PARAM
        assert edges[1].edge.index == 1
        assert edges[1].target is paramspec_p

    def test_edges_matches_children(
        self,
        typevar_t: TypeVarNode,
        int_node: ConcreteNode,
        str_node: ConcreteNode,
    ):
        class Cls:
            pass

        sig = SignatureNode(parameters=(), returns=int_node)
        methods = (MethodSig(name="m", signature=sig),)
        instance_vars = (FieldDef(name="v", type=str_node),)
        node = ClassNode(
            cls=Cls,
            name="Cls",
            type_params=(typevar_t,),
            bases=(int_node,),
            methods=methods,
            instance_vars=instance_vars,
        )
        assert [c.target for c in node.edges()] == list(node.children())

    def test_edges_cached(self, int_node: ConcreteNode):
        class Cls:
            pass

        node = ClassNode(cls=Cls, name="Cls", bases=(int_node,))
        assert node.edges() is node.edges()


class TestTypeEdgeHelperMethods:
    def test_field_creates_field_edge(self):
        edge = TypeEdge.field("my_field")
        assert edge.kind == TypeEdgeKind.FIELD
        assert edge.name == "my_field"
        assert edge.index is None

    def test_element_creates_element_edge(self):
        edge = TypeEdge.element(2)
        assert edge.kind == TypeEdgeKind.ELEMENT
        assert edge.index == 2
        assert edge.name is None


class TestTypeEdgeConnectionRepr:
    def test_repr_includes_edge_and_target(self, int_node: ConcreteNode):
        edge = TypeEdge(TypeEdgeKind.FIELD, name="x")
        conn = TypeEdgeConnection(edge=edge, target=int_node)
        repr_str = repr(conn)
        assert "TypeEdgeConnection" in repr_str
        assert "FIELD" in repr_str


class TestEdgesChildrenInvariant:
    def test_all_node_types_edges_match_children(
        self,
        int_node: ConcreteNode,
        str_node: ConcreteNode,
        typevar_t: TypeVarNode,
        paramspec_p: ParamSpecNode,
        typevartuple_ts: TypeVarTupleNode,
    ):
        sig = SignatureNode(
            parameters=(Parameter(name="x", type=int_node),), returns=str_node
        )
        method_sig = MethodSig(name="method", signature=sig)

        nodes_to_test = [
            AnyNode(),
            NeverNode(),
            SelfNode(),
            LiteralStringNode(),
            EllipsisNode(),
            LiteralNode(values=(1, 2)),
            ConcreteNode(cls=int),
            TypeVarNode(name="T", bound=int_node),
            TypeVarNode(name="T", constraints=(int_node, str_node)),
            TypeVarNode(name="T", default=int_node),
            TypeVarNode(name="T"),
            ParamSpecNode(name="P"),
            ParamSpecNode(name="P", default=int_node),
            TypeVarTupleNode(name="Ts"),
            TypeVarTupleNode(name="Ts", default=TupleNode(elements=(int_node,))),
            GenericTypeNode(cls=list),
            GenericTypeNode(cls=list, type_params=(typevar_t,)),
            SubscriptedGenericNode(
                origin=GenericTypeNode(cls=list), args=(int_node, str_node)
            ),
            TypeAliasNode(name="Alias", value=int_node),
            GenericAliasNode(name="GenAlias", type_params=(typevar_t,), value=int_node),
            UnionNode(members=(int_node, str_node)),
            IntersectionNode(members=(int_node, str_node)),
            TupleNode(elements=(int_node, str_node)),
            TupleNode(elements=()),
            AnnotatedNode(base=int_node),
            CallableNode(params=(int_node,), returns=str_node),
            CallableNode(params=paramspec_p, returns=int_node),
            CallableNode(params=EllipsisNode(), returns=int_node),
            ConcatenateNode(prefix=(int_node,), param_spec=paramspec_p),
            UnpackNode(target=typevartuple_ts),
            sig,
            FunctionNode(name="f", signature=sig),
            TypeGuardNode(narrows_to=int_node),
            TypeIsNode(narrows_to=int_node),
            MetaNode(of=int_node),
            NewTypeNode(name="NT", supertype=int_node),
            ForwardRefNode(ref="X"),
            ForwardRefNode(ref="X", state=RefResolved(node=int_node)),
            ForwardRefNode(ref="X", state=RefFailed(error="err")),
            TypedDictNode(name="TD", fields=(FieldDef(name="f", type=int_node),)),
            NamedTupleNode(name="NT", fields=(FieldDef(name="f", type=int_node),)),
            DataclassNode(
                cls=type("DC", (), {}),
                fields=(DataclassFieldDef(name="f", type=int_node),),
            ),
            EnumNode(cls=type("E", (), {}), value_type=int_node, members=(("A", 1),)),
            ProtocolNode(name="P", methods=(method_sig,)),
            ProtocolNode(
                name="P", methods=(), attributes=(FieldDef(name="a", type=int_node),)
            ),
            ClassNode(cls=type("C", (), {}), name="C"),
            ClassNode(
                cls=type("C", (), {}),
                name="C",
                type_params=(typevar_t,),
                bases=(int_node,),
                methods=(method_sig,),
                class_vars=(FieldDef(name="cv", type=str_node),),
                instance_vars=(FieldDef(name="iv", type=int_node),),
            ),
        ]

        for node in nodes_to_test:
            edge_targets = [conn.target for conn in node.edges()]
            children_list = list(node.children())
            assert edge_targets == children_list, (
                f"Mismatch for {type(node).__name__}: "
                f"edges={edge_targets}, children={children_list}"
            )
