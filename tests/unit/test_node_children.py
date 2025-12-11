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
    TypeGuardNode,
    TypeIsNode,
    TypeNode,
    TypeVarNode,
    TypeVarTupleNode,
    UnionNode,
    UnpackNode,
)


class TestAnyNodeChildren:
    def test_children_returns_empty_tuple(self):
        node = AnyNode()
        assert node.children() == ()

    def test_children_cached(self):
        node = AnyNode()
        assert node.children() is node.children()


class TestNeverNodeChildren:
    def test_children_returns_empty_tuple(self):
        node = NeverNode()
        assert node.children() == ()

    def test_children_cached(self):
        node = NeverNode()
        assert node.children() is node.children()


class TestSelfNodeChildren:
    def test_children_returns_empty_tuple(self):
        node = SelfNode()
        assert node.children() == ()

    def test_children_cached(self):
        node = SelfNode()
        assert node.children() is node.children()


class TestLiteralStringNodeChildren:
    def test_children_returns_empty_tuple(self):
        node = LiteralStringNode()
        assert node.children() == ()

    def test_children_cached(self):
        node = LiteralStringNode()
        assert node.children() is node.children()


class TestEllipsisNodeChildren:
    def test_children_returns_empty_tuple(self):
        node = EllipsisNode()
        assert node.children() == ()

    def test_children_cached(self):
        node = EllipsisNode()
        assert node.children() is node.children()


class TestLiteralNodeChildren:
    def test_children_returns_empty_tuple(self):
        node = LiteralNode(values=(1, 2, "hello"))
        assert node.children() == ()

    def test_children_cached(self):
        node = LiteralNode(values=("a", "b"))
        assert node.children() is node.children()


class TestConcreteNodeChildren:
    def test_children_returns_empty_tuple(self, int_node: ConcreteNode):
        assert int_node.children() == ()

    def test_children_cached(self, float_node: ConcreteNode):
        assert float_node.children() is float_node.children()


