from enum import Enum

from typing_graph import (
    AnyType,
    CallableType,
    ClassNode,
    ConcreteType,
    DataclassFieldDef,
    DataclassType,
    EllipsisType,
    EnumType,
    FieldDef,
    ForwardRef,
    FunctionNode,
    GenericAlias,
    GenericTypeNode,
    LiteralNode,
    MethodSig,
    NamedTupleType,
    NeverType,
    NewTypeNode,
    Parameter,
    ParamSpecNode,
    ProtocolType,
    RefState,
    SelfType,
    SignatureNode,
    SubscriptedGeneric,
    TupleType,
    TypeAliasNode,
    TypedDictType,
    TypeVarNode,
    TypeVarTupleNode,
    UnionType,
)
from typing_graph._node import (
    AnnotatedType,
    AttrsFieldDef,
    AttrsType,
    ConcatenateNode,
    DiscriminatedUnion,
    IntersectionType,
    LiteralStringType,
    MetaType,
    PydanticFieldDef,
    PydanticModelType,
    TypeGuardType,
    TypeIsType,
    UnpackNode,
    is_annotated_type_node,
    is_any_type_node,
    is_attrs_type_node,
    is_callable_type_node,
    is_class_node,
    is_concatenate_node,
    is_concrete_type,
    is_dataclass_type_node,
    is_discriminated_union_node,
    is_ellipsis_type_node,
    is_enum_type_node,
    is_forward_ref_node,
    is_function_node,
    is_generic_alias_node,
    is_generic_type,
    is_intersection_type_node,
    is_literal_node,
    is_literal_string_type_node,
    is_meta_type_node,
    is_method_sig,
    is_named_tuple_type_node,
    is_never_type_node,
    is_new_type_node,
    is_param_spec_node,
    is_protocol_type_node,
    is_pydantic_model_type_node,
    is_ref_state_failed,
    is_ref_state_resolved,
    is_ref_state_unresolved,
    is_self_type_node,
    is_signature_node,
    is_structured_type_node,
    is_subscripted_generic_node,
    is_tuple_type_node,
    is_type_alias_node,
    is_type_guard_type_node,
    is_type_is_type_node,
    is_type_node,
    is_type_var_node,
    is_type_var_tuple_node,
    is_typed_dict_type_node,
    is_union_type_node,
    is_unpack_node,
)


class TestTypeVarNode:
    def test_typevar_children_includes_bound(self) -> None:
        bound = ConcreteType(cls=int)
        node = TypeVarNode(name="T", bound=bound)
        assert bound in node.children()

    def test_typevar_children_includes_constraints(self) -> None:
        constraints = (ConcreteType(cls=int), ConcreteType(cls=str))
        node = TypeVarNode(name="T", constraints=constraints)
        children = node.children()
        assert constraints[0] in children
        assert constraints[1] in children


class TestUnionType:
    def test_union_children(self) -> None:
        members = (ConcreteType(cls=int), ConcreteType(cls=str))
        node = UnionType(members=members)
        assert len(node.children()) == 2


