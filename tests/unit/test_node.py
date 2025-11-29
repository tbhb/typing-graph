from enum import Enum

from typing_graph import (
    AnyNode,
    CallableNode,
    ClassNode,
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
    LiteralNode,
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
    TypeNode,
    TypeVarNode,
    TypeVarTupleNode,
    UnionNode,
)
from typing_graph._node import (
    AnnotatedNode,
    ConcatenateNode,
    DiscriminatedUnionNode,
    IntersectionNode,
    LiteralStringNode,
    MetaNode,
    TypeGuardNode,
    TypeIsNode,
    UnpackNode,
    is_annotated_node,
    is_any_node,
    is_callable_node,
    is_class_node,
    is_concatenate_node,
    is_concrete_node,
    is_dataclass_node,
    is_discriminated_union_node,
    is_ellipsis_node,
    is_enum_node,
    is_forward_ref_node,
    is_function_node,
    is_generic_alias_node,
    is_generic_node,
    is_intersection_node,
    is_literal_node,
    is_literal_string_node,
    is_meta_node,
    is_method_sig,
    is_named_tuple_node,
    is_never_node,
    is_new_type_node,
    is_param_spec_node,
    is_protocol_node,
    is_ref_state_failed,
    is_ref_state_resolved,
    is_ref_state_unresolved,
    is_self_node,
    is_signature_node,
    is_structured_node,
    is_subscripted_generic_node,
    is_tuple_node,
    is_type_alias_node,
    is_type_guard_node,
    is_type_is_node,
    is_type_node,
    is_type_var_node,
    is_type_var_tuple_node,
    is_typed_dict_node,
    is_union_type_node,
    is_unpack_node,
)


class TestTypeVarNode:
    def test_typevar_children_includes_bound(self) -> None:
        bound = ConcreteNode(cls=int)
        node = TypeVarNode(name="T", bound=bound)
        assert bound in node.children()

    def test_typevar_children_includes_constraints(self) -> None:
        constraints = (ConcreteNode(cls=int), ConcreteNode(cls=str))
        node = TypeVarNode(name="T", constraints=constraints)
        children = node.children()
        assert constraints[0] in children
        assert constraints[1] in children


class TestUnionType:
    def test_union_children(self) -> None:
        members = (ConcreteNode(cls=int), ConcreteNode(cls=str))
        node = UnionNode(members=members)
        assert len(node.children()) == 2


