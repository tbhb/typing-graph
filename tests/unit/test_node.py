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


class TestForwardRefNodeResolved:
    def test_resolved_returns_target_for_single_ref(self) -> None:
        target = ConcreteNode(cls=int)
        ref = ForwardRefNode(ref="int", state=RefResolved(node=target))

        assert ref.resolved() is target

    def test_resolved_traverses_chain_of_refs(self) -> None:
        target = ConcreteNode(cls=int)
        inner = ForwardRefNode(ref="int", state=RefResolved(node=target))
        outer = ForwardRefNode(ref="Inner", state=RefResolved(node=inner))

        assert outer.resolved() is target

    def test_resolved_returns_self_for_unresolved(self) -> None:
        ref = ForwardRefNode(ref="X", state=RefUnresolved())

        assert ref.resolved() is ref

    def test_resolved_returns_self_for_failed(self) -> None:
        ref = ForwardRefNode(ref="X", state=RefFailed(error="not found"))

        assert ref.resolved() is ref

    def test_resolved_detects_cycle_via_artificial_mutation(self) -> None:
        # Create a cycle by artificially mutating the frozen dataclass
        # This tests the defensive cycle detection code path
        target = ConcreteNode(cls=int)
        ref_a = ForwardRefNode(ref="A", state=RefResolved(node=target))

        # Now artificially create a cycle: ref_a -> ref_a
        # This can't happen in normal usage but tests the defensive code
        cyclic_state = RefResolved(node=ref_a)
        object.__setattr__(ref_a, "state", cyclic_state)

        # When resolved() is called, it should detect the cycle and return ref_a
        result = ref_a.resolved()
        assert result is ref_a  # Cycle detected, returns the cycling node

    def test_resolved_stops_at_unresolved_in_chain(self) -> None:
        unresolved = ForwardRefNode(ref="Unknown", state=RefUnresolved())
        middle = ForwardRefNode(ref="Middle", state=RefResolved(node=unresolved))
        outer = ForwardRefNode(ref="Outer", state=RefResolved(node=middle))

        result = outer.resolved()

        assert result is unresolved
        assert isinstance(result, ForwardRefNode)
        assert isinstance(result.state, RefUnresolved)

    def test_resolved_stops_at_failed_in_chain(self) -> None:
        failed = ForwardRefNode(ref="Bad", state=RefFailed(error="not found"))
        middle = ForwardRefNode(ref="Middle", state=RefResolved(node=failed))
        outer = ForwardRefNode(ref="Outer", state=RefResolved(node=middle))

        result = outer.resolved()

        assert result is failed
        assert isinstance(result, ForwardRefNode)
        assert isinstance(result.state, RefFailed)

    def test_resolved_handles_long_chain(self) -> None:
        target = ConcreteNode(cls=str)
        current: TypeNode = target
        for i in range(10):
            current = ForwardRefNode(ref=f"Ref{i}", state=RefResolved(node=current))

        result = current.resolved()

        assert result is target

    def test_resolved_preserves_different_target_types(self) -> None:
        # Test with various target types
        targets = [
            ConcreteNode(cls=int),
            AnyNode(),
            NeverNode(),
            UnionNode(members=(ConcreteNode(cls=int), ConcreteNode(cls=str))),
        ]

        for target in targets:
            ref = ForwardRefNode(ref="X", state=RefResolved(node=target))
            assert ref.resolved() is target
