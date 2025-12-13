# Testing namespace utilities requires working with dict[str, Any] types.
# Private function tests (merge_namespaces) require private imports until integrated.
# pyright: reportAny=false, reportExplicitAny=false
# pyright: reportPrivateUsage=false, reportUnannotatedClassAttribute=false
from types import ModuleType
from typing import TYPE_CHECKING, Any

import pytest

from typing_graph import (
    extract_class_namespace,
    extract_function_namespace,
    extract_module_namespace,
    extract_namespace,
)

# merge_namespaces is not yet used by public API, so needs direct testing
# _traverse_to_class edge cases cannot be exercised via public API
# apply_*_namespace functions need direct testing for coverage
from typing_graph._config import InspectConfig
from typing_graph._namespace import (
    _traverse_to_class,
    apply_class_namespace,
    apply_function_namespace,
    merge_namespaces,
)

if TYPE_CHECKING:
    from collections.abc import Callable


class SimpleClass:
    pass


class ClassWithMethod:
    def method(self) -> None:
        pass

    @staticmethod
    def static_method() -> None:
        pass

    @classmethod
    def class_method(cls) -> None:
        pass


class OuterClass:
    class InnerClass:
        def inner_method(self) -> None:
            pass


def top_level_function() -> None:
    pass


class TestOwningClassResolution:
    @pytest.mark.parametrize(
        ("func", "expected_class_name", "expected_class"),
        [
            pytest.param(
                ClassWithMethod.method,
                "ClassWithMethod",
                ClassWithMethod,
                id="instance_method",
            ),
            pytest.param(
                ClassWithMethod.static_method,
                "ClassWithMethod",
                ClassWithMethod,
                id="static_method",
            ),
            pytest.param(
                ClassWithMethod.class_method,
                "ClassWithMethod",
                ClassWithMethod,
                id="class_method",
            ),
            pytest.param(
                OuterClass.InnerClass.inner_method,
                "InnerClass",
                OuterClass.InnerClass,
                id="nested_class_method",
            ),
        ],
    )
    def test_resolves_owner_for_method(
        self,
        func: "Callable[..., Any]",
        expected_class_name: str,
        expected_class: type,
    ) -> None:
        _globalns, localns = extract_function_namespace(func)
        assert expected_class_name in localns
        assert localns[expected_class_name] is expected_class

    def test_no_owner_for_top_level_function(self) -> None:
        globalns, localns = extract_function_namespace(top_level_function)
        # Top-level function has no owning class
        has_type_in_localns = any(isinstance(v, type) for v in localns.values())
        assert not has_type_in_localns
        # But should have module globals
        assert len(globalns) > 0

    def test_nested_class_includes_outer_class(self) -> None:
        inner_method = OuterClass.InnerClass.inner_method
        _globalns, localns = extract_function_namespace(inner_method)
        # Inner class is resolved, outer class should also be accessible via globals
        assert "InnerClass" in localns

    def test_no_owner_for_builtin_function(self) -> None:
        # Built-in functions don't have __globals__ or owning classes
        globalns, localns = extract_function_namespace(len)
        assert globalns == {}
        assert localns == {}

    def test_method_from_instance(self) -> None:
        instance = ClassWithMethod()
        bound_method = instance.method

        # Bound methods should still resolve to the class
        _globalns, localns = extract_function_namespace(bound_method)
        assert "ClassWithMethod" in localns