class TestTypeGuards:
    def test_is_type_node(self) -> None:
        assert is_type_node(ConcreteNode(cls=int)) is True
        assert is_type_node(int) is False

    def test_is_concrete_node(self) -> None:
        assert is_concrete_node(ConcreteNode(cls=int)) is True
        assert is_concrete_node(AnyNode()) is False

    def test_is_any_node(self) -> None:
        assert is_any_node(AnyNode()) is True
        assert is_any_node(ConcreteNode(cls=int)) is False

    def test_is_never_node(self) -> None:
        assert is_never_node(NeverNode()) is True
        assert is_never_node(AnyNode()) is False

    def test_is_self_node(self) -> None:
        assert is_self_node(SelfNode()) is True
        assert is_self_node(AnyNode()) is False

    def test_is_type_var_node(self) -> None:
        assert is_type_var_node(TypeVarNode(name="T")) is True
        assert is_type_var_node(ConcreteNode(cls=int)) is False

    def test_is_union_type_node(self) -> None:
        members = (ConcreteNode(cls=int), ConcreteNode(cls=str))
        assert is_union_type_node(UnionNode(members=members)) is True
        assert is_union_type_node(ConcreteNode(cls=int)) is False

    def test_is_tuple_node(self) -> None:
        elements = (ConcreteNode(cls=int),)
        assert is_tuple_node(TupleNode(elements=elements)) is True
        assert is_tuple_node(ConcreteNode(cls=int)) is False

    def test_is_callable_node(self) -> None:
        params = (ConcreteNode(cls=int),)
        returns = ConcreteNode(cls=str)
        node = CallableNode(params=params, returns=returns)
        assert is_callable_node(node) is True
        assert is_callable_node(ConcreteNode(cls=int)) is False

    def test_is_literal_node(self) -> None:
        assert is_literal_node(LiteralNode(values=(1,))) is True
        assert is_literal_node(ConcreteNode(cls=int)) is False

    def test_is_forward_ref_node(self) -> None:
        assert is_forward_ref_node(ForwardRefNode(ref="X")) is True
        assert is_forward_ref_node(ConcreteNode(cls=int)) is False

    def test_is_subscripted_generic_node(self) -> None:
        origin = ConcreteNode(cls=list)
        args = (ConcreteNode(cls=int),)
        node = SubscriptedGenericNode(origin=origin, args=args)
        assert is_subscripted_generic_node(node) is True
        assert is_subscripted_generic_node(ConcreteNode(cls=int)) is False

    def test_is_type_var_tuple_node(self) -> None:
        assert is_type_var_tuple_node(TypeVarTupleNode(name="Ts")) is True
        assert is_type_var_tuple_node(TypeVarNode(name="T")) is False

    def test_is_param_spec_node(self) -> None:
        assert is_param_spec_node(ParamSpecNode(name="P")) is True
        assert is_param_spec_node(TypeVarNode(name="T")) is False

    def test_is_concatenate_node(self) -> None:
        prefix = (ConcreteNode(cls=int),)
        param_spec = ParamSpecNode(name="P")
        node = ConcatenateNode(prefix=prefix, param_spec=param_spec)
        assert is_concatenate_node(node) is True
        assert is_concatenate_node(ConcreteNode(cls=int)) is False

    def test_is_unpack_node(self) -> None:
        ts = TypeVarTupleNode(name="Ts")
        node = UnpackNode(target=ts)
        assert is_unpack_node(node) is True
        assert is_unpack_node(ConcreteNode(cls=int)) is False

    def test_is_generic_node(self) -> None:
        assert is_generic_node(GenericTypeNode(cls=list)) is True
        assert is_generic_node(ConcreteNode(cls=int)) is False

    def test_is_ellipsis_node(self) -> None:
        assert is_ellipsis_node(EllipsisNode()) is True
        assert is_ellipsis_node(ConcreteNode(cls=int)) is False

    def test_is_generic_alias_node(self) -> None:
        tv = TypeVarNode(name="T")
        node = GenericAliasNode(
            name="Vector",
            type_params=(tv,),
            value=SubscriptedGenericNode(origin=GenericTypeNode(cls=list), args=(tv,)),
        )
        assert is_generic_alias_node(node) is True
        assert is_generic_alias_node(ConcreteNode(cls=int)) is False

    def test_is_type_alias_node(self) -> None:
        node = TypeAliasNode(name="MyInt", value=ConcreteNode(cls=int))
        assert is_type_alias_node(node) is True
        assert is_type_alias_node(ConcreteNode(cls=int)) is False

    def test_is_discriminated_union_node(self) -> None:
        node = DiscriminatedUnionNode(
            discriminant="kind",
            variants={"a": ConcreteNode(cls=dict), "b": ConcreteNode(cls=list)},
        )
        assert is_discriminated_union_node(node) is True
        assert is_discriminated_union_node(UnionNode(members=())) is False

    def test_is_intersection_node(self) -> None:
        node = IntersectionNode(
            members=(ConcreteNode(cls=dict), ConcreteNode(cls=list))
        )
        assert is_intersection_node(node) is True
        assert is_intersection_node(UnionNode(members=())) is False

    def test_is_named_tuple_node(self) -> None:
        node = NamedTupleNode(
            name="Point",
            fields=(
                FieldDef(name="x", type=ConcreteNode(cls=int)),
                FieldDef(name="y", type=ConcreteNode(cls=int)),
            ),
        )
        assert is_named_tuple_node(node) is True
        assert is_named_tuple_node(TupleNode(elements=())) is False

    def test_is_typed_dict_node(self) -> None:
        node = TypedDictNode(
            name="MyDict",
            fields=(FieldDef(name="key", type=ConcreteNode(cls=str)),),
        )
        assert is_typed_dict_node(node) is True
        assert is_typed_dict_node(ConcreteNode(cls=dict)) is False

    def test_is_structured_node(self) -> None:
        td = TypedDictNode(
            name="MyDict",
            fields=(FieldDef(name="key", type=ConcreteNode(cls=str)),),
        )
        nt = NamedTupleNode(
            name="Point",
            fields=(FieldDef(name="x", type=ConcreteNode(cls=int)),),
        )
        assert is_structured_node(td) is True
        assert is_structured_node(nt) is True
        assert is_structured_node(ConcreteNode(cls=dict)) is False

    def test_is_literal_string_node(self) -> None:
        assert is_literal_string_node(LiteralStringNode()) is True
        assert is_literal_string_node(ConcreteNode(cls=str)) is False

    def test_is_ref_state_resolved(self) -> None:
        resolved = RefResolved(node=ConcreteNode(cls=int))
        unresolved = RefUnresolved()
        failed = RefFailed(error="not found")
        assert is_ref_state_resolved(resolved) is True
        assert is_ref_state_resolved(unresolved) is False
        assert is_ref_state_resolved(failed) is False

    def test_is_ref_state_unresolved(self) -> None:
        resolved = RefResolved(node=ConcreteNode(cls=int))
        unresolved = RefUnresolved()
        failed = RefFailed(error="not found")
        assert is_ref_state_unresolved(unresolved) is True
        assert is_ref_state_unresolved(resolved) is False
        assert is_ref_state_unresolved(failed) is False

    def test_is_ref_state_failed(self) -> None:
        resolved = RefResolved(node=ConcreteNode(cls=int))
        unresolved = RefUnresolved()
        failed = RefFailed(error="not found")
        assert is_ref_state_failed(failed) is True
        assert is_ref_state_failed(resolved) is False
        assert is_ref_state_failed(unresolved) is False

    def test_is_annotated_node(self) -> None:
        node = AnnotatedNode(base=ConcreteNode(cls=int), annotations=("metadata",))
        assert is_annotated_node(node) is True
        assert is_annotated_node(ConcreteNode(cls=int)) is False

    def test_is_meta_node(self) -> None:
        node = MetaNode(of=ConcreteNode(cls=int))
        assert is_meta_node(node) is True
        assert is_meta_node(ConcreteNode(cls=type)) is False

    def test_is_type_guard_node(self) -> None:
        node = TypeGuardNode(narrows_to=ConcreteNode(cls=int))
        assert is_type_guard_node(node) is True
        assert is_type_guard_node(ConcreteNode(cls=bool)) is False

    def test_is_type_is_node(self) -> None:
        node = TypeIsNode(narrows_to=ConcreteNode(cls=int))
        assert is_type_is_node(node) is True
        assert is_type_is_node(ConcreteNode(cls=bool)) is False

    def test_is_dataclass_node(self) -> None:
        node = DataclassNode(
            cls=object,
            fields=(DataclassFieldDef(name="x", type=ConcreteNode(cls=int)),),
        )
        assert is_dataclass_node(node) is True
        assert is_dataclass_node(ConcreteNode(cls=object)) is False

    def test_is_enum_node(self) -> None:
        class Color(Enum):
            RED = 1
            GREEN = 2

        node = EnumNode(
            cls=Color,
            value_type=ConcreteNode(cls=int),
            members=(("RED", 1), ("GREEN", 2)),
        )
        assert is_enum_node(node) is True
        assert is_enum_node(ConcreteNode(cls=Enum)) is False

    def test_is_new_type_node(self) -> None:
        node = NewTypeNode(name="UserId", supertype=ConcreteNode(cls=int))
        assert is_new_type_node(node) is True
        assert is_new_type_node(ConcreteNode(cls=int)) is False

    def test_is_signature_node(self) -> None:
        node = SignatureNode(
            parameters=(Parameter(name="x", type=ConcreteNode(cls=int)),),
            returns=ConcreteNode(cls=str),
        )
        assert is_signature_node(node) is True
        assert is_signature_node(CallableNode(params=(), returns=AnyNode())) is False

    def test_is_method_sig(self) -> None:
        sig = SignatureNode(
            parameters=(Parameter(name="self", type=AnyNode()),),
            returns=ConcreteNode(cls=type(None)),
        )
        node = MethodSig(name="my_method", signature=sig)
        assert is_method_sig(node) is True
        assert is_method_sig(sig) is False

    def test_is_protocol_node(self) -> None:
        sig = SignatureNode(
            parameters=(Parameter(name="self", type=AnyNode()),),
            returns=AnyNode(),
        )
        node = ProtocolNode(
            name="MyProtocol",
            methods=(MethodSig(name="do_something", signature=sig),),
        )
        assert is_protocol_node(node) is True
        assert is_protocol_node(ConcreteNode(cls=object)) is False

    def test_is_function_node(self) -> None:
        sig = SignatureNode(
            parameters=(Parameter(name="x", type=ConcreteNode(cls=int)),),
            returns=ConcreteNode(cls=str),
        )
        node = FunctionNode(name="my_func", signature=sig)
        assert is_function_node(node) is True
        assert is_function_node(sig) is False

    def test_is_class_node(self) -> None:
        node = ClassNode(cls=object, name="MyClass")
        assert is_class_node(node) is True
        assert is_class_node(ConcreteNode(cls=type)) is False


