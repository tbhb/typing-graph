import sys
from functools import wraps
from typing import TYPE_CHECKING, Annotated, TypeVar

import pytest

from typing_graph import (
    EvalMode,
    InspectConfig,
    inspect_function,
    inspect_signature,
)
from typing_graph._node import (
    ForwardRefNode,
    RefResolved,
    is_any_node,
    is_forward_ref_node,
    is_function_node,
    is_signature_node,
)

from tests.conftest import assert_concrete_type, assert_subscripted_generic

if TYPE_CHECKING:
    from collections.abc import Generator


def simple_function(x: int, y: str) -> bool:
    return bool(x) and bool(y)


# Test fixture: intentionally missing return type annotation
def no_return_annotation(x: int, y: str):  # type: ignore[return-type]
    return str(x) + y


# Test fixture: intentionally missing all annotations to test unannotated
# function handling
def no_annotations(x, y):  # pyright: ignore[reportUnknownParameterType,reportMissingParameterType]
    return x + y  # pyright: ignore[reportUnknownVariableType]


def with_defaults(x: int = 10, y: str = "default") -> str:
    return f"{x}: {y}"


def with_args(*args: int, **kwargs: str) -> None:
    pass


def positional_only(x: int, /, y: str) -> None:
    pass


def keyword_only(x: int, *, y: str) -> None:
    pass


def mixed_kinds(x: int, /, y: str, *args: float, z: bool, **kwargs: int) -> None:
    pass


async def async_function(x: int) -> str:
    return str(x)


def generator_function(n: int) -> "Generator[int, None, None]":
    yield from range(n)


def returns_none_explicit(x: int) -> None:
    pass


def returns_list(items: list[int]) -> list[str]:
    return [str(i) for i in items]


def with_annotated(x: Annotated[int, "metadata"]) -> int:
    return x


def decorated_function_original(x: int) -> str:
    return str(x)


def create_decorated_function():
    @wraps(decorated_function_original)
    def wrapper(x: int) -> str:
        return decorated_function_original(x)

    return wrapper


decorated_function = create_decorated_function()


class MyClass:
    def instance_method(self, x: int) -> str:
        return str(x)

    @classmethod
    def class_method(cls, x: int) -> str:
        return str(x)

    @staticmethod
    def static_method(x: int) -> str:
        return str(x)


class TestFunctionNode:
    def test_simple_function_has_name_and_signature(self) -> None:
        result = inspect_function(simple_function)

        assert is_function_node(result)
        assert result.name == "simple_function"
        assert is_signature_node(result.signature)

    def test_simple_function_is_not_async(self) -> None:
        result = inspect_function(simple_function)

        assert is_function_node(result)
        assert result.is_async is False

    def test_simple_function_is_not_generator(self) -> None:
        result = inspect_function(simple_function)

        assert is_function_node(result)
        assert result.is_generator is False

    def test_async_function_sets_is_async_true(self) -> None:
        result = inspect_function(async_function)

        assert is_function_node(result)
        assert result.name == "async_function"
        assert result.is_async is True
        assert result.is_generator is False

    def test_async_function_includes_async_in_decorators(self) -> None:
        result = inspect_function(async_function)

        assert is_function_node(result)
        assert "async" in result.decorators

    def test_generator_function_sets_is_generator_true(self) -> None:
        result = inspect_function(generator_function)

        assert is_function_node(result)
        assert result.name == "generator_function"
        assert result.is_generator is True
        assert result.is_async is False

    def test_function_children_returns_signature(self) -> None:
        result = inspect_function(simple_function)

        assert is_function_node(result)
        children = result.children()
        assert len(children) == 1
        assert children[0] is result.signature