class TestTypeGuards:
    def test_is_type_node(self) -> None:
        assert is_type_node(ConcreteType(cls=int)) is True
        assert is_type_node(int) is False

    def test_is_concrete_type(self) -> None:
        assert is_concrete_type(ConcreteType(cls=int)) is True
        assert is_concrete_type(AnyType()) is False

    def test_is_any_type_node(self) -> None:
        assert is_any_type_node(AnyType()) is True
        assert is_any_type_node(ConcreteType(cls=int)) is False

    def test_is_never_type_node(self) -> None:
        assert is_never_type_node(NeverType()) is True
        assert is_never_type_node(AnyType()) is False

    def test_is_self_type_node(self) -> None:
        assert is_self_type_node(SelfType()) is True
        assert is_self_type_node(AnyType()) is False

    def test_is_type_var_node(self) -> None:
        assert is_type_var_node(TypeVarNode(name="T")) is True
        assert is_type_var_node(ConcreteType(cls=int)) is False

    def test_is_union_type_node(self) -> None:
        members = (ConcreteType(cls=int), ConcreteType(cls=str))
        assert is_union_type_node(UnionType(members=members)) is True
        assert is_union_type_node(ConcreteType(cls=int)) is False

    def test_is_tuple_type_node(self) -> None:
        elements = (ConcreteType(cls=int),)
        assert is_tuple_type_node(TupleType(elements=elements)) is True
        assert is_tuple_type_node(ConcreteType(cls=int)) is False

    def test_is_callable_type_node(self) -> None:
        params = (ConcreteType(cls=int),)
        returns = ConcreteType(cls=str)
        node = CallableType(params=params, returns=returns)
        assert is_callable_type_node(node) is True
        assert is_callable_type_node(ConcreteType(cls=int)) is False

    def test_is_literal_node(self) -> None:
        assert is_literal_node(LiteralNode(values=(1,))) is True
        assert is_literal_node(ConcreteType(cls=int)) is False

    def test_is_forward_ref_node(self) -> None:
        assert is_forward_ref_node(ForwardRef(ref="X")) is True
        assert is_forward_ref_node(ConcreteType(cls=int)) is False

    def test_is_subscripted_generic_node(self) -> None:
        origin = ConcreteType(cls=list)
        args = (ConcreteType(cls=int),)
        node = SubscriptedGeneric(origin=origin, args=args)
        assert is_subscripted_generic_node(node) is True
        assert is_subscripted_generic_node(ConcreteType(cls=int)) is False

    def test_is_type_var_tuple_node(self) -> None:
        assert is_type_var_tuple_node(TypeVarTupleNode(name="Ts")) is True
        assert is_type_var_tuple_node(TypeVarNode(name="T")) is False

    def test_is_param_spec_node(self) -> None:
        assert is_param_spec_node(ParamSpecNode(name="P")) is True
        assert is_param_spec_node(TypeVarNode(name="T")) is False

    def test_is_concatenate_node(self) -> None:
        prefix = (ConcreteType(cls=int),)
        param_spec = ParamSpecNode(name="P")
        node = ConcatenateNode(prefix=prefix, param_spec=param_spec)
        assert is_concatenate_node(node) is True
        assert is_concatenate_node(ConcreteType(cls=int)) is False

    def test_is_unpack_node(self) -> None:
        ts = TypeVarTupleNode(name="Ts")
        node = UnpackNode(target=ts)
        assert is_unpack_node(node) is True
        assert is_unpack_node(ConcreteType(cls=int)) is False

    def test_is_generic_type(self) -> None:
        assert is_generic_type(GenericTypeNode(cls=list)) is True
        assert is_generic_type(ConcreteType(cls=int)) is False

    def test_is_ellipsis_type_node(self) -> None:
        assert is_ellipsis_type_node(EllipsisType()) is True
        assert is_ellipsis_type_node(ConcreteType(cls=int)) is False

    def test_is_generic_alias_node(self) -> None:
        tv = TypeVarNode(name="T")
        node = GenericAlias(
            name="Vector",
            type_params=(tv,),
            value=SubscriptedGeneric(origin=GenericTypeNode(cls=list), args=(tv,)),
        )
        assert is_generic_alias_node(node) is True
        assert is_generic_alias_node(ConcreteType(cls=int)) is False

    def test_is_type_alias_node(self) -> None:
        node = TypeAliasNode(name="MyInt", value=ConcreteType(cls=int))
        assert is_type_alias_node(node) is True
        assert is_type_alias_node(ConcreteType(cls=int)) is False

    def test_is_discriminated_union_node(self) -> None:
        node = DiscriminatedUnion(
            discriminant="kind",
            variants={"a": ConcreteType(cls=dict), "b": ConcreteType(cls=list)},
        )
        assert is_discriminated_union_node(node) is True
        assert is_discriminated_union_node(UnionType(members=())) is False

    def test_is_intersection_type_node(self) -> None:
        node = IntersectionType(
            members=(ConcreteType(cls=dict), ConcreteType(cls=list))
        )
        assert is_intersection_type_node(node) is True
        assert is_intersection_type_node(UnionType(members=())) is False

    def test_is_named_tuple_type_node(self) -> None:
        node = NamedTupleType(
            name="Point",
            fields=(
                FieldDef(name="x", type=ConcreteType(cls=int)),
                FieldDef(name="y", type=ConcreteType(cls=int)),
            ),
        )
        assert is_named_tuple_type_node(node) is True
        assert is_named_tuple_type_node(TupleType(elements=())) is False

    def test_is_typed_dict_type_node(self) -> None:
        node = TypedDictType(
            name="MyDict",
            fields=(FieldDef(name="key", type=ConcreteType(cls=str)),),
        )
        assert is_typed_dict_type_node(node) is True
        assert is_typed_dict_type_node(ConcreteType(cls=dict)) is False

    def test_is_structured_type_node(self) -> None:
        td = TypedDictType(
            name="MyDict",
            fields=(FieldDef(name="key", type=ConcreteType(cls=str)),),
        )
        nt = NamedTupleType(
            name="Point",
            fields=(FieldDef(name="x", type=ConcreteType(cls=int)),),
        )
        assert is_structured_type_node(td) is True
        assert is_structured_type_node(nt) is True
        assert is_structured_type_node(ConcreteType(cls=dict)) is False

    def test_is_literal_string_type_node(self) -> None:
        assert is_literal_string_type_node(LiteralStringType()) is True
        assert is_literal_string_type_node(ConcreteType(cls=str)) is False

    def test_is_ref_state_resolved(self) -> None:
        resolved = RefState.Resolved(node=ConcreteType(cls=int))
        unresolved = RefState.Unresolved()
        failed = RefState.Failed(error="not found")
        assert is_ref_state_resolved(resolved) is True
        assert is_ref_state_resolved(unresolved) is False
        assert is_ref_state_resolved(failed) is False

    def test_is_ref_state_unresolved(self) -> None:
        resolved = RefState.Resolved(node=ConcreteType(cls=int))
        unresolved = RefState.Unresolved()
        failed = RefState.Failed(error="not found")
        assert is_ref_state_unresolved(unresolved) is True
        assert is_ref_state_unresolved(resolved) is False
        assert is_ref_state_unresolved(failed) is False

    def test_is_ref_state_failed(self) -> None:
        resolved = RefState.Resolved(node=ConcreteType(cls=int))
        unresolved = RefState.Unresolved()
        failed = RefState.Failed(error="not found")
        assert is_ref_state_failed(failed) is True
        assert is_ref_state_failed(resolved) is False
        assert is_ref_state_failed(unresolved) is False

    def test_is_annotated_type_node(self) -> None:
        node = AnnotatedType(base=ConcreteType(cls=int), annotations=("metadata",))
        assert is_annotated_type_node(node) is True
        assert is_annotated_type_node(ConcreteType(cls=int)) is False

    def test_is_meta_type_node(self) -> None:
        node = MetaType(of=ConcreteType(cls=int))
        assert is_meta_type_node(node) is True
        assert is_meta_type_node(ConcreteType(cls=type)) is False

    def test_is_type_guard_type_node(self) -> None:
        node = TypeGuardType(narrows_to=ConcreteType(cls=int))
        assert is_type_guard_type_node(node) is True
        assert is_type_guard_type_node(ConcreteType(cls=bool)) is False

    def test_is_type_is_type_node(self) -> None:
        node = TypeIsType(narrows_to=ConcreteType(cls=int))
        assert is_type_is_type_node(node) is True
        assert is_type_is_type_node(ConcreteType(cls=bool)) is False

    def test_is_dataclass_type_node(self) -> None:
        node = DataclassType(
            cls=object,
            fields=(DataclassFieldDef(name="x", type=ConcreteType(cls=int)),),
        )
        assert is_dataclass_type_node(node) is True
        assert is_dataclass_type_node(ConcreteType(cls=object)) is False

    def test_is_attrs_type_node(self) -> None:
        node = AttrsType(
            cls=object,
            fields=(AttrsFieldDef(name="x", type=ConcreteType(cls=int)),),
        )
        assert is_attrs_type_node(node) is True
        assert is_attrs_type_node(ConcreteType(cls=object)) is False

    def test_is_pydantic_model_type_node(self) -> None:
        node = PydanticModelType(
            cls=object,
            fields=(PydanticFieldDef(name="x", type=ConcreteType(cls=int)),),
        )
        assert is_pydantic_model_type_node(node) is True
        assert is_pydantic_model_type_node(ConcreteType(cls=object)) is False

    def test_is_enum_type_node(self) -> None:
        class Color(Enum):
            RED = 1
            GREEN = 2

        node = EnumType(
            cls=Color,
            value_type=ConcreteType(cls=int),
            members=(("RED", 1), ("GREEN", 2)),
        )
        assert is_enum_type_node(node) is True
        assert is_enum_type_node(ConcreteType(cls=Enum)) is False

    def test_is_new_type_node(self) -> None:
        node = NewTypeNode(name="UserId", supertype=ConcreteType(cls=int))
        assert is_new_type_node(node) is True
        assert is_new_type_node(ConcreteType(cls=int)) is False

    def test_is_signature_node(self) -> None:
        node = SignatureNode(
            parameters=(Parameter(name="x", type=ConcreteType(cls=int)),),
            returns=ConcreteType(cls=str),
        )
        assert is_signature_node(node) is True
        assert is_signature_node(CallableType(params=(), returns=AnyType())) is False

    def test_is_method_sig(self) -> None:
        sig = SignatureNode(
            parameters=(Parameter(name="self", type=AnyType()),),
            returns=ConcreteType(cls=type(None)),
        )
        node = MethodSig(name="my_method", signature=sig)
        assert is_method_sig(node) is True
        assert is_method_sig(sig) is False

    def test_is_protocol_type_node(self) -> None:
        sig = SignatureNode(
            parameters=(Parameter(name="self", type=AnyType()),),
            returns=AnyType(),
        )
        node = ProtocolType(
            name="MyProtocol",
            methods=(MethodSig(name="do_something", signature=sig),),
        )
        assert is_protocol_type_node(node) is True
        assert is_protocol_type_node(ConcreteType(cls=object)) is False

    def test_is_function_node(self) -> None:
        sig = SignatureNode(
            parameters=(Parameter(name="x", type=ConcreteType(cls=int)),),
            returns=ConcreteType(cls=str),
        )
        node = FunctionNode(name="my_func", signature=sig)
        assert is_function_node(node) is True
        assert is_function_node(sig) is False

    def test_is_class_node(self) -> None:
        node = ClassNode(cls=object, name="MyClass")
        assert is_class_node(node) is True
        assert is_class_node(ConcreteType(cls=type)) is False