class TestNodeHashability:
    def test_nodes_usable_as_dict_keys(self) -> None:
        cache: dict[TypeNode, str] = {}
        node1 = ConcreteNode(cls=int)
        node2 = ConcreteNode(cls=str)

        cache[node1] = "integer"
        cache[node2] = "string"

        assert cache[node1] == "integer"
        assert cache[node2] == "string"
        assert len(cache) == 2

    def test_nodes_usable_in_sets(self) -> None:
        nodes = {
            ConcreteNode(cls=int),
            ConcreteNode(cls=int),  # duplicate
            ConcreteNode(cls=str),
        }
        assert len(nodes) == 2

    def test_complex_nodes_usable_as_dict_keys(self) -> None:
        cache: dict[TypeNode, str] = {}
        union = UnionNode(members=(ConcreteNode(cls=int), ConcreteNode(cls=str)))
        callable_node = CallableNode(
            params=(ConcreteNode(cls=int),),
            returns=ConcreteNode(cls=str),
        )

        cache[union] = "union"
        cache[callable_node] = "callable"

        assert cache[union] == "union"
        assert len(cache) == 2

    def test_nodes_with_post_init_usable_in_sets(self) -> None:
        tv = TypeVarNode(name="T", bound=ConcreteNode(cls=int))
        concat = ConcatenateNode(
            prefix=(ConcreteNode(cls=int),),
            param_spec=ParamSpecNode(name="P"),
        )
        sub = SubscriptedGenericNode(
            origin=GenericTypeNode(cls=list),
            args=(ConcreteNode(cls=int),),
        )

        nodes = {tv, concat, sub}
        assert len(nodes) == 3


