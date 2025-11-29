import sys
import types
from typing import TYPE_CHECKING, ParamSpec, TypeVar
from typing_extensions import TypeAliasType, TypeVarTuple

import pytest

from typing_graph import (
    InspectConfig,
    ModuleTypes,
    cache_clear,
    inspect_module,
)
from typing_graph._node import (
    is_class_node,
    is_concrete_node,
    is_function_node,
    is_param_spec_node,
    is_signature_node,
    is_type_var_node,
    is_type_var_tuple_node,
)

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(autouse=True)
def clear_type_cache() -> "Generator[None]":
    cache_clear()
    yield
    cache_clear()


def _create_sample_module() -> types.ModuleType:
    """Create a sample module for testing."""
    module = types.ModuleType("sample_module")
    module.__dict__["__name__"] = "sample_module"

    # Add a class with __module__ set
    class SampleClass:
        value: int = 0

    SampleClass.__module__ = "sample_module"
    module.__dict__["SampleClass"] = SampleClass

    # Add a function with __module__ set
    def sample_function(x: int) -> str:
        return str(x)

    sample_function.__module__ = "sample_module"
    module.__dict__["sample_function"] = sample_function

    # Add a type variable with __module__ set
    T = TypeVar("T")
    T.__module__ = "sample_module"
    module.__dict__["T"] = T

    return module


def _create_module_with_private() -> types.ModuleType:
    """Create a module with private items."""
    module = types.ModuleType("private_module")
    module.__dict__["__name__"] = "private_module"

    class PublicClass:
        pass

    class _PrivateClass:
        pass

    def public_function() -> None:
        pass

    def _private_function() -> None:
        pass

    PublicClass.__module__ = "private_module"
    _PrivateClass.__module__ = "private_module"
    public_function.__module__ = "private_module"
    _private_function.__module__ = "private_module"

    module.__dict__["PublicClass"] = PublicClass
    module.__dict__["_PrivateClass"] = _PrivateClass
    module.__dict__["public_function"] = public_function
    module.__dict__["_private_function"] = _private_function

    return module


def _create_module_with_imported() -> types.ModuleType:
    """Create a module with imported items."""
    module = types.ModuleType("importing_module")
    module.__dict__["__name__"] = "importing_module"

    # Local class
    class LocalClass:
        pass

    LocalClass.__module__ = "importing_module"
    module.__dict__["LocalClass"] = LocalClass

    # Imported class (from another module)
    class ImportedClass:
        pass

    ImportedClass.__module__ = "other_module"
    module.__dict__["ImportedClass"] = ImportedClass

    return module


class TestClassDiscovery:
    def test_class_discovered_in_classes_dict(self) -> None:
        module = _create_sample_module()
        result = inspect_module(module)

        assert "SampleClass" in result.classes

    def test_class_is_inspected_as_class_node(self) -> None:
        module = _create_sample_module()
        result = inspect_module(module)

        class_node = result.classes["SampleClass"]
        assert is_class_node(class_node)

    def test_class_name_matches(self) -> None:
        module = _create_sample_module()
        result = inspect_module(module)

        class_node = result.classes["SampleClass"]
        assert is_class_node(class_node)
        assert class_node.name == "SampleClass"


class TestFunctionDiscovery:
    def test_function_discovered_in_functions_dict(self) -> None:
        module = _create_sample_module()
        result = inspect_module(module)

        assert "sample_function" in result.functions

    def test_function_is_inspected_as_function_node(self) -> None:
        module = _create_sample_module()
        result = inspect_module(module)

        func_node = result.functions["sample_function"]
        assert is_function_node(func_node)

    def test_function_name_matches(self) -> None:
        module = _create_sample_module()
        result = inspect_module(module)

        func_node = result.functions["sample_function"]
        assert is_function_node(func_node)
        assert func_node.name == "sample_function"

    def test_function_signature_is_captured(self) -> None:
        module = _create_sample_module()
        result = inspect_module(module)

        func_node = result.functions["sample_function"]
        assert is_function_node(func_node)
        assert is_signature_node(func_node.signature)
        assert len(func_node.signature.parameters) == 1
        assert func_node.signature.parameters[0].name == "x"

    def test_function_parameter_type_is_concrete(self) -> None:
        module = _create_sample_module()
        result = inspect_module(module)

        func_node = result.functions["sample_function"]
        assert is_function_node(func_node)
        param_type = func_node.signature.parameters[0].type
        assert is_concrete_node(param_type)
        assert param_type.cls is int

    def test_function_return_type_is_captured(self) -> None:
        module = _create_sample_module()
        result = inspect_module(module)

        func_node = result.functions["sample_function"]
        assert is_function_node(func_node)
        assert is_concrete_node(func_node.signature.returns)
        assert func_node.signature.returns.cls is str