class TestSignatureNode:
    def test_simple_signature_has_parameters_and_returns(self) -> None:
        result = inspect_signature(simple_function)

        assert is_signature_node(result)
        assert len(result.parameters) == 2
        assert result.returns is not None

    def test_parameter_names_captured_in_order(self) -> None:
        result = inspect_signature(simple_function)

        assert is_signature_node(result)
        assert result.parameters[0].name == "x"
        assert result.parameters[1].name == "y"

    def test_parameter_types_are_concrete(self) -> None:
        result = inspect_signature(simple_function)

        assert is_signature_node(result)
        _ = assert_concrete_type(result.parameters[0].type, int)
        _ = assert_concrete_type(result.parameters[1].type, str)

    def test_return_type_is_concrete(self) -> None:
        result = inspect_signature(simple_function)

        assert is_signature_node(result)
        _ = assert_concrete_type(result.returns, bool)

    def test_none_return_type_inspected(self) -> None:
        result = inspect_signature(returns_none_explicit)

        assert is_signature_node(result)
        _ = assert_concrete_type(result.returns, type(None))

    def test_generic_return_type_inspected(self) -> None:
        result = inspect_signature(returns_list)

        assert is_signature_node(result)
        _ = assert_subscripted_generic(result.returns, list)

    def test_signature_children_includes_param_types_and_returns(self) -> None:
        result = inspect_signature(simple_function)

        assert is_signature_node(result)
        children = result.children()
        assert len(children) >= 3
        assert result.parameters[0].type in children
        assert result.parameters[1].type in children
        assert result.returns in children


class TestParameterDetails:
    def test_parameter_default_captured(self) -> None:
        result = inspect_signature(with_defaults)

        assert is_signature_node(result)
        x_param = result.parameters[0]
        y_param = result.parameters[1]

        assert x_param.has_default is True
        assert x_param.default == 10
        assert y_param.has_default is True
        assert y_param.default == "default"

    def test_parameter_no_default_sets_has_default_false(self) -> None:
        result = inspect_signature(simple_function)

        assert is_signature_node(result)
        assert result.parameters[0].has_default is False
        assert result.parameters[0].default is None

    def test_parameter_kind_positional_or_keyword(self) -> None:
        result = inspect_signature(simple_function)

        assert is_signature_node(result)
        assert result.parameters[0].kind == "POSITIONAL_OR_KEYWORD"
        assert result.parameters[1].kind == "POSITIONAL_OR_KEYWORD"

    def test_parameter_kind_positional_only(self) -> None:
        result = inspect_signature(positional_only)

        assert is_signature_node(result)
        x_param = result.parameters[0]
        y_param = result.parameters[1]

        assert x_param.kind == "POSITIONAL_ONLY"
        assert y_param.kind == "POSITIONAL_OR_KEYWORD"

    def test_parameter_kind_keyword_only(self) -> None:
        result = inspect_signature(keyword_only)

        assert is_signature_node(result)
        x_param = result.parameters[0]
        y_param = result.parameters[1]

        assert x_param.kind == "POSITIONAL_OR_KEYWORD"
        assert y_param.kind == "KEYWORD_ONLY"

    def test_parameter_kind_var_positional(self) -> None:
        result = inspect_signature(with_args)

        assert is_signature_node(result)
        args_param = result.parameters[0]
        kwargs_param = result.parameters[1]

        assert args_param.name == "args"
        assert args_param.kind == "VAR_POSITIONAL"
        assert kwargs_param.name == "kwargs"
        assert kwargs_param.kind == "VAR_KEYWORD"

    def test_mixed_parameter_kinds(self) -> None:
        result = inspect_signature(mixed_kinds)

        assert is_signature_node(result)
        param_kinds = {p.name: p.kind for p in result.parameters}

        assert param_kinds["x"] == "POSITIONAL_ONLY"
        assert param_kinds["y"] == "POSITIONAL_OR_KEYWORD"
        assert param_kinds["args"] == "VAR_POSITIONAL"
        assert param_kinds["z"] == "KEYWORD_ONLY"
        assert param_kinds["kwargs"] == "VAR_KEYWORD"

    def test_var_positional_type_is_int(self) -> None:
        result = inspect_signature(with_args)

        assert is_signature_node(result)
        args_param = result.parameters[0]
        _ = assert_concrete_type(args_param.type, int)

    def test_var_keyword_type_is_str(self) -> None:
        result = inspect_signature(with_args)

        assert is_signature_node(result)
        kwargs_param = result.parameters[1]
        _ = assert_concrete_type(kwargs_param.type, str)