class TestExtractClassNamespace:
    def test_extracts_global_namespace_from_module(self) -> None:
        globalns, _localns = extract_class_namespace(SimpleClass)
        # Should contain module globals
        assert "SimpleClass" in globalns
        assert "ClassWithMethod" in globalns

    def test_includes_class_in_local_namespace(self) -> None:
        _globalns, localns = extract_class_namespace(SimpleClass)
        assert "SimpleClass" in localns
        assert localns["SimpleClass"] is SimpleClass

    def test_handles_none_module_attribute(self) -> None:
        # Test via a class with __module__ set to None (edge case)
        # We can't delete __module__, but we test that None is handled gracefully
        # The implementation already handles getattr returning None
        cls = type("NoneModule", (), {"__module__": None})  # type: ignore[dict-item]
        globalns, localns = extract_class_namespace(cls)
        # Should return empty global namespace but still have class in local
        assert globalns == {}
        assert "NoneModule" in localns

    def test_handles_module_not_in_sys_modules(self) -> None:
        # Create a class with fake module name
        cls = type("FakeModuleClass", (), {"__module__": "nonexistent.module"})
        globalns, _localns = extract_class_namespace(cls)
        assert globalns == {}

    def test_handles_builtin_types(self) -> None:
        # Built-in types like int should work
        _globalns, localns = extract_class_namespace(int)
        # builtins module should be accessible
        assert "int" in localns
        assert localns["int"] is int

    def test_handles_module_with_non_dict_attribute(self) -> None:
        # Test partial branch: module_dict not a dict (line 125->129)
        import sys

        class FakeModule:
            __dict__ = "not a dict"  # pyright: ignore[reportAssignmentType]

        fake_mod_name = "__fake_module_test__"
        sys.modules[fake_mod_name] = FakeModule()  # pyright: ignore[reportArgumentType]
        try:
            cls = type("TestClass", (), {"__module__": fake_mod_name})
            globalns, localns = extract_class_namespace(cls)
            assert globalns == {}
            assert "TestClass" in localns
        finally:
            del sys.modules[fake_mod_name]

    def test_class_name_none_not_added_to_localns(self) -> None:
        # Test partial branch: class_name is None (line 130->134)
        cls = type("NoneNameClass", (), {"__name__": None})  # type: ignore[dict-item]
        _globalns, localns = extract_class_namespace(cls)
        assert None not in localns

    def test_dynamically_created_class(self) -> None:
        # Dynamically created class might have unusual module
        dynamic_class = type("DynamicClass", (), {"__module__": __name__})
        _globalns, localns = extract_class_namespace(dynamic_class)

        # Should extract from current module
        assert "DynamicClass" in localns
        assert localns["DynamicClass"] is dynamic_class


class TestExtractFunctionNamespace:
    def test_extracts_global_namespace_from_function(self) -> None:
        globalns, _localns = extract_function_namespace(top_level_function)
        # Should contain module globals
        assert "SimpleClass" in globalns
        assert "top_level_function" in globalns

    def test_includes_owning_class_in_local_namespace_for_method(self) -> None:
        _globalns, localns = extract_function_namespace(ClassWithMethod.method)
        assert "ClassWithMethod" in localns
        assert localns["ClassWithMethod"] is ClassWithMethod

    def test_top_level_function_has_empty_local_namespace(self) -> None:
        _globalns, localns = extract_function_namespace(top_level_function)
        # No owning class, no type params on 3.10/3.11
        # Could have type params on 3.12+ if function is generic
        # For our non-generic function, should be empty (or have only type params)
        assert "top_level_function" not in localns

    def test_handles_missing_globals(self) -> None:
        # Built-in functions don't have __globals__
        globalns, localns = extract_function_namespace(len)
        assert globalns == {}
        assert localns == {}

    def test_handles_nested_class_method(self) -> None:
        _globalns, localns = extract_function_namespace(
            OuterClass.InnerClass.inner_method
        )
        # Should resolve to InnerClass
        assert "InnerClass" in localns
        assert localns["InnerClass"] is OuterClass.InnerClass

    def test_lambda_function(self) -> None:
        # Lambdas are callables with unusual qualnames
        fn: Callable[[Any], Any] = lambda x: x  # noqa: E731
        globalns, localns = extract_function_namespace(fn)

        # Should have module globals but no owning class
        assert isinstance(globalns, dict)
        # Lambdas don't have owning classes
        assert not any(isinstance(v, type) for v in localns.values())


class TestExtractModuleNamespace:
    def test_extracts_module_dict_as_global_namespace(self) -> None:
        import typing_graph

        globalns, localns = extract_module_namespace(typing_graph)
        # Should contain module exports
        assert "inspect_type" in globalns
        assert localns == {}

    def test_local_namespace_always_empty(self) -> None:
        import typing_graph

        _globalns, localns = extract_module_namespace(typing_graph)
        assert localns == {}

    def test_handles_module_without_dict(self) -> None:
        # Create a minimal module-like object
        fake_module = ModuleType("fake_module")
        globalns, localns = extract_module_namespace(fake_module)
        # ModuleType always has __dict__, but should handle gracefully
        assert isinstance(globalns, dict)
        assert localns == {}

    def test_module_with_non_dict_attribute(self) -> None:
        # Test partial branch: module_dict not a dict (line 197->200)
        class FakeModuleNonDict:
            __dict__ = "not a dict"  # pyright: ignore[reportAssignmentType]

        globalns, localns = extract_module_namespace(
            FakeModuleNonDict()  # pyright: ignore[reportArgumentType]
        )
        assert globalns == {}
        assert localns == {}