class TestNodeChildrenMethods:
    def test_typevar_with_default_includes_default_in_children(self) -> None:
        default = ConcreteType(cls=str)
        node = TypeVarNode(name="T", default=default)
        assert default in node.children()

    def test_paramspec_with_default_includes_default_in_children(self) -> None:
        default = ConcreteType(cls=int)
        node = ParamSpecNode(name="P", default=default)
        children = node.children()
        assert len(children) == 1
        assert default in children

    def test_paramspec_without_default_has_empty_children(self) -> None:
        node = ParamSpecNode(name="P")
        assert node.children() == ()

    def test_typevartuple_with_default_includes_default_in_children(self) -> None:
        default = TupleType(elements=(ConcreteType(cls=int),))
        node = TypeVarTupleNode(name="Ts", default=default)
        children = node.children()
        assert len(children) == 1
        assert default in children

    def test_typevartuple_without_default_has_empty_children(self) -> None:
        node = TypeVarTupleNode(name="Ts")
        assert node.children() == ()

    def test_concatenate_children_includes_prefix_and_paramspec(self) -> None:
        prefix1 = ConcreteType(cls=int)
        prefix2 = ConcreteType(cls=str)
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
        node = LiteralStringType()
        assert node.children() == ()

    def test_forward_ref_resolved_includes_node_in_children(self) -> None:
        resolved_node = ConcreteType(cls=int)
        state = RefState.Resolved(node=resolved_node)
        node = ForwardRef(ref="SomeClass", state=state)
        children = node.children()
        assert len(children) == 1
        assert resolved_node in children

    def test_forward_ref_unresolved_has_empty_children(self) -> None:
        node = ForwardRef(ref="SomeClass", state=RefState.Unresolved())
        assert node.children() == ()

    def test_forward_ref_failed_has_empty_children(self) -> None:
        node = ForwardRef(ref="SomeClass", state=RefState.Failed(error="Not found"))
        assert node.children() == ()

    def test_subscripted_generic_children_includes_origin_and_args(self) -> None:
        origin = GenericTypeNode(cls=list)
        arg = ConcreteType(cls=int)
        node = SubscriptedGeneric(origin=origin, args=(arg,))
        children = node.children()
        assert len(children) == 2
        assert origin in children
        assert arg in children

    def test_generic_alias_children_includes_type_params_and_value(self) -> None:
        tv = TypeVarNode(name="T")
        value = SubscriptedGeneric(origin=GenericTypeNode(cls=list), args=(tv,))
        node = GenericAlias(name="Vector", type_params=(tv,), value=value)
        children = node.children()
        assert len(children) == 2
        assert tv in children
        assert value in children

    def test_type_alias_children_includes_value(self) -> None:
        value = ConcreteType(cls=int)
        node = TypeAliasNode(name="MyInt", value=value)
        children = node.children()
        assert len(children) == 1
        assert value in children

    def test_discriminated_union_children_includes_variants(self) -> None:
        variant_a = ConcreteType(cls=dict)
        variant_b = ConcreteType(cls=list)
        node = DiscriminatedUnion(
            discriminant="kind", variants={"a": variant_a, "b": variant_b}
        )
        children = node.children()
        assert len(children) == 2
        assert variant_a in children
        assert variant_b in children

    def test_intersection_type_children_includes_members(self) -> None:
        member1 = ConcreteType(cls=dict)
        member2 = ConcreteType(cls=list)
        node = IntersectionType(members=(member1, member2))
        children = node.children()
        assert len(children) == 2
        assert member1 in children
        assert member2 in children

    def test_callable_with_paramspec_children(self) -> None:
        ps = ParamSpecNode(name="P")
        returns = ConcreteType(cls=str)
        node = CallableType(params=ps, returns=returns)
        children = node.children()
        assert len(children) == 2
        assert ps in children
        assert returns in children

    def test_callable_with_ellipsis_children(self) -> None:
        ellipsis = EllipsisType()
        returns = ConcreteType(cls=str)
        node = CallableType(params=ellipsis, returns=returns)
        children = node.children()
        assert len(children) == 2
        assert ellipsis in children
        assert returns in children

    def test_tuple_type_children_includes_elements(self) -> None:
        elem1 = ConcreteType(cls=int)
        elem2 = ConcreteType(cls=str)
        node = TupleType(elements=(elem1, elem2))
        children = node.children()
        assert len(children) == 2
        assert elem1 in children
        assert elem2 in children

    def test_annotated_type_children_includes_base(self) -> None:
        base = ConcreteType(cls=int)
        node = AnnotatedType(base=base, annotations=("metadata",))
        children = node.children()
        assert len(children) == 1
        assert base in children

    def test_meta_type_children_includes_of(self) -> None:
        of_type = ConcreteType(cls=int)
        node = MetaType(of=of_type)
        children = node.children()
        assert len(children) == 1
        assert of_type in children

    def test_type_guard_type_children_includes_narrows_to(self) -> None:
        narrows_to = ConcreteType(cls=int)
        node = TypeGuardType(narrows_to=narrows_to)
        children = node.children()
        assert len(children) == 1
        assert narrows_to in children

    def test_type_is_type_children_includes_narrows_to(self) -> None:
        narrows_to = ConcreteType(cls=int)
        node = TypeIsType(narrows_to=narrows_to)
        children = node.children()
        assert len(children) == 1
        assert narrows_to in children

    def test_typed_dict_type_children_includes_field_types(self) -> None:
        field1 = FieldDef(name="a", type=ConcreteType(cls=int))
        field2 = FieldDef(name="b", type=ConcreteType(cls=str))
        node = TypedDictType(name="MyDict", fields=(field1, field2))
        children = node.children()
        assert len(children) == 2
        assert field1.type in children
        assert field2.type in children

    def test_typed_dict_get_fields(self) -> None:
        field1 = FieldDef(name="a", type=ConcreteType(cls=int))
        field2 = FieldDef(name="b", type=ConcreteType(cls=str))
        node = TypedDictType(name="MyDict", fields=(field1, field2))
        fields = node.get_fields()
        assert len(fields) == 2
        assert field1 in fields
        assert field2 in fields

    def test_named_tuple_type_children_includes_field_types(self) -> None:
        field1 = FieldDef(name="x", type=ConcreteType(cls=int))
        field2 = FieldDef(name="y", type=ConcreteType(cls=int))
        node = NamedTupleType(name="Point", fields=(field1, field2))
        children = node.children()
        assert len(children) == 2
        assert field1.type in children
        assert field2.type in children

    def test_named_tuple_get_fields(self) -> None:
        field1 = FieldDef(name="x", type=ConcreteType(cls=int))
        field2 = FieldDef(name="y", type=ConcreteType(cls=int))
        node = NamedTupleType(name="Point", fields=(field1, field2))
        fields = node.get_fields()
        assert len(fields) == 2
        assert field1 in fields
        assert field2 in fields

    def test_dataclass_type_children_includes_field_types(self) -> None:
        field1 = DataclassFieldDef(name="x", type=ConcreteType(cls=int))
        field2 = DataclassFieldDef(name="y", type=ConcreteType(cls=str))
        node = DataclassType(cls=object, fields=(field1, field2))
        children = node.children()
        assert len(children) == 2
        assert field1.type in children
        assert field2.type in children

    def test_dataclass_type_get_fields(self) -> None:
        field1 = DataclassFieldDef(name="x", type=ConcreteType(cls=int))
        field2 = DataclassFieldDef(name="y", type=ConcreteType(cls=str))
        node = DataclassType(cls=object, fields=(field1, field2))
        fields = node.get_fields()
        assert len(fields) == 2
        assert field1 in fields
        assert field2 in fields

    def test_attrs_type_children_includes_field_types(self) -> None:
        field1 = AttrsFieldDef(name="x", type=ConcreteType(cls=int))
        field2 = AttrsFieldDef(name="y", type=ConcreteType(cls=str))
        node = AttrsType(cls=object, fields=(field1, field2))
        children = node.children()
        assert len(children) == 2
        assert field1.type in children
        assert field2.type in children

    def test_attrs_type_get_fields(self) -> None:
        field1 = AttrsFieldDef(name="x", type=ConcreteType(cls=int))
        field2 = AttrsFieldDef(name="y", type=ConcreteType(cls=str))
        node = AttrsType(cls=object, fields=(field1, field2))
        fields = node.get_fields()
        assert len(fields) == 2
        assert field1 in fields
        assert field2 in fields

    def test_pydantic_model_type_children_includes_field_types(self) -> None:
        field1 = PydanticFieldDef(name="x", type=ConcreteType(cls=int))
        field2 = PydanticFieldDef(name="y", type=ConcreteType(cls=str))
        node = PydanticModelType(cls=object, fields=(field1, field2))
        children = node.children()
        assert len(children) == 2
        assert field1.type in children
        assert field2.type in children

    def test_pydantic_model_type_get_fields(self) -> None:
        field1 = PydanticFieldDef(name="x", type=ConcreteType(cls=int))
        field2 = PydanticFieldDef(name="y", type=ConcreteType(cls=str))
        node = PydanticModelType(cls=object, fields=(field1, field2))
        fields = node.get_fields()
        assert len(fields) == 2
        assert field1 in fields
        assert field2 in fields

    def test_enum_type_children_includes_value_type(self) -> None:
        class Color(Enum):
            RED = 1

        value_type = ConcreteType(cls=int)
        node = EnumType(cls=Color, value_type=value_type, members=(("RED", 1),))
        children = node.children()
        assert len(children) == 1
        assert value_type in children

    def test_new_type_node_children_includes_supertype(self) -> None:
        supertype = ConcreteType(cls=int)
        node = NewTypeNode(name="UserId", supertype=supertype)
        children = node.children()
        assert len(children) == 1
        assert supertype in children

    def test_signature_node_children_includes_params_returns_type_params(self) -> None:
        param_type = ConcreteType(cls=int)
        return_type = ConcreteType(cls=str)
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
            parameters=(Parameter(name="self", type=AnyType()),),
            returns=AnyType(),
        )
        attr = FieldDef(name="value", type=ConcreteType(cls=int))
        node = ProtocolType(
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
            parameters=(Parameter(name="x", type=ConcreteType(cls=int)),),
            returns=ConcreteType(cls=str),
        )
        node = FunctionNode(name="my_func", signature=sig)
        children = node.children()
        assert len(children) == 1
        assert sig in children

    def test_class_node_children_includes_all_components(self) -> None:
        tv = TypeVarNode(name="T")
        base = ConcreteType(cls=object)
        sig = SignatureNode(
            parameters=(Parameter(name="self", type=AnyType()),),
            returns=AnyType(),
        )
        class_var = FieldDef(name="CLASS_VAR", type=ConcreteType(cls=int))
        instance_var = FieldDef(name="instance_var", type=ConcreteType(cls=str))
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