class TestUnannotatedFunctions:
    def test_no_return_annotation_returns_any(self) -> None:
        result = inspect_signature(no_return_annotation)

        assert is_signature_node(result)
        assert is_any_node(result.returns)

    def test_no_parameter_annotation_returns_any(self) -> None:
        result = inspect_signature(no_annotations)  # pyright: ignore[reportUnknownArgumentType]

        assert is_signature_node(result)
        assert is_any_node(result.parameters[0].type)
        assert is_any_node(result.parameters[1].type)


class TestMethodInspection:
    def test_instance_method_captures_self(self) -> None:
        result = inspect_function(MyClass.instance_method)

        assert is_function_node(result)
        assert result.name == "instance_method"
        assert result.signature.parameters[0].name == "self"

    def test_class_method_captures_cls(self) -> None:
        result = inspect_function(MyClass.class_method.__func__)

        assert is_function_node(result)
        assert result.name == "class_method"
        assert result.signature.parameters[0].name == "cls"

    def test_static_method_no_implicit_param(self) -> None:
        result = inspect_function(MyClass.static_method)

        assert is_function_node(result)
        assert result.name == "static_method"
        assert len(result.signature.parameters) == 1
        assert result.signature.parameters[0].name == "x"


class TestDecoratedFunctions:
    def test_wrapped_function_follow_wrapped_true(self) -> None:
        result = inspect_signature(decorated_function, follow_wrapped=True)

        assert is_signature_node(result)
        assert len(result.parameters) == 1
        assert result.parameters[0].name == "x"

    def test_wrapped_function_follow_wrapped_false(self) -> None:
        result = inspect_signature(decorated_function, follow_wrapped=False)

        assert is_signature_node(result)
        assert len(result.parameters) == 1
        assert result.parameters[0].name == "x"


class TestAnnotatedParameters:
    def test_annotated_parameter_extracts_metadata(self) -> None:
        result = inspect_signature(with_annotated)

        assert is_signature_node(result)
        x_param = result.parameters[0]
        _ = assert_concrete_type(x_param.type, int)
        assert "metadata" in x_param.metadata


class TestStaticMethodAndClassMethodDecorators:
    def test_staticmethod_decorator_captured(self) -> None:
        result = inspect_function(staticmethod(MyClass.static_method))

        assert is_function_node(result)
        assert "staticmethod" in result.decorators

    def test_classmethod_decorator_captured(self) -> None:
        # classmethod() expects a function but we pass a bound method
        # - intentional for testing
        cm = classmethod(  # pyright: ignore[reportUnknownVariableType]
            MyClass.instance_method,  # type: ignore[arg-type] # pyright: ignore[reportArgumentType]
        )
        result = inspect_function(cm)  # pyright: ignore[reportArgumentType]

        assert is_function_node(result)
        assert "classmethod" in result.decorators


class TestSignatureExceptionHandling:
    def test_function_with_broken_annotations_continues(self) -> None:
        # Create a function with annotations that will fail to evaluate
        # Intentionally uses undefined type to test error recovery
        def broken_func(
            x: "NonexistentType",  # type: ignore[name-defined] # noqa: ARG001, F821 # pyright: ignore[reportUndefinedVariable,reportUnknownParameterType]
        ) -> int:
            return 0

        # Use stringified mode to avoid evaluation errors
        config = InspectConfig(eval_mode=EvalMode.STRINGIFIED)
        result = inspect_signature(broken_func, config=config)  # pyright: ignore[reportUnknownArgumentType]

        assert is_signature_node(result)
        # Should have the parameter even if annotation is a forward ref
        assert len(result.parameters) == 1
        assert result.parameters[0].name == "x"

    def test_callable_without_signature_returns_minimal_node(self) -> None:
        # Intentionally break __call__ to test fallback behavior
        class MinimalCallable:
            __call__: None = None  # type: ignore[assignment] - intentionally invalid to break signature

        try:
            # MinimalCallable() is not truly callable - testing error handling
            result = inspect_signature(MinimalCallable())  # pyright: ignore[reportArgumentType]
            # If we get here, check minimal structure
            assert is_signature_node(result)
            assert result.parameters == ()
            assert is_any_node(result.returns)
        except (TypeError, ValueError):
            # Some Python versions may raise instead
            pass