class TestNodeChildrenMethods:
    def test_typevar_with_default_includes_default_in_children(self) -> None:
        default = ConcreteNode(cls=str)
        node = TypeVarNode(name="T", default=default)
        assert default in node.children()

    def test_paramspec_with_default_includes_default_in_children(self) -> None:
        default = ConcreteNode(cls=int)
        node = ParamSpecNode(name="P", default=default)
        children = node.children()
        assert len(children) == 1
        assert default in children

    def test_paramspec_without_default_has_empty_children(self) -> None:
        node = ParamSpecNode(name="P")
        assert node.children() == ()

    def test_typevartuple_with_default_includes_default_in_children(self) -> None:
        default = TupleNode(elements=(ConcreteNode(cls=int),))
        node = TypeVarTupleNode(name="Ts", default=default)
        children = node.children()
        assert len(children) == 1
        assert default in children

    def test_typevartuple_without_default_has_empty_children(self) -> None:
        node = TypeVarTupleNode(name="Ts")
        assert node.children() == ()

    def test_concatenate_children_includes_prefix_and_paramspec(self) -> None:
        prefix1 = ConcreteNode(cls=int)
        prefix2 = ConcreteNode(cls=str)
        param_spec = ParamSpecNode(name="P")
        node = ConcatenateNode(prefix=(prefix1, prefix2), param_spec=param_spec)
        children = node.children()
        assert len(children) == 3
        assert prefix1 in children
        assert prefix2 in children
        assert param_spec in children

    def test_unpack_children_includes_target(self) -> None:
        ts = TypeVarTupleNode(name="Ts")
        node = UnpackNode(target=ts)
        children = node.children()
        assert len(children) == 1
        assert ts in children

    def test_generic_type_children_includes_type_params(self) -> None:
        tv1 = TypeVarNode(name="K")
        tv2 = TypeVarNode(name="V")
        node = GenericTypeNode(cls=dict, type_params=(tv1, tv2))
        children = node.children()
        assert len(children) == 2
        assert tv1 in children
        assert tv2 in children

    def test_generic_type_without_params_has_empty_children(self) -> None:
        node = GenericTypeNode(cls=list)
        assert node.children() == ()

    def test_literal_string_type_has_empty_children(self) -> None:
        node = LiteralStringNode()
        assert node.children() == ()

    def test_forward_ref_resolved_includes_node_in_children(self) -> None:
        resolved_node = ConcreteNode(cls=int)
        state = RefResolved(node=resolved_node)
        node = ForwardRefNode(ref="SomeClass", state=state)
        children = node.children()
        assert len(children) == 1
        assert resolved_node in children

    def test_forward_ref_unresolved_has_empty_children(self) -> None:
        node = ForwardRefNode(ref="SomeClass", state=RefUnresolved())
        assert node.children() == ()

    def test_forward_ref_failed_has_empty_children(self) -> None:
        node = ForwardRefNode(ref="SomeClass", state=RefFailed(error="Not found"))
        assert node.children() == ()

    def test_subscripted_generic_children_includes_origin_and_args(self) -> None:
        origin = GenericTypeNode(cls=list)
        arg = ConcreteNode(cls=int)
        node = SubscriptedGenericNode(origin=origin, args=(arg,))
        children = node.children()
        assert len(children) == 2
        assert origin in children
        assert arg in children

    def test_generic_alias_children_includes_type_params_and_value(self) -> None:
        tv = TypeVarNode(name="T")
        value = SubscriptedGenericNode(origin=GenericTypeNode(cls=list), args=(tv,))
        node = GenericAliasNode(name="Vector", type_params=(tv,), value=value)
        children = node.children()
        assert len(children) == 2
        assert tv in children
        assert value in children

    def test_type_alias_children_includes_value(self) -> None:
        value = ConcreteNode(cls=int)
        node = TypeAliasNode(name="MyInt", value=value)
        children = node.children()
        assert len(children) == 1
        assert value in children

    def test_discriminated_union_children_includes_variants(self) -> None:
        variant_a = ConcreteNode(cls=dict)
        variant_b = ConcreteNode(cls=list)
        node = DiscriminatedUnionNode(
            discriminant="kind", variants={"a": variant_a, "b": variant_b}
        )
        children = node.children()
        assert len(children) == 2
        assert variant_a in children
        assert variant_b in children

    def test_intersection_type_children_includes_members(self) -> None:
        member1 = ConcreteNode(cls=dict)
        member2 = ConcreteNode(cls=list)
        node = IntersectionNode(members=(member1, member2))
        children = node.children()
        assert len(children) == 2
        assert member1 in children
        assert member2 in children

    def test_callable_with_paramspec_children(self) -> None:
        ps = ParamSpecNode(name="P")
        returns = ConcreteNode(cls=str)
        node = CallableNode(params=ps, returns=returns)
        children = node.children()
        assert len(children) == 2
        assert ps in children
        assert returns in children

    def test_callable_with_ellipsis_children(self) -> None:
        ellipsis = EllipsisNode()
        returns = ConcreteNode(cls=str)
        node = CallableNode(params=ellipsis, returns=returns)
        children = node.children()
        assert len(children) == 2
        assert ellipsis in children
        assert returns in children

    def test_tuple_type_children_includes_elements(self) -> None:
        elem1 = ConcreteNode(cls=int)
        elem2 = ConcreteNode(cls=str)
        node = TupleNode(elements=(elem1, elem2))
        children = node.children()
        assert len(children) == 2
        assert elem1 in children
        assert elem2 in children

    def test_annotated_type_children_includes_base(self) -> None:
        base = ConcreteNode(cls=int)
        node = AnnotatedNode(base=base, annotations=("metadata",))
        children = node.children()
        assert len(children) == 1
        assert base in children

    def test_meta_type_children_includes_of(self) -> None:
        of_type = ConcreteNode(cls=int)
        node = MetaNode(of=of_type)
        children = node.children()
        assert len(children) == 1
        assert of_type in children

    def test_type_guard_type_children_includes_narrows_to(self) -> None:
        narrows_to = ConcreteNode(cls=int)
        node = TypeGuardNode(narrows_to=narrows_to)
        children = node.children()
        assert len(children) == 1
        assert narrows_to in children

    def test_type_is_type_children_includes_narrows_to(self) -> None:
        narrows_to = ConcreteNode(cls=int)
        node = TypeIsNode(narrows_to=narrows_to)
        children = node.children()
        assert len(children) == 1
        assert narrows_to in children

    def test_typed_dict_type_children_includes_field_types(self) -> None:
        field1 = FieldDef(name="a", type=ConcreteNode(cls=int))
        field2 = FieldDef(name="b", type=ConcreteNode(cls=str))
        node = TypedDictNode(name="MyDict", fields=(field1, field2))
        children = node.children()
        assert len(children) == 2
        assert field1.type in children
        assert field2.type in children

    def test_typed_dict_get_fields(self) -> None:
        field1 = FieldDef(name="a", type=ConcreteNode(cls=int))
        field2 = FieldDef(name="b", type=ConcreteNode(cls=str))
        node = TypedDictNode(name="MyDict", fields=(field1, field2))
        fields = node.get_fields()
        assert len(fields) == 2
        assert field1 in fields
        assert field2 in fields

    def test_named_tuple_type_children_includes_field_types(self) -> None:
        field1 = FieldDef(name="x", type=ConcreteNode(cls=int))
        field2 = FieldDef(name="y", type=ConcreteNode(cls=int))
        node = NamedTupleNode(name="Point", fields=(field1, field2))
        children = node.children()
        assert len(children) == 2
        assert field1.type in children
        assert field2.type in children

    def test_named_tuple_get_fields(self) -> None:
        field1 = FieldDef(name="x", type=ConcreteNode(cls=int))
        field2 = FieldDef(name="y", type=ConcreteNode(cls=int))
        node = NamedTupleNode(name="Point", fields=(field1, field2))
        fields = node.get_fields()
        assert len(fields) == 2
        assert field1 in fields
        assert field2 in fields

    def test_dataclass_type_children_includes_field_types(self) -> None:
        field1 = DataclassFieldDef(name="x", type=ConcreteNode(cls=int))
        field2 = DataclassFieldDef(name="y", type=ConcreteNode(cls=str))
        node = DataclassNode(cls=object, fields=(field1, field2))
        children = node.children()
        assert len(children) == 2
        assert field1.type in children
        assert field2.type in children

    def test_dataclass_type_get_fields(self) -> None:
        field1 = DataclassFieldDef(name="x", type=ConcreteNode(cls=int))
        field2 = DataclassFieldDef(name="y", type=ConcreteNode(cls=str))
        node = DataclassNode(cls=object, fields=(field1, field2))
        fields = node.get_fields()
        assert len(fields) == 2
        assert field1 in fields
        assert field2 in fields

    def test_enum_type_children_includes_value_type(self) -> None:
        class Color(Enum):
            RED = 1

        value_type = ConcreteNode(cls=int)
        node = EnumNode(cls=Color, value_type=value_type, members=(("RED", 1),))
        children = node.children()
        assert len(children) == 1
        assert value_type in children

    def test_new_type_node_children_includes_supertype(self) -> None:
        supertype = ConcreteNode(cls=int)
        node = NewTypeNode(name="UserId", supertype=supertype)
        children = node.children()
        assert len(children) == 1
        assert supertype in children

    def test_signature_node_children_includes_params_returns_type_params(self) -> None:
        param_type = ConcreteNode(cls=int)
        return_type = ConcreteNode(cls=str)
        tv = TypeVarNode(name="T")
        node = SignatureNode(
            parameters=(Parameter(name="x", type=param_type),),
            returns=return_type,
            type_params=(tv,),
        )
        children = node.children()
        assert len(children) == 3
        assert param_type in children
        assert return_type in children
        assert tv in children

    def test_protocol_type_children_includes_methods_and_attributes(self) -> None:
        sig = SignatureNode(
            parameters=(Parameter(name="self", type=AnyNode()),),
            returns=AnyNode(),
        )
        attr = FieldDef(name="value", type=ConcreteNode(cls=int))
        node = ProtocolNode(
            name="MyProtocol",
            methods=(MethodSig(name="do_something", signature=sig),),
            attributes=(attr,),
        )
        children = node.children()
        assert len(children) == 2
        assert sig in children
        assert attr.type in children

    def test_function_node_children_includes_signature(self) -> None:
        sig = SignatureNode(
            parameters=(Parameter(name="x", type=ConcreteNode(cls=int)),),
            returns=ConcreteNode(cls=str),
        )
        node = FunctionNode(name="my_func", signature=sig)
        children = node.children()
        assert len(children) == 1
        assert sig in children

    def test_class_node_children_includes_all_components(self) -> None:
        tv = TypeVarNode(name="T")
        base = ConcreteNode(cls=object)
        sig = SignatureNode(
            parameters=(Parameter(name="self", type=AnyNode()),),
            returns=AnyNode(),
        )
        class_var = FieldDef(name="CLASS_VAR", type=ConcreteNode(cls=int))
        instance_var = FieldDef(name="instance_var", type=ConcreteNode(cls=str))
        node = ClassNode(
            cls=object,
            name="MyClass",
            type_params=(tv,),
            bases=(base,),
            methods=(MethodSig(name="method", signature=sig),),
            class_vars=(class_var,),
            instance_vars=(instance_var,),
        )
        children = node.children()
        assert tv in children
        assert base in children
        assert sig in children
        assert class_var.type in children
        assert instance_var.type in children