class TestExtractNamespace:
    def test_dispatches_to_class_extractor(self) -> None:
        result = extract_namespace(SimpleClass)
        expected = extract_class_namespace(SimpleClass)
        assert result == expected

    def test_dispatches_to_function_extractor(self) -> None:
        result = extract_namespace(top_level_function)
        expected = extract_function_namespace(top_level_function)
        assert result == expected

    def test_dispatches_to_module_extractor(self) -> None:
        import typing_graph

        result = extract_namespace(typing_graph)
        expected = extract_module_namespace(typing_graph)
        assert result == expected

    @pytest.mark.parametrize(
        ("source", "match"),
        [
            pytest.param(
                "not a valid source", "source must be a class, callable", id="string"
            ),
            pytest.param(None, "source must be a class, callable", id="none"),
            pytest.param(42, "got 'int'", id="int"),
        ],
    )
    def test_raises_type_error_for_invalid_source(
        self, source: Any, match: str
    ) -> None:
        with pytest.raises(TypeError, match=match):
            _ = extract_namespace(source)

    def test_handles_callable_class_instance(self) -> None:
        class CallableClass:
            def __call__(self) -> None:
                pass

        instance = CallableClass()
        # Should use function extractor since it's callable but not a type
        globalns, _localns = extract_namespace(instance)
        # Callable instances don't have __globals__, so empty
        assert globalns == {}


class TestMergeNamespaces:
    def test_merges_auto_and_user_globalns(self) -> None:
        auto_global = {"a": 1, "b": 2}
        auto_local: dict[str, Any] = {}
        user_global = {"b": 3, "c": 4}
        user_local: dict[str, Any] | None = None

        merged_global, merged_local = merge_namespaces(
            auto_global, auto_local, user_global, user_local
        )

        assert merged_global == {"a": 1, "b": 3, "c": 4}
        assert merged_local == {}

    def test_merges_auto_and_user_localns(self) -> None:
        auto_global: dict[str, Any] = {}
        auto_local = {"x": 10}
        user_global: dict[str, Any] | None = None
        user_local = {"x": 20, "y": 30}

        merged_global, merged_local = merge_namespaces(
            auto_global, auto_local, user_global, user_local
        )

        assert merged_global == {}
        assert merged_local == {"x": 20, "y": 30}

    def test_user_values_take_precedence(self) -> None:
        auto_global = {"key": "auto_value"}
        auto_local = {"key2": "auto_value2"}
        user_global = {"key": "user_value"}
        user_local = {"key2": "user_value2"}

        merged_global, merged_local = merge_namespaces(
            auto_global, auto_local, user_global, user_local
        )

        assert merged_global["key"] == "user_value"
        assert merged_local["key2"] == "user_value2"

    def test_handles_none_user_namespaces(self) -> None:
        auto_global = {"a": 1}
        auto_local = {"b": 2}

        merged_global, merged_local = merge_namespaces(
            auto_global, auto_local, None, None
        )

        assert merged_global == {"a": 1}
        assert merged_local == {"b": 2}

    def test_does_not_modify_input_dicts(self) -> None:
        auto_global = {"a": 1}
        auto_local = {"b": 2}
        user_global = {"c": 3}
        user_local = {"d": 4}

        auto_global_copy = dict(auto_global)
        auto_local_copy = dict(auto_local)
        user_global_copy = dict(user_global)
        user_local_copy = dict(user_local)

        _ = merge_namespaces(auto_global, auto_local, user_global, user_local)

        assert auto_global == auto_global_copy
        assert auto_local == auto_local_copy
        assert user_global == user_global_copy
        assert user_local == user_local_copy

    def test_returns_new_dicts(self) -> None:
        auto_global = {"a": 1}
        auto_local = {"b": 2}

        merged_global, merged_local = merge_namespaces(
            auto_global, auto_local, None, None
        )

        assert merged_global is not auto_global
        assert merged_local is not auto_local