class TestFunctionTypeParams:
    @pytest.mark.skipif(
        sys.version_info < (3, 12),
        reason="PEP 695 type params require Python 3.12+",
    )
    def test_function_with_type_params_captured(self) -> None:
        # This test would need a function with type params defined using
        # the new syntax: def f[T](x: T) -> T
        # Can't define this dynamically easily, so skip for now
        pytest.skip("PEP 695 function type params require special syntax")


class TestAnonymousFunction:
    def test_anonymous_function_has_fallback_name(self) -> None:
        # Create a callable without __name__
        class AnonymousCallable:
            def __call__(self, x: int) -> str:
                return str(x)

        anon = AnonymousCallable()
        # Intentionally remove __name__ to test fallback name handling
        if hasattr(anon, "__name__"):
            del anon.__name__  # type: ignore[attr-defined] # pyright: ignore[reportAttributeAccessIssue]

        result = inspect_function(anon)

        assert is_function_node(result)
        # Should have a fallback name
        assert result.name == "<anonymous>"


class TestAnnotationExceptionHandling:
    def test_function_with_broken_annotations_dict_continues(self) -> None:
        # Use the EvalMode.STRINGIFIED to avoid evaluating the annotation
        # but trigger get_annotations to handle the broken annotation
        # Intentionally uses undefined type to test error recovery
        def broken_func(
            x: "NonexistentType",  # type: ignore[name-defined] # noqa: ARG001, F821 # pyright: ignore[reportUndefinedVariable,reportUnknownParameterType]
        ) -> int:
            return 0

        config = InspectConfig(eval_mode=EvalMode.STRINGIFIED)
        result = inspect_signature(broken_func, config=config)  # pyright: ignore[reportUnknownArgumentType]

        assert is_signature_node(result)
        # Should have the parameter with a forward ref
        assert len(result.parameters) == 1


class TestFunctionTypeParamsHandling:
    def test_function_with_simulated_type_params_attribute(self) -> None:
        # Simulate __type_params__ attribute on a function
        # This tests the code path that handles __type_params__ even on Python < 3.12
        def sample_func(x: int) -> str:
            return str(x)

        # Manually add __type_params__ to simulate Python 3.12+ behavior
        # on older versions
        T = TypeVar("T")
        sample_func.__type_params__ = (T,)  # type: ignore[attr-defined] # pyright: ignore[reportFunctionMemberAccess]

        result = inspect_signature(sample_func)

        assert is_signature_node(result)
        # Should have type params captured
        assert len(result.type_params) == 1

    def test_function_without_type_params(self) -> None:
        def regular_func(x: int) -> str:
            return str(x)

        result = inspect_signature(regular_func)

        assert is_signature_node(result)
        assert len(result.type_params) == 0

    def test_function_with_non_typeparam_in_type_params(self) -> None:
        # Test that non-TypeVar/ParamSpec/TypeVarTuple items in __type_params__
        # are skipped (the `if is_type_param_node(tp_node)` branch)
        def sample_func(x: int) -> str:
            return str(x)

        # Intentionally add non-type-params to test filtering logic
        sample_func.__type_params__ = (int, str)  # type: ignore[attr-defined] # pyright: ignore[reportFunctionMemberAccess]

        result = inspect_signature(sample_func)

        assert is_signature_node(result)
        # Should have 0 type params since int/str aren't type parameters
        assert len(result.type_params) == 0


class TestBrokenAnnotationsPropertyHandling:
    def test_broken_annotations_property_returns_any_types(self) -> None:
        # Create a callable with working signature but broken __annotations__
        class BadCallable:
            def __call__(self, x: int) -> str:
                return str(x)

        obj = BadCallable()
        # Set __annotations__ to something that causes ValueError in get_annotations
        object.__setattr__(
            obj,
            "__annotations__",
            property(lambda _: None),  # pyright: ignore[reportAny]
        )

        result = inspect_signature(obj)

        assert is_signature_node(result)
        # Signature is captured but types are Any since annotations failed
        assert len(result.parameters) == 1
        assert result.parameters[0].name == "x"
        assert is_any_node(result.parameters[0].type)
        assert is_any_node(result.returns)


# Module-level classes for auto-namespace testing with forward references
class ForwardRefTarget:
    pass


class ContainerWithMethod:
    def method(self, x: "ContainerWithMethod") -> "ContainerWithMethod":
        return x


