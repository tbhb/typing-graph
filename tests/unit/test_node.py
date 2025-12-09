from enum import Enum
from typing import TYPE_CHECKING

import pytest

from typing_graph import (
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
    TypeGuardNode,
    TypeIsNode,
    TypeNode,
    TypeVarNode,
    TypeVarTupleNode,
    UnionNode,
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
    is_type_param_node,
    is_type_var_node,
    is_type_var_tuple_node,
    is_typed_dict_node,
    is_union_type_node,
    is_unpack_node,
)

if TYPE_CHECKING:
    from collections.abc import Callable


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
    @pytest.mark.parametrize(
        ("guard_func", "node_true", "node_false"),
        [
            pytest.param(
                is_type_node,
                ConcreteNode(cls=int),
                int,
                id="is_type_node",
            ),
            pytest.param(
                is_concrete_node,
                ConcreteNode(cls=int),
                AnyNode(),
                id="is_concrete_node",
            ),
            pytest.param(
                is_any_node,
                AnyNode(),
                ConcreteNode(cls=int),
                id="is_any_node",
            ),
            pytest.param(
                is_never_node,
                NeverNode(),
                AnyNode(),
                id="is_never_node",
            ),
            pytest.param(
                is_self_node,
                SelfNode(),
                AnyNode(),
                id="is_self_node",
            ),
            pytest.param(
                is_type_var_node,
                TypeVarNode(name="T"),
                ConcreteNode(cls=int),
                id="is_type_var_node",
            ),
            pytest.param(
                is_union_type_node,
                UnionNode(members=(ConcreteNode(cls=int), ConcreteNode(cls=str))),
                ConcreteNode(cls=int),
                id="is_union_type_node",
            ),
            pytest.param(
                is_tuple_node,
                TupleNode(elements=(ConcreteNode(cls=int),)),
                ConcreteNode(cls=int),
                id="is_tuple_node",
            ),
            pytest.param(
                is_callable_node,
                CallableNode(
                    params=(ConcreteNode(cls=int),), returns=ConcreteNode(cls=str)
                ),
                ConcreteNode(cls=int),
                id="is_callable_node",
            ),
            pytest.param(
                is_literal_node,
                LiteralNode(values=(1,)),
                ConcreteNode(cls=int),
                id="is_literal_node",
            ),
            pytest.param(
                is_forward_ref_node,
                ForwardRefNode(ref="X"),
                ConcreteNode(cls=int),
                id="is_forward_ref_node",
            ),
            pytest.param(
                is_subscripted_generic_node,
                SubscriptedGenericNode(
                    origin=ConcreteNode(cls=list),
                    args=(ConcreteNode(cls=int),),
                ),
                ConcreteNode(cls=int),
                id="is_subscripted_generic_node",
            ),
            pytest.param(
                is_type_var_tuple_node,
                TypeVarTupleNode(name="Ts"),
                TypeVarNode(name="T"),
                id="is_type_var_tuple_node",
            ),
            pytest.param(
                is_param_spec_node,
                ParamSpecNode(name="P"),
                TypeVarNode(name="T"),
                id="is_param_spec_node",
            ),
            pytest.param(
                is_concatenate_node,
                ConcatenateNode(
                    prefix=(ConcreteNode(cls=int),),
                    param_spec=ParamSpecNode(name="P"),
                ),
                ConcreteNode(cls=int),
                id="is_concatenate_node",
            ),
            pytest.param(
                is_unpack_node,
                UnpackNode(target=TypeVarTupleNode(name="Ts")),
                ConcreteNode(cls=int),
                id="is_unpack_node",
            ),
            pytest.param(
                is_generic_node,
                GenericTypeNode(cls=list),
                ConcreteNode(cls=int),
                id="is_generic_node",
            ),
            pytest.param(
                is_ellipsis_node,
                EllipsisNode(),
                ConcreteNode(cls=int),
                id="is_ellipsis_node",
            ),
            pytest.param(
                is_generic_alias_node,
                GenericAliasNode(
                    name="Vector",
                    type_params=(TypeVarNode(name="T"),),
                    value=SubscriptedGenericNode(
                        origin=GenericTypeNode(cls=list),
                        args=(TypeVarNode(name="T"),),
                    ),
                ),
                ConcreteNode(cls=int),
                id="is_generic_alias_node",
            ),
            pytest.param(
                is_type_alias_node,
                TypeAliasNode(name="MyInt", value=ConcreteNode(cls=int)),
                ConcreteNode(cls=int),
                id="is_type_alias_node",
            ),
            pytest.param(
                is_discriminated_union_node,
                DiscriminatedUnionNode(
                    discriminant="kind",
                    variants={"a": ConcreteNode(cls=dict), "b": ConcreteNode(cls=list)},
                ),
                UnionNode(members=()),
                id="is_discriminated_union_node",
            ),
            pytest.param(
                is_intersection_node,
                IntersectionNode(
                    members=(ConcreteNode(cls=dict), ConcreteNode(cls=list))
                ),
                UnionNode(members=()),
                id="is_intersection_node",
            ),
            pytest.param(
                is_named_tuple_node,
                NamedTupleNode(
                    name="Point",
                    fields=(
                        FieldDef(name="x", type=ConcreteNode(cls=int)),
                        FieldDef(name="y", type=ConcreteNode(cls=int)),
                    ),
                ),
                TupleNode(elements=()),
                id="is_named_tuple_node",
            ),
            pytest.param(
                is_typed_dict_node,
                TypedDictNode(
                    name="MyDict",
                    fields=(FieldDef(name="key", type=ConcreteNode(cls=str)),),
                ),
                ConcreteNode(cls=dict),
                id="is_typed_dict_node",
            ),
            pytest.param(
                is_literal_string_node,
                LiteralStringNode(),
                ConcreteNode(cls=str),
                id="is_literal_string_node",
            ),
            pytest.param(
                is_annotated_node,
                AnnotatedNode(base=ConcreteNode(cls=int), annotations=("metadata",)),
                ConcreteNode(cls=int),
                id="is_annotated_node",
            ),
            pytest.param(
                is_meta_node,
                MetaNode(of=ConcreteNode(cls=int)),
                ConcreteNode(cls=type),
                id="is_meta_node",
            ),
            pytest.param(
                is_type_guard_node,
                TypeGuardNode(narrows_to=ConcreteNode(cls=int)),
                ConcreteNode(cls=bool),
                id="is_type_guard_node",
            ),
            pytest.param(
                is_type_is_node,
                TypeIsNode(narrows_to=ConcreteNode(cls=int)),
                ConcreteNode(cls=bool),
                id="is_type_is_node",
            ),
            pytest.param(
                is_dataclass_node,
                DataclassNode(
                    cls=object,
                    fields=(DataclassFieldDef(name="x", type=ConcreteNode(cls=int)),),
                ),
                ConcreteNode(cls=object),
                id="is_dataclass_node",
            ),
            pytest.param(
                is_enum_node,
                EnumNode(
                    cls=Enum,
                    value_type=ConcreteNode(cls=int),
                    members=(("RED", 1), ("GREEN", 2)),
                ),
                ConcreteNode(cls=Enum),
                id="is_enum_node",
            ),
            pytest.param(
                is_new_type_node,
                NewTypeNode(name="UserId", supertype=ConcreteNode(cls=int)),
                ConcreteNode(cls=int),
                id="is_new_type_node",
            ),
            pytest.param(
                is_signature_node,
                SignatureNode(
                    parameters=(Parameter(name="x", type=ConcreteNode(cls=int)),),
                    returns=ConcreteNode(cls=str),
                ),
                CallableNode(params=(), returns=AnyNode()),
                id="is_signature_node",
            ),
            pytest.param(
                is_method_sig,
                MethodSig(
                    name="my_method",
                    signature=SignatureNode(
                        parameters=(Parameter(name="self", type=AnyNode()),),
                        returns=ConcreteNode(cls=type(None)),
                    ),
                ),
                SignatureNode(
                    parameters=(Parameter(name="self", type=AnyNode()),),
                    returns=ConcreteNode(cls=type(None)),
                ),
                id="is_method_sig",
            ),
            pytest.param(
                is_protocol_node,
                ProtocolNode(
                    name="MyProtocol",
                    methods=(
                        MethodSig(
                            name="do_something",
                            signature=SignatureNode(
                                parameters=(Parameter(name="self", type=AnyNode()),),
                                returns=AnyNode(),
                            ),
                        ),
                    ),
                ),
                ConcreteNode(cls=object),
                id="is_protocol_node",
            ),
            pytest.param(
                is_function_node,
                FunctionNode(
                    name="my_func",
                    signature=SignatureNode(
                        parameters=(Parameter(name="x", type=ConcreteNode(cls=int)),),
                        returns=ConcreteNode(cls=str),
                    ),
                ),
                SignatureNode(
                    parameters=(Parameter(name="x", type=ConcreteNode(cls=int)),),
                    returns=ConcreteNode(cls=str),
                ),
                id="is_function_node",
            ),
            pytest.param(
                is_class_node,
                ClassNode(cls=object, name="MyClass"),
                ConcreteNode(cls=type),
                id="is_class_node",
            ),
        ],
    )
    def test_type_guards(
        self,
        guard_func: "Callable[[object], bool]",
        node_true: object,
        node_false: object,
    ) -> None:
        assert guard_func(node_true) is True
        assert guard_func(node_false) is False

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


class TestIsTypeParamNode:
    def test_returns_true_for_typevar_node(self) -> None:
        node = TypeVarNode(name="T")

        assert is_type_param_node(node) is True

    def test_returns_true_for_paramspec_node(self) -> None:
        node = ParamSpecNode(name="P")

        assert is_type_param_node(node) is True

    def test_returns_true_for_typevartuple_node(self) -> None:
        node = TypeVarTupleNode(name="Ts")

        assert is_type_param_node(node) is True

    def test_returns_false_for_concrete_type(self) -> None:
        node = ConcreteNode(cls=int)

        assert is_type_param_node(node) is False

    def test_returns_false_for_annotated_type(self) -> None:
        node = AnnotatedNode(base=ConcreteNode(cls=int), annotations=("meta",))

        assert is_type_param_node(node) is False