class TestTypeParameters:
    def test_class_type_params_extracted_when_present(self) -> None:
        # Manually add __type_params__ to simulate PEP 695
        # (actual generic syntax only available on 3.12+)
        class MockTypeParam:
            __name__ = "T"

        cls = type("GenericClass", (), {"__type_params__": (MockTypeParam(),)})

        _globalns, localns = extract_class_namespace(cls)
        assert "T" in localns

    def test_function_type_params_extracted_when_present(self) -> None:
        class MockTypeParam:
            __name__ = "U"

        def generic_func() -> None:
            pass

        generic_func.__type_params__ = (MockTypeParam(),)  # pyright: ignore[reportFunctionMemberAccess]

        _globalns, localns = extract_function_namespace(generic_func)
        assert "U" in localns

    def test_handles_type_param_without_name(self) -> None:
        class BadTypeParam:
            pass  # No __name__

        cls = type("BadGenericClass", (), {"__type_params__": (BadTypeParam(),)})

        # Should not raise, just skip the param
        _globalns, localns = extract_class_namespace(cls)
        # No error raised
        assert isinstance(localns, dict)


class TestTraverseToClass:
    @pytest.mark.parametrize(
        ("globals_dict", "parts"),
        [
            pytest.param({}, [], id="empty_parts"),
            pytest.param({"foo": None}, ["foo", "bar"], id="intermediate_none"),
            pytest.param({"foo": "not a type"}, ["foo"], id="non_type_result"),
            pytest.param({"foo": int}, ["nonexistent"], id="missing_key"),
        ],
    )
    def test_returns_none_for_invalid_paths(
        self,
        globals_dict: dict[str, Any],
        parts: list[str],
    ) -> None:
        result = _traverse_to_class(globals_dict, parts)
        assert result is None

    def test_attribute_error_returns_none(self) -> None:
        # Test exception handling - object that raises on getattr
        class BadGetattr:
            def __getattribute__(self, name: str) -> None:  # pyright: ignore[reportImplicitOverride]
                raise AttributeError(name)

        result = _traverse_to_class({"bad": BadGetattr()}, ["bad", "something"])
        assert result is None

    def test_type_error_returns_none(self) -> None:
        # Test exception handling - dict that raises TypeError on get
        class TypeErrorDict(dict[str, Any]):
            def get(self, key: str, default: Any = None) -> Any:  # pyright: ignore[reportImplicitOverride]
                msg = "custom error"
                raise TypeError(msg)

        result = _traverse_to_class(TypeErrorDict(), ["foo"])
        assert result is None


class TestApplyClassNamespace:
    def test_applies_namespace_when_auto_namespace_true(
        self, auto_namespace_config: InspectConfig
    ) -> None:
        class TestClass:
            pass

        new_config = apply_class_namespace(TestClass, auto_namespace_config)

        assert new_config.globalns is not None
        assert new_config.localns is not None
        assert "TestClass" in new_config.localns

    def test_returns_unchanged_config_when_auto_namespace_false(
        self, no_auto_namespace_config: InspectConfig
    ) -> None:
        class TestClass:
            pass

        new_config = apply_class_namespace(TestClass, no_auto_namespace_config)

        assert new_config is no_auto_namespace_config

    def test_user_namespace_takes_precedence(self) -> None:
        class TestClass:
            pass

        user_value = "user override"
        config = InspectConfig(
            auto_namespace=True,
            localns={"TestClass": user_value},
        )
        new_config = apply_class_namespace(TestClass, config)

        assert new_config.localns is not None
        assert new_config.localns["TestClass"] == user_value


class TestApplyFunctionNamespace:
    def test_applies_namespace_when_auto_namespace_true(
        self, auto_namespace_config: InspectConfig
    ) -> None:
        def test_func() -> None:
            pass

        new_config = apply_function_namespace(test_func, auto_namespace_config)

        assert new_config.globalns is not None

    def test_returns_unchanged_config_when_auto_namespace_false(
        self, no_auto_namespace_config: InspectConfig
    ) -> None:
        def test_func() -> None:
            pass

        new_config = apply_function_namespace(test_func, no_auto_namespace_config)

        assert new_config is no_auto_namespace_config

    def test_method_includes_owning_class(
        self, auto_namespace_config: InspectConfig
    ) -> None:
        # Use module-level class ClassWithMethod since locally-defined classes
        # won't be in __globals__ and thus won't be resolved
        method = ClassWithMethod.method
        new_config = apply_function_namespace(method, auto_namespace_config)

        assert new_config.localns is not None
        assert "ClassWithMethod" in new_config.localns
        assert new_config.localns["ClassWithMethod"] is ClassWithMethod

    def test_user_namespace_takes_precedence(self) -> None:
        def test_func() -> None:
            pass

        user_global = {"custom": "value"}
        config = InspectConfig(
            auto_namespace=True,
            globalns=user_global,
        )
        new_config = apply_function_namespace(test_func, config)

        assert new_config.globalns is not None
        assert new_config.globalns["custom"] == "value"