class TestTypeVarNodeChildren:
    def test_children_with_bound_only(self, int_node: ConcreteNode):
        node = TypeVarNode(name="T", bound=int_node)
        children = node.children()
        assert len(children) == 1
        assert int_node in children

    def test_children_with_constraints(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        node = TypeVarNode(name="T", constraints=(int_node, str_node))
        children = node.children()
        assert len(children) == 2
        assert int_node in children
        assert str_node in children

    def test_children_with_default(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        node = TypeVarNode(name="T", bound=int_node, default=str_node)
        children = node.children()
        assert len(children) == 2
        assert int_node in children
        assert str_node in children

    def test_children_no_bound_no_constraints(self):
        node = TypeVarNode(name="T")
        assert node.children() == ()

    def test_children_with_default_includes_default(self):
        default = ConcreteNode(cls=str)
        node = TypeVarNode(name="T", default=default)
        assert default in node.children()

    def test_children_cached(self, int_node: ConcreteNode):
        node = TypeVarNode(name="T", bound=int_node)
        assert node.children() is node.children()


class TestParamSpecNodeChildren:
    def test_children_without_default(self):
        node = ParamSpecNode(name="P")
        assert node.children() == ()

    def test_children_with_default(self, int_node: ConcreteNode):
        node = ParamSpecNode(name="P", default=int_node)
        children = node.children()
        assert len(children) == 1
        assert int_node in children

    def test_children_cached_with_default(self, int_node: ConcreteNode):
        node = ParamSpecNode(name="P", default=int_node)
        assert node.children() is node.children()

    def test_children_cached_without_default(self):
        node = ParamSpecNode(name="P")
        assert node.children() is node.children()


class TestTypeVarTupleNodeChildren:
    def test_children_without_default(self):
        node = TypeVarTupleNode(name="Ts")
        assert node.children() == ()

    def test_children_with_default(self, int_node: ConcreteNode):
        default_tuple = TupleNode(elements=(int_node,))
        node = TypeVarTupleNode(name="Ts", default=default_tuple)
        children = node.children()
        assert len(children) == 1
        assert default_tuple in children

    def test_children_cached_with_default(self, int_node: ConcreteNode):
        default_tuple = TupleNode(elements=(int_node,))
        node = TypeVarTupleNode(name="Ts", default=default_tuple)
        assert node.children() is node.children()

    def test_children_cached_without_default(self):
        node = TypeVarTupleNode(name="Ts")
        assert node.children() is node.children()


class TestGenericTypeNodeChildren:
    def test_children_without_type_params(self):
        node = GenericTypeNode(cls=list)
        assert node.children() == ()

    def test_children_with_type_params(self, typevar_t: TypeVarNode):
        typevar_u = TypeVarNode(name="U")
        node = GenericTypeNode(cls=dict, type_params=(typevar_t, typevar_u))
        children = node.children()
        assert len(children) == 2
        assert typevar_t in children
        assert typevar_u in children

    def test_children_cached(self, typevar_t: TypeVarNode):
        node = GenericTypeNode(cls=list, type_params=(typevar_t,))
        assert node.children() is node.children()


class TestSubscriptedGenericNodeChildren:
    def test_children_includes_origin_and_args(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        origin = GenericTypeNode(cls=dict)
        node = SubscriptedGenericNode(origin=origin, args=(int_node, str_node))
        children = node.children()
        assert len(children) == 3
        assert origin in children
        assert int_node in children
        assert str_node in children

    def test_children_with_single_arg(self, int_node: ConcreteNode):
        origin = GenericTypeNode(cls=list)
        node = SubscriptedGenericNode(origin=origin, args=(int_node,))
        children = node.children()
        assert len(children) == 2
        assert origin in children
        assert int_node in children

    def test_children_cached(self, int_node: ConcreteNode):
        origin = GenericTypeNode(cls=list)
        node = SubscriptedGenericNode(origin=origin, args=(int_node,))
        assert node.children() is node.children()


class TestTypeAliasNodeChildren:
    def test_children_includes_value(self, int_node: ConcreteNode):
        node = TypeAliasNode(name="IntAlias", value=int_node)
        children = node.children()
        assert len(children) == 1
        assert int_node in children

    def test_children_cached(self, int_node: ConcreteNode):
        node = TypeAliasNode(name="Alias", value=int_node)
        assert node.children() is node.children()


class TestGenericAliasNodeChildren:
    def test_children_includes_type_params_and_value(
        self, typevar_t: TypeVarNode, int_node: ConcreteNode
    ):
        node = GenericAliasNode(
            name="MyAlias", type_params=(typevar_t,), value=int_node
        )
        children = node.children()
        assert len(children) == 2
        assert typevar_t in children
        assert int_node in children

    def test_children_with_multiple_type_params(
        self, typevar_t: TypeVarNode, int_node: ConcreteNode
    ):
        typevar_u = TypeVarNode(name="U")
        node = GenericAliasNode(
            name="MyAlias", type_params=(typevar_t, typevar_u), value=int_node
        )
        children = node.children()
        assert len(children) == 3
        assert typevar_t in children
        assert typevar_u in children
        assert int_node in children

    def test_children_cached(self, typevar_t: TypeVarNode, int_node: ConcreteNode):
        node = GenericAliasNode(name="Alias", type_params=(typevar_t,), value=int_node)
        assert node.children() is node.children()


class TestUnionNodeChildren:
    def test_children_returns_members(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        node = UnionNode(members=(int_node, str_node))
        children = node.children()
        assert len(children) == 2
        assert int_node in children
        assert str_node in children

    def test_children_with_three_members(
        self, int_node: ConcreteNode, str_node: ConcreteNode, float_node: ConcreteNode
    ):
        node = UnionNode(members=(int_node, str_node, float_node))
        children = node.children()
        assert len(children) == 3
        assert int_node in children
        assert str_node in children
        assert float_node in children

    def test_children_cached(self, int_node: ConcreteNode, str_node: ConcreteNode):
        node = UnionNode(members=(int_node, str_node))
        assert node.children() is node.children()


class TestIntersectionNodeChildren:
    def test_children_returns_members(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        node = IntersectionNode(members=(int_node, str_node))
        children = node.children()
        assert len(children) == 2
        assert int_node in children
        assert str_node in children

    def test_children_cached(self, int_node: ConcreteNode, str_node: ConcreteNode):
        node = IntersectionNode(members=(int_node, str_node))
        assert node.children() is node.children()


class TestTupleNodeChildren:
    def test_children_returns_elements(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        node = TupleNode(elements=(int_node, str_node))
        children = node.children()
        assert len(children) == 2
        assert int_node in children
        assert str_node in children

    def test_children_empty_tuple(self):
        node = TupleNode(elements=())
        assert node.children() == ()

    def test_children_homogeneous_tuple(self, int_node: ConcreteNode):
        node = TupleNode(elements=(int_node,), homogeneous=True)
        children = node.children()
        assert len(children) == 1
        assert int_node in children

    def test_children_cached(self, int_node: ConcreteNode, str_node: ConcreteNode):
        node = TupleNode(elements=(int_node, str_node))
        assert node.children() is node.children()


class TestAnnotatedNodeChildren:
    def test_children_includes_base(self, int_node: ConcreteNode):
        node = AnnotatedNode(base=int_node, annotations=("some_metadata",))
        children = node.children()
        assert len(children) == 1
        assert int_node in children

    def test_children_cached(self, int_node: ConcreteNode):
        node = AnnotatedNode(base=int_node)
        assert node.children() is node.children()


class TestCallableNodeChildren:
    def test_children_with_tuple_params(
        self, int_node: ConcreteNode, str_node: ConcreteNode, float_node: ConcreteNode
    ):
        node = CallableNode(params=(int_node, str_node), returns=float_node)
        children = node.children()
        assert len(children) == 3
        assert int_node in children
        assert str_node in children
        assert float_node in children

    def test_children_with_paramspec(
        self, paramspec_p: ParamSpecNode, int_node: ConcreteNode
    ):
        node = CallableNode(params=paramspec_p, returns=int_node)
        children = node.children()
        assert len(children) == 2
        assert paramspec_p in children
        assert int_node in children

    def test_children_with_ellipsis(self, int_node: ConcreteNode):
        ellipsis_node = EllipsisNode()
        node = CallableNode(params=ellipsis_node, returns=int_node)
        children = node.children()
        assert len(children) == 2
        assert ellipsis_node in children
        assert int_node in children

    def test_children_with_empty_params(self, int_node: ConcreteNode):
        node = CallableNode(params=(), returns=int_node)
        children = node.children()
        assert len(children) == 1
        assert int_node in children

    def test_children_cached(self, int_node: ConcreteNode, str_node: ConcreteNode):
        node = CallableNode(params=(int_node,), returns=str_node)
        assert node.children() is node.children()


class TestConcatenateNodeChildren:
    def test_children_includes_prefix_and_paramspec(
        self,
        int_node: ConcreteNode,
        str_node: ConcreteNode,
        paramspec_p: ParamSpecNode,
    ):
        node = ConcatenateNode(prefix=(int_node, str_node), param_spec=paramspec_p)
        children = node.children()
        assert len(children) == 3
        assert int_node in children
        assert str_node in children
        assert paramspec_p in children

    def test_children_with_empty_prefix(self, paramspec_p: ParamSpecNode):
        node = ConcatenateNode(prefix=(), param_spec=paramspec_p)
        children = node.children()
        assert len(children) == 1
        assert paramspec_p in children

    def test_children_cached(self, int_node: ConcreteNode, paramspec_p: ParamSpecNode):
        node = ConcatenateNode(prefix=(int_node,), param_spec=paramspec_p)
        assert node.children() is node.children()


class TestUnpackNodeChildren:
    def test_children_includes_target(self, typevartuple_ts: TypeVarTupleNode):
        node = UnpackNode(target=typevartuple_ts)
        children = node.children()
        assert len(children) == 1
        assert typevartuple_ts in children

    def test_children_with_tuple_target(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        tuple_node = TupleNode(elements=(int_node, str_node))
        node = UnpackNode(target=tuple_node)
        children = node.children()
        assert len(children) == 1
        assert tuple_node in children

    def test_children_cached(self, typevartuple_ts: TypeVarTupleNode):
        node = UnpackNode(target=typevartuple_ts)
        assert node.children() is node.children()


class TestSignatureNodeChildren:
    def test_children_includes_params_return_and_type_params(
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
        children = node.children()
        assert len(children) == 4
        assert int_node in children
        assert str_node in children
        assert typevar_t in children

    def test_children_without_type_params(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        params = (Parameter(name="arg", type=int_node),)
        node = SignatureNode(parameters=params, returns=str_node)
        children = node.children()
        assert len(children) == 2
        assert int_node in children
        assert str_node in children

    def test_children_without_params(self, int_node: ConcreteNode):
        node = SignatureNode(parameters=(), returns=int_node)
        children = node.children()
        assert len(children) == 1
        assert int_node in children

    def test_children_cached(self, int_node: ConcreteNode):
        node = SignatureNode(parameters=(), returns=int_node)
        assert node.children() is node.children()


class TestFunctionNodeChildren:
    def test_children_includes_signature(self, int_node: ConcreteNode):
        sig = SignatureNode(parameters=(), returns=int_node)
        node = FunctionNode(name="my_func", signature=sig)
        children = node.children()
        assert len(children) == 1
        assert sig in children

    def test_children_cached(self, int_node: ConcreteNode):
        sig = SignatureNode(parameters=(), returns=int_node)
        node = FunctionNode(name="f", signature=sig)
        assert node.children() is node.children()


class TestTypeGuardNodeChildren:
    def test_children_includes_narrows_to(self, int_node: ConcreteNode):
        node = TypeGuardNode(narrows_to=int_node)
        children = node.children()
        assert len(children) == 1
        assert int_node in children

    def test_children_cached(self, int_node: ConcreteNode):
        node = TypeGuardNode(narrows_to=int_node)
        assert node.children() is node.children()


class TestTypeIsNodeChildren:
    def test_children_includes_narrows_to(self, int_node: ConcreteNode):
        node = TypeIsNode(narrows_to=int_node)
        children = node.children()
        assert len(children) == 1
        assert int_node in children

    def test_children_cached(self, int_node: ConcreteNode):
        node = TypeIsNode(narrows_to=int_node)
        assert node.children() is node.children()


class TestMetaNodeChildren:
    def test_children_includes_of(self, int_node: ConcreteNode):
        node = MetaNode(of=int_node)
        children = node.children()
        assert len(children) == 1
        assert int_node in children

    def test_children_cached(self, int_node: ConcreteNode):
        node = MetaNode(of=int_node)
        assert node.children() is node.children()


class TestNewTypeNodeChildren:
    def test_children_includes_supertype(self, int_node: ConcreteNode):
        node = NewTypeNode(name="UserId", supertype=int_node)
        children = node.children()
        assert len(children) == 1
        assert int_node in children

    def test_children_cached(self, int_node: ConcreteNode):
        node = NewTypeNode(name="Id", supertype=int_node)
        assert node.children() is node.children()


class TestForwardRefNodeChildren:
    def test_children_unresolved_returns_empty(self):
        node = ForwardRefNode(ref="MyClass", state=RefUnresolved())
        assert node.children() == ()

    def test_children_failed_returns_empty(self):
        node = ForwardRefNode(ref="Missing", state=RefFailed(error="Not found"))
        assert node.children() == ()

    def test_children_resolved_includes_resolved_node(self, int_node: ConcreteNode):
        node = ForwardRefNode(ref="int", state=RefResolved(node=int_node))
        children = node.children()
        assert len(children) == 1
        assert int_node in children

    def test_children_cached_resolved(self, int_node: ConcreteNode):
        node = ForwardRefNode(ref="int", state=RefResolved(node=int_node))
        assert node.children() is node.children()

    def test_children_cached_unresolved(self):
        node = ForwardRefNode(ref="Unresolved")
        assert node.children() is node.children()


class TestTypedDictNodeChildren:
    def test_children_includes_field_types(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        fields = (
            FieldDef(name="id", type=int_node),
            FieldDef(name="name", type=str_node),
        )
        node = TypedDictNode(name="Person", fields=fields)
        children = node.children()
        assert len(children) == 2
        assert int_node in children
        assert str_node in children

    def test_children_empty_fields(self):
        node = TypedDictNode(name="Empty", fields=())
        assert node.children() == ()

    def test_children_cached(self, int_node: ConcreteNode):
        fields = (FieldDef(name="value", type=int_node),)
        node = TypedDictNode(name="TD", fields=fields)
        assert node.children() is node.children()


class TestNamedTupleNodeChildren:
    def test_children_includes_field_types(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        fields = (
            FieldDef(name="x", type=int_node),
            FieldDef(name="y", type=str_node),
        )
        node = NamedTupleNode(name="Point", fields=fields)
        children = node.children()
        assert len(children) == 2
        assert int_node in children
        assert str_node in children

    def test_children_empty_fields(self):
        node = NamedTupleNode(name="Empty", fields=())
        assert node.children() == ()

    def test_children_cached(self, int_node: ConcreteNode):
        fields = (FieldDef(name="val", type=int_node),)
        node = NamedTupleNode(name="NT", fields=fields)
        assert node.children() is node.children()


class TestDataclassNodeChildren:
    def test_children_includes_field_types(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        class MyDataclass:
            pass

        fields = (
            DataclassFieldDef(name="id", type=int_node),
            DataclassFieldDef(name="name", type=str_node),
        )
        node = DataclassNode(cls=MyDataclass, fields=fields)
        children = node.children()
        assert len(children) == 2
        assert int_node in children
        assert str_node in children

    def test_children_empty_fields(self):
        class EmptyDC:
            pass

        node = DataclassNode(cls=EmptyDC, fields=())
        assert node.children() == ()

    def test_children_cached(self, int_node: ConcreteNode):
        class DC:
            pass

        fields = (DataclassFieldDef(name="val", type=int_node),)
        node = DataclassNode(cls=DC, fields=fields)
        assert node.children() is node.children()


class TestEnumNodeChildren:
    def test_children_includes_value_type(self, int_node: ConcreteNode):
        class Status(IntEnum):
            ACTIVE = 1
            INACTIVE = 0

        node = EnumNode(
            cls=Status,
            value_type=int_node,
            members=(("ACTIVE", 1), ("INACTIVE", 0)),
        )
        children = node.children()
        assert len(children) == 1
        assert int_node in children

    def test_children_cached(self, int_node: ConcreteNode):
        class E:
            pass

        node = EnumNode(cls=E, value_type=int_node, members=())
        assert node.children() is node.children()


class TestProtocolNodeChildren:
    def test_children_includes_methods_and_attributes(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        sig = SignatureNode(parameters=(), returns=int_node)
        methods = (MethodSig(name="get_id", signature=sig),)
        attributes = (FieldDef(name="name", type=str_node),)
        node = ProtocolNode(name="Identifiable", methods=methods, attributes=attributes)
        children = node.children()
        assert len(children) == 2
        assert sig in children
        assert str_node in children

    def test_children_methods_only(self, int_node: ConcreteNode):
        sig = SignatureNode(parameters=(), returns=int_node)
        methods = (MethodSig(name="method", signature=sig),)
        node = ProtocolNode(name="Proto", methods=methods)
        children = node.children()
        assert len(children) == 1
        assert sig in children

    def test_children_attributes_only(self, str_node: ConcreteNode):
        attributes = (FieldDef(name="attr", type=str_node),)
        node = ProtocolNode(name="Proto", methods=(), attributes=attributes)
        children = node.children()
        assert len(children) == 1
        assert str_node in children

    def test_children_empty_protocol(self):
        node = ProtocolNode(name="EmptyProto", methods=())
        assert node.children() == ()

    def test_children_cached(self, int_node: ConcreteNode):
        sig = SignatureNode(parameters=(), returns=int_node)
        methods = (MethodSig(name="m", signature=sig),)
        node = ProtocolNode(name="P", methods=methods)
        assert node.children() is node.children()


class TestClassNodeChildren:
    def test_children_includes_all_components(
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
        children = node.children()
        assert len(children) == 5
        assert typevar_t in children
        assert base_node in children
        assert sig in children
        assert str_node in children
        assert float_node in children

    def test_children_minimal_class(self):
        class MinimalClass:
            pass

        node = ClassNode(cls=MinimalClass, name="MinimalClass")
        assert node.children() == ()

    def test_children_with_multiple_bases(
        self, int_node: ConcreteNode, str_node: ConcreteNode
    ):
        class MultiBaseClass:
            pass

        node = ClassNode(
            cls=MultiBaseClass,
            name="MultiBaseClass",
            bases=(int_node, str_node),
        )
        children = node.children()
        assert len(children) == 2
        assert int_node in children
        assert str_node in children

    def test_children_cached(self, int_node: ConcreteNode):
        class Cls:
            pass

        node = ClassNode(cls=Cls, name="Cls", bases=(int_node,))
        assert node.children() is node.children()


class TestChildrenEdgesInvariant:
    def test_all_node_types_children_match_edge_targets(
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

        nodes_to_test: list[TypeNode] = [
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