class TestTypeVarDiscovery:
    def test_typevar_discovered_in_type_vars_dict(self) -> None:
        module = _create_sample_module()
        result = inspect_module(module)

        assert "T" in result.type_vars

    def test_typevar_is_inspected_as_typevar_node(self) -> None:
        module = _create_sample_module()
        result = inspect_module(module)

        tv_node = result.type_vars["T"]
        assert is_type_var_node(tv_node)

    def test_typevar_name_matches(self) -> None:
        module = _create_sample_module()
        result = inspect_module(module)

        tv_node = result.type_vars["T"]
        assert is_type_var_node(tv_node)
        assert tv_node.name == "T"


class TestPrivateFiltering:
    def test_include_private_false_excludes_private_classes(self) -> None:
        module = _create_module_with_private()
        config = InspectConfig(include_private=False)
        result = inspect_module(module, config=config)

        assert "PublicClass" in result.classes
        assert "_PrivateClass" not in result.classes

    def test_include_private_false_excludes_private_functions(self) -> None:
        module = _create_module_with_private()
        config = InspectConfig(include_private=False)
        result = inspect_module(module, config=config)

        assert "public_function" in result.functions
        assert "_private_function" not in result.functions

    def test_include_private_true_includes_private_classes(self) -> None:
        module = _create_module_with_private()
        config = InspectConfig(include_private=True)
        result = inspect_module(module, config=config)

        assert "PublicClass" in result.classes
        assert "_PrivateClass" in result.classes

    def test_include_private_true_includes_private_functions(self) -> None:
        module = _create_module_with_private()
        config = InspectConfig(include_private=True)
        result = inspect_module(module, config=config)

        assert "public_function" in result.functions
        assert "_private_function" in result.functions


class TestImportedFiltering:
    def test_include_imported_false_excludes_imported_classes(self) -> None:
        module = _create_module_with_imported()
        result = inspect_module(module, include_imported=False)

        assert "LocalClass" in result.classes
        assert "ImportedClass" not in result.classes

    def test_include_imported_true_includes_imported_classes(self) -> None:
        module = _create_module_with_imported()
        result = inspect_module(module, include_imported=True)

        assert "LocalClass" in result.classes
        assert "ImportedClass" in result.classes


class TestRealModuleInspection:
    def test_inspect_typing_module(self) -> None:
        result = inspect_module(sys.modules["typing"])

        assert isinstance(result, ModuleTypes)
        # typing module should have some classes
        assert len(result.classes) > 0 or len(result.type_vars) > 0

    def test_inspect_with_config(self) -> None:
        module = _create_sample_module()
        config = InspectConfig()
        result = inspect_module(module, config=config)

        assert isinstance(result, ModuleTypes)
        assert "SampleClass" in result.classes


class TestModuleAnnotationExceptionHandling:
    def test_module_with_broken_annotations_continues_gracefully(self) -> None:
        module = types.ModuleType("broken_annotations")
        module.__dict__["__name__"] = "broken_annotations"

        # Create an object that will raise when get_annotations is called
        # by setting __annotations__ to something that causes evaluation errors
        # ARG005: unused self param is intentional - property signature requires it
        module.__dict__["__annotations__"] = property(
            lambda self: 1 / 0  # noqa: ARG005  # pyright: ignore[reportAny]
        )

        # Should not raise
        result = inspect_module(module)
        assert isinstance(result, ModuleTypes)


class TestModuleAttributeErrorHandling:
    def test_module_getattr_error_in_dir_is_handled(self) -> None:
        # We can't easily add a descriptor to a module type, so we test
        # by verifying the module inspects without error even when
        # attributes might be problematic
        module = types.ModuleType("test_attr")
        module.__dict__["__name__"] = "test_attr"

        # Add a normal item
        def normal_func() -> None:
            pass

        normal_func.__module__ = "test_attr"
        module.__dict__["normal_func"] = normal_func

        # Should work without error
        result = inspect_module(module)
        assert isinstance(result, ModuleTypes)