def _assert_resolved_forward_ref(node: ForwardRefNode, expected_cls: type) -> None:
    """Assert that a forward ref node is resolved to the expected class."""
    node_type = type(node).__name__
    assert isinstance(node, ForwardRefNode), f"Expected ForwardRefNode, got {node_type}"
    state_type = type(node.state).__name__
    msg = f"Expected RefResolved, got {state_type}"
    assert isinstance(node.state, RefResolved), msg
    _ = assert_concrete_type(node.state.node, expected_cls)


class TestAutoNamespaceIntegration:
    def test_inspect_function_resolves_forward_ref_with_auto_namespace(self) -> None:
        def func_with_forward_ref(x: "ForwardRefTarget") -> "ForwardRefTarget":
            return x

        result = inspect_function(func_with_forward_ref)

        assert is_function_node(result)
        param_type = result.signature.parameters[0].type
        return_type = result.signature.returns
        assert isinstance(param_type, ForwardRefNode)
        assert isinstance(return_type, ForwardRefNode)
        _assert_resolved_forward_ref(param_type, ForwardRefTarget)
        _assert_resolved_forward_ref(return_type, ForwardRefTarget)

    def test_inspect_signature_resolves_forward_ref_with_auto_namespace(self) -> None:
        def func_with_forward_ref(x: "ForwardRefTarget") -> "ForwardRefTarget":
            return x

        result = inspect_signature(func_with_forward_ref)

        assert is_signature_node(result)
        param_type = result.parameters[0].type
        return_type = result.returns
        assert isinstance(param_type, ForwardRefNode)
        assert isinstance(return_type, ForwardRefNode)
        _assert_resolved_forward_ref(param_type, ForwardRefTarget)
        _assert_resolved_forward_ref(return_type, ForwardRefTarget)

    def test_inspect_function_with_auto_namespace_disabled_leaves_forward_refs(
        self,
    ) -> None:
        def func_with_forward_ref(x: "ForwardRefTarget") -> "ForwardRefTarget":
            return x

        config = InspectConfig(auto_namespace=False)
        result = inspect_function(func_with_forward_ref, config=config)

        assert is_function_node(result)
        param_type = result.signature.parameters[0].type
        assert is_forward_ref_node(param_type)

    def test_inspect_signature_with_auto_namespace_disabled_leaves_forward_refs(
        self,
    ) -> None:
        def func_with_forward_ref(x: "ForwardRefTarget") -> "ForwardRefTarget":
            return x

        config = InspectConfig(auto_namespace=False)
        result = inspect_signature(func_with_forward_ref, config=config)

        assert is_signature_node(result)
        param_type = result.parameters[0].type
        assert is_forward_ref_node(param_type)

    def test_user_provided_namespace_takes_precedence(self) -> None:
        class CustomTarget:
            pass

        def func_with_forward_ref(x: "ForwardRefTarget") -> "ForwardRefTarget":
            return x  # type: ignore[return-value]

        config = InspectConfig(localns={"ForwardRefTarget": CustomTarget})
        result = inspect_signature(func_with_forward_ref, config=config)

        assert is_signature_node(result)
        param_type = result.parameters[0].type
        assert isinstance(param_type, ForwardRefNode)
        _assert_resolved_forward_ref(param_type, CustomTarget)

    def test_builtin_function_with_auto_namespace_no_error(self) -> None:
        # Built-in functions have no __globals__
        result = inspect_signature(len)

        assert is_signature_node(result)
        # Should not raise, even though len has no __globals__

    def test_lambda_with_auto_namespace_resolves_forward_refs(self) -> None:
        func = lambda x: x  # noqa: E731 # pyright: ignore[reportUnknownLambdaType,reportUnknownVariableType]
        func.__annotations__ = {"x": "ForwardRefTarget", "return": "ForwardRefTarget"}

        result = inspect_signature(func)  # pyright: ignore[reportUnknownArgumentType]

        assert is_signature_node(result)
        param_type = result.parameters[0].type
        assert isinstance(param_type, ForwardRefNode)
        _assert_resolved_forward_ref(param_type, ForwardRefTarget)

    def test_method_with_auto_namespace_resolves_owning_class(self) -> None:
        result = inspect_signature(ContainerWithMethod.method)

        assert is_signature_node(result)
        # x parameter is the second one (after self)
        x_param_type = result.parameters[1].type
        return_type = result.returns
        assert isinstance(x_param_type, ForwardRefNode)
        assert isinstance(return_type, ForwardRefNode)
        _assert_resolved_forward_ref(x_param_type, ContainerWithMethod)
        _assert_resolved_forward_ref(return_type, ContainerWithMethod)


# PEP 563 function inspection tests


class TestPEP563FunctionScenarios:
    def test_function_with_self_referential_return_resolved(self) -> None:
        from tests.unit.pep563_fixtures import TreeNodeDC, create_tree_node

        result = inspect_function(create_tree_node)

        assert is_function_node(result)
        return_type = result.signature.returns
        assert isinstance(return_type, ForwardRefNode)
        _assert_resolved_forward_ref(return_type, TreeNodeDC)

    def test_function_with_self_referential_param_resolved(self) -> None:
        from tests.unit.pep563_fixtures import TreeNodeDC, process_tree

        result = inspect_function(process_tree)

        assert is_function_node(result)
        param_type = result.signature.parameters[0].type
        assert isinstance(param_type, ForwardRefNode)
        _assert_resolved_forward_ref(param_type, TreeNodeDC)

    def test_function_with_union_return_type_contains_forward_ref(self) -> None:
        from typing_graph._node import ConcreteNode, UnionNode, is_concrete_node

        from tests.unit.pep563_fixtures import TreeNodeDC, process_tree

        result = inspect_function(process_tree)

        assert is_function_node(result)
        # Return type is ForwardRefNode wrapping "TreeNodeDC | None"
        return_type = result.signature.returns
        assert isinstance(return_type, ForwardRefNode)
        assert isinstance(return_type.state, RefResolved)
        # The resolved node is a UnionNode containing TreeNodeDC and None
        resolved_union = return_type.state.node
        assert isinstance(resolved_union, UnionNode)
        assert len(resolved_union.members) == 2
        # One member should be ConcreteNode for TreeNodeDC (already resolved)
        tree_member = next(
            (
                m
                for m in resolved_union.members
                if is_concrete_node(m) and m.cls is TreeNodeDC
            ),
            None,
        )
        assert tree_member is not None
        # Other member should be ConcreteNode for NoneType
        none_member = next(
            (
                m
                for m in resolved_union.members
                if is_concrete_node(m) and m.cls is type(None)
            ),
            None,
        )
        assert none_member is not None
        assert isinstance(none_member, ConcreteNode)
        assert none_member.cls is type(None)

    def test_function_with_sibling_reference_param_resolved(self) -> None:
        from typing_graph._node import (
            SubscriptedGenericNode,
            is_concrete_node,
            is_generic_node,
        )

        from tests.unit.pep563_fixtures import ChildDC, create_parent

        result = inspect_function(create_parent)

        assert is_function_node(result)
        # Second parameter (children) is list[ChildDC] wrapped in ForwardRefNode
        children_param = result.signature.parameters[1]
        assert children_param.name == "children"
        # The param type is a ForwardRefNode wrapping list[ChildDC]
        assert isinstance(children_param.type, ForwardRefNode)
        assert isinstance(children_param.type.state, RefResolved)
        # The resolved node should be SubscriptedGenericNode for list[ChildDC]
        resolved_list = children_param.type.state.node
        assert isinstance(resolved_list, SubscriptedGenericNode)
        assert is_generic_node(resolved_list.origin)
        assert resolved_list.origin.cls is list
        # The type arg should be ConcreteNode for ChildDC (already resolved)
        assert len(resolved_list.args) == 1
        child_arg = resolved_list.args[0]
        assert is_concrete_node(child_arg)
        assert child_arg.cls is ChildDC

    def test_function_with_sibling_reference_return_resolved(self) -> None:
        from tests.unit.pep563_fixtures import ParentDC, create_parent

        result = inspect_function(create_parent)

        assert is_function_node(result)
        return_type = result.signature.returns
        assert isinstance(return_type, ForwardRefNode)
        _assert_resolved_forward_ref(return_type, ParentDC)

    def test_function_with_optional_sibling_param_resolved(self) -> None:
        from tests.unit.pep563_fixtures import create_child

        result = inspect_function(create_child)

        assert is_function_node(result)
        # Second parameter (parent) is ParentDC | None
        parent_param = result.signature.parameters[1]
        assert parent_param.name == "parent"
        assert parent_param.has_default is True
        assert parent_param.default is None

    def test_generic_function_with_forward_ref_resolved(self) -> None:
        from typing_graph._node import GenericTypeNode, SubscriptedGenericNode

        from tests.unit.pep563_fixtures import GenericNode, create_generic_node

        result = inspect_function(create_generic_node)

        assert is_function_node(result)
        return_type = result.signature.returns
        # GenericNode[T] is ForwardRefNode with resolved SubscriptedGenericNode
        assert isinstance(return_type, ForwardRefNode)
        assert isinstance(return_type.state, RefResolved)
        resolved_node = return_type.state.node
        assert isinstance(resolved_node, SubscriptedGenericNode)
        assert isinstance(resolved_node.origin, GenericTypeNode)
        assert resolved_node.origin.cls is GenericNode