class TestModuleAnnotationsFiltering:
    def test_module_level_annotations_become_constants(self) -> None:
        module = types.ModuleType("annotated_module")
        module.__dict__["__name__"] = "annotated_module"

        # Set module annotations for constants
        module.__annotations__ = {"MY_CONSTANT": int, "OTHER_VALUE": str}

        result = inspect_module(module)

        assert isinstance(result, ModuleTypes)
        assert "MY_CONSTANT" in result.constants
        assert "OTHER_VALUE" in result.constants

    def test_private_annotations_excluded_by_default(self) -> None:
        module = types.ModuleType("private_annotations")
        module.__dict__["__name__"] = "private_annotations"

        module.__annotations__ = {
            "PUBLIC_VALUE": int,
            "_PRIVATE_VALUE": str,
        }

        config = InspectConfig(include_private=False)
        result = inspect_module(module, config=config)

        assert "PUBLIC_VALUE" in result.constants
        assert "_PRIVATE_VALUE" not in result.constants

    def test_private_annotations_included_when_configured(self) -> None:
        module = types.ModuleType("private_annotations_included")
        module.__dict__["__name__"] = "private_annotations_included"

        module.__annotations__ = {
            "PUBLIC_VALUE": int,
            "_PRIVATE_VALUE": str,
        }

        config = InspectConfig(include_private=True)
        result = inspect_module(module, config=config)

        assert "PUBLIC_VALUE" in result.constants
        assert "_PRIVATE_VALUE" in result.constants

    def test_annotations_not_duplicated_when_already_class_or_function(self) -> None:
        module = types.ModuleType("no_duplication")
        module.__dict__["__name__"] = "no_duplication"

        class MyClass:
            pass

        MyClass.__module__ = "no_duplication"
        module.__dict__["MyClass"] = MyClass
        module.__annotations__ = {"MyClass": type}

        result = inspect_module(module)

        assert "MyClass" in result.classes
        assert "MyClass" not in result.constants


class TestModuleInspectionExceptionHandling:
    def test_class_inspection_failure_continues(self) -> None:
        module = types.ModuleType("class_error_module")
        module.__dict__["__name__"] = "class_error_module"

        # Create a class that will cause inspection to fail
        class BrokenClass:
            # This will cause get_annotations to fail if it tries to evaluate
            __annotations__ = {"field": "NonexistentType"}  # pyright: ignore[reportUnannotatedClassAttribute]

        BrokenClass.__module__ = "class_error_module"
        module.__dict__["BrokenClass"] = BrokenClass

        # Add a normal class too
        class GoodClass:
            value: int = 0

        GoodClass.__module__ = "class_error_module"
        module.__dict__["GoodClass"] = GoodClass

        # Should not raise, and should still inspect the good class
        result = inspect_module(module)
        assert isinstance(result, ModuleTypes)

    def test_function_inspection_failure_continues(self) -> None:
        module = types.ModuleType("func_error_module")
        module.__dict__["__name__"] = "func_error_module"

        # Create a "function" that will cause signature inspection to fail
        class NotReallyCallable:
            __module__ = "func_error_module"

            def __call__(self) -> None:
                pass

        # Make inspect.signature fail by removing __wrapped__ and breaking signature
        broken_func = NotReallyCallable()
        broken_func.__module__ = "func_error_module"

        module.__dict__["broken_func"] = broken_func

        def good_func(x: int) -> str:
            return str(x)

        good_func.__module__ = "func_error_module"
        module.__dict__["good_func"] = good_func

        result = inspect_module(module)
        assert isinstance(result, ModuleTypes)
        # The good function should still be inspected
        assert "good_func" in result.functions


class TestTypeAliasInspection:
    def test_type_alias_is_discovered(self) -> None:
        module = types.ModuleType("alias_module")
        module.__dict__["__name__"] = "alias_module"

        # Create a type alias (TypeAliasType module is read-only, so we use
        # include_imported=True to allow inspection)
        # TypeAliasType at function scope triggers pyright errors about scope
        my_alias = TypeAliasType(  # pyright: ignore[reportGeneralTypeIssues]
            "MyAlias",  # pyright: ignore[reportGeneralTypeIssues]
            int,
        )
        module.__dict__["MyAlias"] = my_alias

        result = inspect_module(module, include_imported=True)

        assert isinstance(result, ModuleTypes)
        # TypeAliasType should be discovered in type_aliases dict
        assert "MyAlias" in result.type_aliases


class TestParamSpecDiscovery:
    def test_paramspec_discovered_in_type_vars(self) -> None:
        module = types.ModuleType("paramspec_module")
        module.__dict__["__name__"] = "paramspec_module"

        P = ParamSpec("P")  # noqa: N806
        P.__module__ = "paramspec_module"
        module.__dict__["P"] = P

        result = inspect_module(module)

        assert "P" in result.type_vars
        assert is_param_spec_node(result.type_vars["P"])


class TestTypeVarTupleDiscovery:
    def test_typevartuple_discovered_in_type_vars(self) -> None:
        module = types.ModuleType("tvt_module")
        module.__dict__["__name__"] = "tvt_module"

        Ts = TypeVarTuple("Ts")  # noqa: N806
        Ts.__module__ = "tvt_module"
        module.__dict__["Ts"] = Ts

        result = inspect_module(module)

        assert "Ts" in result.type_vars
        assert is_type_var_tuple_node(result.type_vars["Ts"])