class TestPEP563MethodScenarios:
    def test_instance_method_returns_forward_ref_resolved(self) -> None:
        from tests.unit.pep563_fixtures import NodeService, TreeNodeDC

        result = inspect_function(NodeService.get_node)

        assert is_function_node(result)
        return_type = result.signature.returns
        assert isinstance(return_type, ForwardRefNode)
        _assert_resolved_forward_ref(return_type, TreeNodeDC)

    def test_instance_method_param_forward_ref_resolved(self) -> None:
        from tests.unit.pep563_fixtures import NodeService, TreeNodeDC

        result = inspect_function(NodeService.process)

        assert is_function_node(result)
        # node is the second parameter (after self)
        node_param = result.signature.parameters[1]
        assert node_param.name == "node"
        assert isinstance(node_param.type, ForwardRefNode)
        _assert_resolved_forward_ref(node_param.type, TreeNodeDC)

    def test_instance_method_self_referential_return_resolved(self) -> None:
        from tests.unit.pep563_fixtures import NodeService

        result = inspect_function(NodeService.create_self)

        assert is_function_node(result)
        return_type = result.signature.returns
        assert isinstance(return_type, ForwardRefNode)
        _assert_resolved_forward_ref(return_type, NodeService)

    def test_classmethod_self_referential_return_resolved(self) -> None:
        from tests.unit.pep563_fixtures import NodeService

        result = inspect_function(NodeService.from_value.__func__)

        assert is_function_node(result)
        return_type = result.signature.returns
        assert isinstance(return_type, ForwardRefNode)
        _assert_resolved_forward_ref(return_type, NodeService)

    def test_staticmethod_forward_ref_param_resolved(self) -> None:
        from tests.unit.pep563_fixtures import NodeService, TreeNodeDC

        result = inspect_function(NodeService.helper)

        assert is_function_node(result)
        # node is the first parameter (no self for staticmethod)
        node_param = result.signature.parameters[0]
        assert node_param.name == "node"
        assert isinstance(node_param.type, ForwardRefNode)
        _assert_resolved_forward_ref(node_param.type, TreeNodeDC)


class TestPEP563CallableScenarios:
    def test_callable_class_call_method_forward_ref_return_resolved(self) -> None:
        from tests.unit.pep563_fixtures import NodeCreator, TreeNodeDC

        # Test __call__ method via class, not instance
        result = inspect_function(NodeCreator.__call__)

        assert is_function_node(result)
        return_type = result.signature.returns
        assert isinstance(return_type, ForwardRefNode)
        _assert_resolved_forward_ref(return_type, TreeNodeDC)

    def test_callable_class_call_method_multiple_forward_ref_params_resolved(
        self,
    ) -> None:
        from tests.unit.pep563_fixtures import ChildDC, ParentDC, TreeProcessor

        # Test __call__ method via class, not instance
        result = inspect_function(TreeProcessor.__call__)

        assert is_function_node(result)
        # First param after self is parent (index 1)
        parent_param = result.signature.parameters[1]
        assert parent_param.name == "parent"
        assert isinstance(parent_param.type, ForwardRefNode)
        _assert_resolved_forward_ref(parent_param.type, ParentDC)

        # Second param is child (index 2)
        child_param = result.signature.parameters[2]
        assert child_param.name == "child"
        assert isinstance(child_param.type, ForwardRefNode)
        _assert_resolved_forward_ref(child_param.type, ChildDC)

    def test_callable_class_call_method_complex_return_type(self) -> None:
        from typing_graph._node import (
            SubscriptedGenericNode,
            TupleNode,
            is_concrete_node,
            is_generic_node,
        )

        from tests.unit.pep563_fixtures import ChildDC, ParentDC, TreeProcessor

        # Test __call__ method via class, not instance
        result = inspect_function(TreeProcessor.__call__)

        assert is_function_node(result)
        # Return is ForwardRefNode wrapping "tuple[ParentDC, list[ChildDC]]"
        return_type = result.signature.returns
        assert isinstance(return_type, ForwardRefNode)
        assert isinstance(return_type.state, RefResolved)
        # The resolved node is a TupleNode for tuple[ParentDC, list[ChildDC]]
        resolved_tuple = return_type.state.node
        assert isinstance(resolved_tuple, TupleNode)
        assert resolved_tuple.homogeneous is False
        assert len(resolved_tuple.elements) == 2
        # First element should be ConcreteNode for ParentDC (already resolved)
        first_elem = resolved_tuple.elements[0]
        assert is_concrete_node(first_elem)
        assert first_elem.cls is ParentDC
        # Second element should be SubscriptedGenericNode for list[ChildDC]
        second_elem = resolved_tuple.elements[1]
        assert isinstance(second_elem, SubscriptedGenericNode)
        assert is_generic_node(second_elem.origin)
        assert second_elem.origin.cls is list
        assert len(second_elem.args) == 1
        child_arg = second_elem.args[0]
        assert is_concrete_node(child_arg)
        assert child_arg.cls is ChildDC

    def test_nested_class_inner_self_referential_method(self) -> None:
        from tests.unit.pep563_fixtures import Outer

        result = inspect_function(Outer.Inner.get_inner)

        assert is_function_node(result)
        return_type = result.signature.returns
        assert isinstance(return_type, ForwardRefNode)
        _assert_resolved_forward_ref(return_type, Outer.Inner)

    def test_nested_class_inner_to_outer_reference(self) -> None:
        from tests.unit.pep563_fixtures import Outer

        result = inspect_function(Outer.Inner.get_outer)

        assert is_function_node(result)
        return_type = result.signature.returns
        assert isinstance(return_type, ForwardRefNode)
        _assert_resolved_forward_ref(return_type, Outer)


class TestPEP563FunctionAutoNamespaceDisabled:
    def test_function_forward_ref_unresolved_when_auto_namespace_disabled(self) -> None:
        from tests.unit.pep563_fixtures import process_tree

        config = InspectConfig(auto_namespace=False)
        result = inspect_function(process_tree, config=config)

        assert is_function_node(result)
        param_type = result.signature.parameters[0].type
        assert is_forward_ref_node(param_type)
        # Without auto_namespace, it should still be a forward ref but may not resolve

    def test_method_forward_ref_unresolved_when_auto_namespace_disabled(self) -> None:
        from tests.unit.pep563_fixtures import NodeService

        config = InspectConfig(auto_namespace=False)
        result = inspect_function(NodeService.get_node, config=config)

        assert is_function_node(result)
        return_type = result.signature.returns
        assert is_forward_ref_node(return_type)

    def test_callable_forward_ref_unresolved_when_auto_namespace_disabled(self) -> None:
        from tests.unit.pep563_fixtures import NodeCreator

        # Test __call__ method via class, not instance
        config = InspectConfig(auto_namespace=False)
        result = inspect_function(NodeCreator.__call__, config=config)

        assert is_function_node(result)
        return_type = result.signature.returns
        assert is_forward_ref_node(return_type)

    def test_explicit_namespace_overrides_auto_namespace(self) -> None:
        from tests.unit.pep563_fixtures import TreeNodeDC, process_tree

        # Provide explicit namespace
        config = InspectConfig(localns={"TreeNodeDC": TreeNodeDC})
        result = inspect_function(process_tree, config=config)

        assert is_function_node(result)
        param_type = result.signature.parameters[0].type
        assert isinstance(param_type, ForwardRefNode)
        _assert_resolved_forward_ref(param_type, TreeNodeDC)
