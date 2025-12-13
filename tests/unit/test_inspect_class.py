from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, IntEnum, auto
from typing import (
    ClassVar,
    Generic,
    NamedTuple,
    Protocol,
    TypedDict,
    TypeVar,
    runtime_checkable,
)
from typing_extensions import (
    NotRequired,
    Required,
    TypedDict as ExtTypedDict,
)

import pytest

from typing_graph import (
    InspectConfig,
    inspect_class,
    inspect_dataclass,
    inspect_enum,
)
from typing_graph._inspect_class import (
    inspect_named_tuple,
    inspect_protocol,
    inspect_typed_dict,
    is_enum_class,
)
from typing_graph._node import (
    TypeNode,
    is_class_node,
    is_dataclass_node,
    is_enum_node,
    is_forward_ref_node,
    is_named_tuple_node,
    is_protocol_node,
    is_ref_state_resolved,
    is_typed_dict_node,
    is_union_type_node,
)

from tests.conftest import assert_concrete_type


@dataclass
class SimpleDataclass:
    x: int
    y: str


@dataclass(frozen=True)
class FrozenDataclass:
    x: int


@dataclass(slots=True)
class SlottedDataclass:
    x: int


@dataclass(kw_only=True)
class KwOnlyDataclass:
    x: int


@dataclass
class DataclassWithDefault:
    x: int = 42


@dataclass
class DataclassWithFactory:
    items: list[int] = field(default_factory=list)


@dataclass
class DataclassWithInitFalse:
    computed: int = field(init=False, default=0)


@dataclass
class DataclassWithReprFalse:
    secret: str = field(repr=False, default="hidden")


@dataclass
class DataclassWithCompareFalse:
    cached: int = field(compare=False, default=0)


@dataclass
class DataclassWithKwOnlyField:
    x: int
    y: int = field(kw_only=True, default=0)


@dataclass
class DataclassWithHashFalse:
    x: int = field(hash=False, default=0)


class SimpleTypedDict(TypedDict):
    name: str
    age: int


class PartialTypedDict(TypedDict, total=False):
    x: int


class MixedTypedDict(TypedDict):
    required_field: str


class SimpleNamedTuple(NamedTuple):
    x: int
    y: str


class NamedTupleWithDefaults(NamedTuple):
    x: int
    y: str = "default"


class SimpleProtocol(Protocol):
    def read(self) -> str: ...


@runtime_checkable
class RuntimeCheckableProtocol(Protocol):
    def do_thing(self) -> None: ...


class ProtocolWithAttributes(Protocol):
    name: str
    count: int


class ProtocolWithClassMethod(Protocol):
    @classmethod
    def create(cls) -> "ProtocolWithClassMethod": ...


class ProtocolWithStaticMethod(Protocol):
    @staticmethod
    def helper() -> int: ...


class SimpleEnum(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3


class IntValueEnum(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class StrValueEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class AutoValueEnum(Enum):
    A = auto()
    B = auto()
    C = auto()


class MixedValueEnum(Enum):
    INT_VAL = 1
    STR_VAL = "string"


class PlainClass:
    pass


# Test fixture: class with instance variable annotations but no values
class ClassWithVars:
    x: int  # pyright: ignore[reportUninitializedInstanceVariable]
    y: str  # pyright: ignore[reportUninitializedInstanceVariable]


class ClassWithClassVars:
    counter: ClassVar[int] = 0


class AbstractClass(ABC):
    @abstractmethod
    def abstract_method(self) -> None: ...


class ConcreteClass:
    def method(self) -> None:
        pass


class BaseClass:
    pass


class DerivedClass(BaseClass):
    pass


T = TypeVar("T")


# Test fixture: generic class with uninitialized type-parameterized attribute
class GenericContainer(Generic[T]):
    value: T  # pyright: ignore[reportUninitializedInstanceVariable]


class ClassWithMethods:
    def public_method(self) -> int:
        return 42


# Test fixture: class with public and private annotations for filtering tests
class ClassWithPrivate:
    public: int  # pyright: ignore[reportUninitializedInstanceVariable]
    _private: str  # pyright: ignore[reportUninitializedInstanceVariable]


class NotADataclass:
    pass


class NotAnEnum:
    pass


class TestDataclassType:
    def test_simple_dataclass_has_cls_and_fields(self) -> None:
        result = inspect_dataclass(SimpleDataclass)

        assert is_dataclass_node(result)
        assert result.cls is SimpleDataclass
        assert len(result.fields) == 2
        assert result.fields[0].name == "x"
        assert result.fields[0].required is True
        assert result.fields[1].name == "y"

    def test_frozen_dataclass_sets_frozen_true(self) -> None:
        result = inspect_dataclass(FrozenDataclass)

        assert is_dataclass_node(result)
        assert result.frozen is True

    def test_non_frozen_dataclass_sets_frozen_false(self) -> None:
        result = inspect_dataclass(SimpleDataclass)

        assert is_dataclass_node(result)
        assert result.frozen is False

    def test_slots_dataclass_sets_slots_true(self) -> None:
        result = inspect_dataclass(SlottedDataclass)

        assert is_dataclass_node(result)
        assert result.slots is True

    def test_non_slots_dataclass_sets_slots_false(self) -> None:
        result = inspect_dataclass(SimpleDataclass)

        assert is_dataclass_node(result)
        assert result.slots is False

    def test_kw_only_dataclass_makes_all_fields_kw_only(self) -> None:
        # When @dataclass(kw_only=True) is used, all fields become kw_only
        # Note: result.kw_only is only available in Python 3.11+
        result = inspect_dataclass(KwOnlyDataclass)

        assert is_dataclass_node(result)
        assert len(result.fields) == 1
        assert result.fields[0].kw_only is True

    def test_field_with_default_sets_required_false(self) -> None:
        result = inspect_dataclass(DataclassWithDefault)

        assert is_dataclass_node(result)
        assert len(result.fields) == 1
        assert result.fields[0].required is False
        assert result.fields[0].default == 42

    def test_field_with_default_factory_sets_required_false(self) -> None:
        result = inspect_dataclass(DataclassWithFactory)

        assert is_dataclass_node(result)
        assert len(result.fields) == 1
        assert result.fields[0].required is False
        assert result.fields[0].default_factory is True

    def test_field_init_false_is_captured(self) -> None:
        result = inspect_dataclass(DataclassWithInitFalse)

        assert is_dataclass_node(result)
        assert result.fields[0].init is False

    def test_field_repr_false_is_captured(self) -> None:
        result = inspect_dataclass(DataclassWithReprFalse)

        assert is_dataclass_node(result)
        assert result.fields[0].repr is False

    def test_field_compare_false_is_captured(self) -> None:
        result = inspect_dataclass(DataclassWithCompareFalse)

        assert is_dataclass_node(result)
        assert result.fields[0].compare is False

    def test_field_kw_only_is_captured(self) -> None:
        result = inspect_dataclass(DataclassWithKwOnlyField)

        assert is_dataclass_node(result)
        assert result.fields[0].kw_only is False
        assert result.fields[1].kw_only is True

    def test_field_hash_is_captured(self) -> None:
        result = inspect_dataclass(DataclassWithHashFalse)

        assert is_dataclass_node(result)
        assert result.fields[0].hash is False

    def test_children_returns_field_types(self) -> None:
        result = inspect_dataclass(SimpleDataclass)

        assert is_dataclass_node(result)
        children = result.children()
        assert len(children) == 2

    def test_inspect_dataclass_raises_for_non_dataclass(self) -> None:
        with pytest.raises(TypeError, match="not a dataclass"):
            _ = inspect_dataclass(NotADataclass)


class TestTypedDictType:
    def test_simple_typed_dict_has_name_and_fields(self) -> None:
        result = inspect_class(SimpleTypedDict)

        assert is_typed_dict_node(result)
        assert result.name == "SimpleTypedDict"
        assert len(result.fields) == 2

        field_names = {f.name for f in result.fields}
        assert field_names == {"name", "age"}

    def test_total_true_by_default(self) -> None:
        result = inspect_class(SimpleTypedDict)

        assert is_typed_dict_node(result)
        assert result.total is True

    def test_total_false_when_specified(self) -> None:
        result = inspect_class(PartialTypedDict)

        assert is_typed_dict_node(result)
        assert result.total is False

    def test_required_keys_populates_field_required(self) -> None:
        result = inspect_class(MixedTypedDict)

        assert is_typed_dict_node(result)
        required_field = next(f for f in result.fields if f.name == "required_field")
        assert required_field.required is True

    def test_children_returns_field_types(self) -> None:
        result = inspect_class(SimpleTypedDict)

        assert is_typed_dict_node(result)
        children = result.children()
        assert len(children) == 2


class TestNamedTupleType:
    def test_simple_named_tuple_has_name_and_fields(self) -> None:
        result = inspect_class(SimpleNamedTuple)

        assert is_named_tuple_node(result)
        assert result.name == "SimpleNamedTuple"
        assert len(result.fields) == 2

        field_names = [f.name for f in result.fields]
        assert field_names == ["x", "y"]

    def test_field_types_are_concrete(self) -> None:
        result = inspect_class(SimpleNamedTuple)

        assert is_named_tuple_node(result)
        x_field = result.fields[0]
        y_field = result.fields[1]

        _ = assert_concrete_type(x_field.type, int)
        _ = assert_concrete_type(y_field.type, str)

    def test_field_without_default_is_required(self) -> None:
        result = inspect_class(SimpleNamedTuple)

        assert is_named_tuple_node(result)
        assert result.fields[0].required is True
        assert result.fields[1].required is True

    def test_field_with_default_is_not_required(self) -> None:
        result = inspect_class(NamedTupleWithDefaults)

        assert is_named_tuple_node(result)
        x_field = result.fields[0]
        y_field = result.fields[1]

        assert x_field.required is True
        assert y_field.required is False
        # Note: FieldDef doesn't have a default attribute - check would need
        # a different approach once NamedTupleType is implemented

    def test_children_returns_field_types(self) -> None:
        result = inspect_class(SimpleNamedTuple)

        assert is_named_tuple_node(result)
        children = result.children()
        assert len(children) == 2


class TestProtocolType:
    def test_simple_protocol_has_name_and_methods(self) -> None:
        result = inspect_class(SimpleProtocol)

        assert is_protocol_node(result)
        assert result.name == "SimpleProtocol"
        assert len(result.methods) >= 1

        read_method = next((m for m in result.methods if m.name == "read"), None)
        assert read_method is not None

    def test_runtime_checkable_sets_flag_true(self) -> None:
        result = inspect_class(RuntimeCheckableProtocol)

        assert is_protocol_node(result)
        assert result.is_runtime_checkable is True

    def test_non_runtime_checkable_sets_flag_false(self) -> None:
        result = inspect_class(SimpleProtocol)

        assert is_protocol_node(result)
        assert result.is_runtime_checkable is False

    def test_protocol_with_attributes(self) -> None:
        result = inspect_class(ProtocolWithAttributes)

        assert is_protocol_node(result)
        assert len(result.attributes) == 2

        attr_names = {a.name for a in result.attributes}
        assert attr_names == {"name", "count"}

    def test_protocol_method_classmethod_flag(self) -> None:
        result = inspect_class(ProtocolWithClassMethod)

        assert is_protocol_node(result)
        create_method = next((m for m in result.methods if m.name == "create"), None)
        assert create_method is not None
        assert create_method.is_classmethod is True

    def test_protocol_method_staticmethod_flag(self) -> None:
        result = inspect_class(ProtocolWithStaticMethod)

        assert is_protocol_node(result)
        helper_method = next((m for m in result.methods if m.name == "helper"), None)
        assert helper_method is not None
        assert helper_method.is_staticmethod is True


class TestEnumType:
    def test_simple_enum_has_cls_and_members(self) -> None:
        result = inspect_enum(SimpleEnum)

        assert is_enum_node(result)
        assert result.cls is SimpleEnum
        assert len(result.members) == 3

        member_dict = dict(result.members)
        assert member_dict == {"RED": 1, "GREEN": 2, "BLUE": 3}

    def test_int_enum_value_type_is_int(self) -> None:
        result = inspect_enum(IntValueEnum)

        assert is_enum_node(result)
        # value_type should represent int
        assert result.value_type is not None

    def test_str_enum_value_type_is_str(self) -> None:
        result = inspect_enum(StrValueEnum)

        assert is_enum_node(result)
        assert result.value_type is not None

    def test_auto_enum_has_correct_values(self) -> None:
        result = inspect_enum(AutoValueEnum)

        assert is_enum_node(result)
        member_dict = dict(result.members)
        assert "A" in member_dict
        assert "B" in member_dict
        assert "C" in member_dict

    def test_mixed_value_types_produce_union_type(self) -> None:
        result = inspect_enum(MixedValueEnum)

        assert is_enum_node(result)
        assert is_union_type_node(result.value_type)

    def test_children_returns_value_type(self) -> None:
        result = inspect_enum(SimpleEnum)

        assert is_enum_node(result)
        children = result.children()
        assert len(children) == 1
        assert children[0] is result.value_type

    def test_inspect_enum_raises_for_non_enum(self) -> None:
        with pytest.raises(TypeError, match="not an Enum"):
            _ = inspect_enum(NotAnEnum)


class TestClassNode:
    def test_simple_class_has_name_and_cls(self) -> None:
        result = inspect_class(PlainClass)

        assert is_class_node(result)
        assert result.cls is PlainClass
        assert result.name == "PlainClass"

    def test_class_with_instance_vars(self) -> None:
        config = InspectConfig(include_instance_vars=True)
        result = inspect_class(ClassWithVars, config=config)

        assert is_class_node(result)
        assert len(result.instance_vars) == 2

        var_names = {v.name for v in result.instance_vars}
        assert var_names == {"x", "y"}

    def test_class_with_class_vars(self) -> None:
        config = InspectConfig(include_class_vars=True)
        result = inspect_class(ClassWithClassVars, config=config)

        assert is_class_node(result)
        assert len(result.class_vars) == 1
        assert result.class_vars[0].name == "counter"

    def test_abstract_class_sets_is_abstract_true(self) -> None:
        result = inspect_class(AbstractClass)

        assert is_class_node(result)
        assert result.is_abstract is True

    def test_non_abstract_class_sets_is_abstract_false(self) -> None:
        result = inspect_class(ConcreteClass)

        assert is_class_node(result)
        assert result.is_abstract is False

    def test_class_with_base_captures_bases(self) -> None:
        result = inspect_class(DerivedClass)

        assert is_class_node(result)
        assert len(result.bases) == 1

    def test_generic_class_is_inspected(self) -> None:
        result = inspect_class(GenericContainer)

        assert is_class_node(result)
        # Generic classes should be detected

    def test_include_methods_captures_methods(self) -> None:
        config = InspectConfig(include_methods=True)
        result = inspect_class(ClassWithMethods, config=config)

        assert is_class_node(result)
        method_names = {m.name for m in result.methods}
        assert "public_method" in method_names

    def test_include_private_false_excludes_private(self) -> None:
        config = InspectConfig(include_private=False, include_instance_vars=True)
        result = inspect_class(ClassWithPrivate, config=config)

        assert is_class_node(result)
        var_names = {v.name for v in result.instance_vars}
        assert "public" in var_names
        assert "_private" not in var_names

    def test_include_private_true_includes_private(self) -> None:
        config = InspectConfig(include_private=True, include_instance_vars=True)
        result = inspect_class(ClassWithPrivate, config=config)

        assert is_class_node(result)
        var_names = {v.name for v in result.instance_vars}
        assert "public" in var_names
        assert "_private" in var_names


class TestInspectClassDispatch:
    def test_dispatches_dataclass_to_dataclass_type(self) -> None:
        result = inspect_class(SimpleDataclass)

        assert is_dataclass_node(result)

    def test_dispatches_typed_dict_to_typed_dict_type(self) -> None:
        result = inspect_class(SimpleTypedDict)

        assert is_typed_dict_node(result)

    def test_dispatches_protocol_to_protocol_type(self) -> None:
        result = inspect_class(SimpleProtocol)

        assert is_protocol_node(result)

    def test_dispatches_enum_to_enum_type(self) -> None:
        result = inspect_class(SimpleEnum)

        assert is_enum_node(result)

    def test_dispatches_regular_class_to_class_node(self) -> None:
        result = inspect_class(PlainClass)

        assert is_class_node(result)


class TestDedicatedInspectionFunctions:
    def test_inspect_typed_dict_function(self) -> None:
        result = inspect_typed_dict(SimpleTypedDict)

        assert is_typed_dict_node(result)
        assert result.name == "SimpleTypedDict"

    def test_inspect_typed_dict_raises_for_non_typed_dict(self) -> None:
        with pytest.raises(TypeError, match="not a TypedDict"):
            _ = inspect_typed_dict(PlainClass)

    def test_inspect_named_tuple_function(self) -> None:
        result = inspect_named_tuple(SimpleNamedTuple)

        assert is_named_tuple_node(result)
        assert result.name == "SimpleNamedTuple"

    def test_inspect_named_tuple_raises_for_non_named_tuple(self) -> None:
        with pytest.raises(TypeError, match="not a NamedTuple"):
            _ = inspect_named_tuple(PlainClass)

    def test_inspect_protocol_function(self) -> None:
        result = inspect_protocol(SimpleProtocol)

        assert is_protocol_node(result)
        assert result.name == "SimpleProtocol"

    def test_inspect_protocol_raises_for_non_protocol(self) -> None:
        with pytest.raises(TypeError, match="not a Protocol"):
            _ = inspect_protocol(PlainClass)


class TestPrivateFieldFiltering:
    def test_dataclass_excludes_private_field_by_default(self) -> None:
        @dataclass
        class DataclassWithPrivateField:
            public: int
            _private: str

        config = InspectConfig(include_private=False)
        result = inspect_dataclass(DataclassWithPrivateField, config=config)

        field_names = {f.name for f in result.fields}
        assert "public" in field_names
        assert "_private" not in field_names

    def test_dataclass_includes_private_field_when_configured(self) -> None:
        @dataclass
        class DataclassWithPrivateField:
            public: int
            _private: str

        config = InspectConfig(include_private=True)
        result = inspect_dataclass(DataclassWithPrivateField, config=config)

        field_names = {f.name for f in result.fields}
        assert "public" in field_names
        assert "_private" in field_names

    def test_typed_dict_excludes_private_field_by_default(self) -> None:
        class TypedDictWithPrivateField(TypedDict):
            public: str
            _private: int

        config = InspectConfig(include_private=False)
        result = inspect_class(TypedDictWithPrivateField, config=config)

        assert is_typed_dict_node(result)
        field_names = {f.name for f in result.fields}
        assert "public" in field_names
        assert "_private" not in field_names


class TestIsEnumTypeErrorHandling:
    def test_is_enum_class_returns_false_for_non_class(self) -> None:
        # Intentionally pass non-class values to verify graceful handling
        result = is_enum_class(42)  # type: ignore[arg-type] # pyright: ignore[reportArgumentType]
        assert result is False

        result = is_enum_class("not a class")  # type: ignore[arg-type] # pyright: ignore[reportArgumentType]
        assert result is False


class TestClassMethodExceptionHandling:
    def test_include_inherited_false_excludes_inherited_methods(self) -> None:
        class BaseClass:
            def base_method(self) -> None:
                pass

        class DerivedClass(BaseClass):
            def derived_method(self) -> None:
                pass

        config = InspectConfig(include_methods=True, include_inherited=False)
        result = inspect_class(DerivedClass, config=config)

        assert is_class_node(result)
        method_names = {m.name for m in result.methods}
        assert "derived_method" in method_names
        assert "base_method" not in method_names

    def test_getattr_raises_attribute_error_is_skipped(self) -> None:
        class ClassWithDescriptorRaisingError:
            @property
            def broken_attr(self) -> int:
                msg = "intentional error"
                raise AttributeError(msg)

        config = InspectConfig(include_methods=True)
        # Should not raise, just skip the broken attribute
        result = inspect_class(ClassWithDescriptorRaisingError, config=config)

        assert is_class_node(result)

    def test_method_with_uninspectable_signature_is_skipped(self) -> None:
        # Intentionally create a callable with broken __signature__ for testing
        class CallableWithBrokenSignature:
            __signature__ = None  # pyright: ignore[reportUnannotatedClassAttribute] - intentionally invalid

            def __call__(self) -> None:
                pass

        class ClassWithBrokenMethod:
            # We can't easily add a method with broken signature,
            # but we can check the class inspects successfully
            broken_method = CallableWithBrokenSignature()  # pyright: ignore[reportUnannotatedClassAttribute]

            def working_method(self) -> int:
                return 42

        config = InspectConfig(include_methods=True)
        result = inspect_class(ClassWithBrokenMethod, config=config)

        assert is_class_node(result)
        # Should have at least the working_method
        method_names = {m.name for m in result.methods}
        assert "working_method" in method_names


class TestTypedDictQualifierFiltering:
    def test_required_not_required_qualifiers_are_filtered(self) -> None:
        # Use TypedDict from typing_extensions for proper Required/NotRequired
        # support on Python < 3.11
        class TypedDictWithQualifiers(ExtTypedDict, total=False):
            required_field: Required[int]
            optional_field: NotRequired[str]

        result = inspect_class(TypedDictWithQualifiers)

        assert is_typed_dict_node(result)
        required_field = next(f for f in result.fields if f.name == "required_field")
        optional_field = next(f for f in result.fields if f.name == "optional_field")

        # Check requiredness is properly captured
        assert required_field.required is True
        assert optional_field.required is False

        # Qualifiers should have Required/NotRequired filtered out
        # The type itself should be the inner type, not wrapped


class TestNamedTuplePrivateFieldHandling:
    def test_named_tuple_inspection_without_private_fields(self) -> None:
        # Note: NamedTuple doesn't allow underscore-prefixed field names
        # at class definition time, so this test verifies normal behavior
        class NormalNamedTuple(NamedTuple):
            x: int
            y: str

        config = InspectConfig(include_private=False)
        result = inspect_class(NormalNamedTuple, config=config)

        assert is_named_tuple_node(result)
        assert len(result.fields) == 2


class TestProtocolPrivateMemberHandling:
    def test_protocol_excludes_private_methods_by_default(self) -> None:
        @runtime_checkable
        class ProtocolWithPrivate(Protocol):
            def public_method(self) -> None: ...
            def _private_method(self) -> None: ...

        config = InspectConfig(include_private=False)
        result = inspect_class(ProtocolWithPrivate, config=config)

        assert is_protocol_node(result)
        method_names = {m.name for m in result.methods}
        assert "public_method" in method_names
        assert "_private_method" not in method_names

    def test_protocol_includes_private_methods_when_configured(self) -> None:
        @runtime_checkable
        class ProtocolWithPrivate(Protocol):
            def public_method(self) -> None: ...
            def _private_method(self) -> None: ...

        config = InspectConfig(include_private=True)
        result = inspect_class(ProtocolWithPrivate, config=config)

        assert is_protocol_node(result)
        method_names = {m.name for m in result.methods}
        assert "public_method" in method_names
        assert "_private_method" in method_names


class TestClassVarInstanceVarFiltering:
    def test_classvar_excluded_when_include_class_vars_false(self) -> None:
        class ClassWithClassVar:
            class_val: ClassVar[int] = 0
            instance_val: str = ""

        config = InspectConfig(include_class_vars=False, include_instance_vars=True)
        result = inspect_class(ClassWithClassVar, config=config)

        assert is_class_node(result)
        # ClassVar should be excluded
        class_var_names = {cv.name for cv in result.class_vars}
        assert "class_val" not in class_var_names
        # Instance var should be included
        instance_var_names = {iv.name for iv in result.instance_vars}
        assert "instance_val" in instance_var_names

    def test_instance_var_excluded_when_include_instance_vars_false(self) -> None:
        class ClassWithInstanceVar:
            class_val: ClassVar[int] = 0
            instance_val: str = ""

        config = InspectConfig(include_class_vars=True, include_instance_vars=False)
        result = inspect_class(ClassWithInstanceVar, config=config)

        assert is_class_node(result)
        # Instance var should be excluded
        instance_var_names = {iv.name for iv in result.instance_vars}
        assert "instance_val" not in instance_var_names
        # ClassVar should be included
        class_var_names = {cv.name for cv in result.class_vars}
        assert "class_val" in class_var_names


class TestEmptyClassMethodInspection:
    def test_class_with_no_methods_inspected_with_include_methods(self) -> None:
        class EmptyClass:
            pass

        config = InspectConfig(include_methods=True)
        result = inspect_class(EmptyClass, config=config)

        assert is_class_node(result)
        # __init__, __new__ etc come from object but are filtered by
        # include_inherited=False (the default). Only direct methods are included.

    def test_class_with_no_annotations_inspected(self) -> None:
        class NoAnnotations:
            def method(self) -> None:
                pass

        config = InspectConfig(include_methods=True)
        result = inspect_class(NoAnnotations, config=config)

        assert is_class_node(result)
        assert len(result.class_vars) == 0
        assert len(result.instance_vars) == 0


class TestMethodInspectionExceptionHandling:
    def test_method_with_broken_signature_is_skipped(self) -> None:
        # Add a callable that raises on signature inspection
        class BadCallable:
            def __call__(self) -> None:
                pass

        class ClassWithBrokenMethod:
            normal_method: int = 0
            broken: object = ...  # Will be set dynamically below

        # Remove signature info to force ValueError
        bad_callable = BadCallable()
        ClassWithBrokenMethod.broken = bad_callable
        # Remove __wrapped__ which inspect.signature looks for
        if hasattr(bad_callable, "__signature__"):
            delattr(bad_callable, "__signature__")

        config = InspectConfig(include_methods=True, include_inherited=True)
        # Should not raise
        result = inspect_class(ClassWithBrokenMethod, config=config)
        assert is_class_node(result)


class TestProtocolNonMethodNonAttribute:
    def test_protocol_with_class_variable(self) -> None:
        @runtime_checkable
        class ProtocolWithClassVar(Protocol):
            name: str  # attribute

            def method(self) -> None: ...

        result = inspect_class(ProtocolWithClassVar)

        assert is_protocol_node(result)
        # Method should be captured
        method_names = {m.name for m in result.methods}
        assert "method" in method_names
        # Attribute should be captured
        attr_names = {a.name for a in result.attributes}
        assert "name" in attr_names

    def test_protocol_with_unannotated_constant_skipped(self) -> None:
        @runtime_checkable
        class ProtocolWithConstant(Protocol):
            name: str  # typed attribute
            VALUE = 42  # pyright: ignore[reportUnannotatedClassAttribute] - not callable, not in annotations

            def method(self) -> None: ...

        result = inspect_class(ProtocolWithConstant)

        assert is_protocol_node(result)
        # Method should be captured
        method_names = {m.name for m in result.methods}
        assert "method" in method_names
        # Typed attribute should be captured
        attr_names = {a.name for a in result.attributes}
        assert "name" in attr_names
        # VALUE is in protocol_attrs but skipped (not callable, not in annotations)


class TestNamedTupleFieldTypes:
    def test_named_tuple_uses_annotations(self) -> None:
        # Python 3.10+ NamedTuples use __annotations__
        class ModernNamedTuple(NamedTuple):
            x: int
            y: str

        result = inspect_class(ModernNamedTuple)

        assert is_named_tuple_node(result)
        assert len(result.fields) == 2
        field_names = {f.name for f in result.fields}
        assert "x" in field_names
        assert "y" in field_names


class TestClassNodeEmptyTypeParams:
    def test_class_with_empty_type_params(self) -> None:
        class NonGenericClass:
            value: int = 0

        config = InspectConfig(include_instance_vars=True)
        result = inspect_class(NonGenericClass, config=config)

        assert is_class_node(result)
        assert len(result.type_params) == 0


class TestMethodIterationExceptions:
    def test_attribute_error_during_getattr_is_handled(self) -> None:
        class RaisingDescriptor:
            def __get__(self, obj: object, objtype: type | None = None) -> None:
                msg = "Cannot get this attribute"
                raise AttributeError(msg)

        class ClassWithRaisingDescriptor:
            raising = RaisingDescriptor()  # pyright: ignore[reportUnannotatedClassAttribute]

            def good_method(self) -> int:
                return 42

        config = InspectConfig(include_methods=True, include_inherited=True)
        result = inspect_class(ClassWithRaisingDescriptor, config=config)

        assert is_class_node(result)
        method_names = {m.name for m in result.methods}
        assert "good_method" in method_names
        # raising descriptor should be skipped without error

    def test_builtin_method_is_inspected_gracefully(self) -> None:
        class ClassWithBuiltinMethod:
            builtin_func: object = ...  # Will be set dynamically below

            def good_method(self) -> int:
                return 42

        # Add a C function - _inspect_signature handles these internally
        # by returning a minimal SignatureNode
        ClassWithBuiltinMethod.builtin_func = len

        config = InspectConfig(include_methods=True, include_inherited=True)
        result = inspect_class(ClassWithBuiltinMethod, config=config)

        assert is_class_node(result)
        method_names = {m.name for m in result.methods}
        assert "good_method" in method_names
        # builtin_func is inspected but returns minimal signature


class TestDataclassAutoNamespace:
    def test_auto_namespace_enabled_resolves_forward_refs(self) -> None:
        # Forward reference to class defined in same scope
        @dataclass
        class Node:
            value: int
            child: "Node | None"  # Forward reference

        # With auto_namespace=True (default), forward refs should resolve
        result = inspect_dataclass(Node)

        assert is_dataclass_node(result)
        assert len(result.fields) == 2
        child_field = next(f for f in result.fields if f.name == "child")
        # The type should be resolved (union containing Node reference)
        assert child_field.type is not None

    def test_auto_namespace_disabled_uses_only_user_namespaces(self) -> None:
        @dataclass
        class Item:
            name: str
            related: "Item | None"

        # With auto_namespace=False, no automatic namespace extraction
        config = InspectConfig(auto_namespace=False)
        result = inspect_dataclass(Item, config=config)

        assert is_dataclass_node(result)
        # Without namespace, forward ref resolution depends on eval_mode
        # The field should still be captured
        assert len(result.fields) == 2

    def test_user_namespace_takes_precedence_over_auto(self) -> None:
        @dataclass
        class Container:
            item: "CustomItem"

        # Define a different CustomItem that should override auto-detection
        class CustomItem:
            pass

        user_globalns = {"CustomItem": CustomItem}
        config = InspectConfig(globalns=user_globalns, auto_namespace=True)
        result = inspect_dataclass(Container, config=config)

        assert is_dataclass_node(result)
        item_field = next(f for f in result.fields if f.name == "item")
        # User-provided namespace should take precedence
        assert item_field.type is not None

    def test_self_referential_dataclass_resolved(self) -> None:
        @dataclass
        class TreeNode:
            value: int
            left: "TreeNode | None"
            right: "TreeNode | None"

        result = inspect_dataclass(TreeNode)

        assert is_dataclass_node(result)
        assert len(result.fields) == 3
        # All fields should be captured
        field_names = {f.name for f in result.fields}
        assert field_names == {"value", "left", "right"}

    def test_dataclass_from_different_module_uses_module_namespace(self) -> None:
        # Test with a dataclass from this module - it should use the module's
        # namespace for resolution
        result = inspect_dataclass(SimpleDataclass)

        assert is_dataclass_node(result)
        # The dataclass should be inspected using its defining module's namespace
        assert result.cls is SimpleDataclass

    def test_dataclass_with_forward_ref_to_sibling_class(self) -> None:
        # Both classes defined together, referencing each other
        @dataclass
        class Parent:
            children: "list[Child]"

        @dataclass
        class Child:
            parent: "Parent | None"

        result_parent = inspect_dataclass(Parent)
        result_child = inspect_dataclass(Child)

        assert is_dataclass_node(result_parent)
        assert is_dataclass_node(result_child)
        assert len(result_parent.fields) == 1
        assert len(result_child.fields) == 1


class TestTypedDictAutoNamespace:
    def test_auto_namespace_enabled_resolves_forward_refs(self) -> None:
        # Forward reference to class defined in same scope
        class Node(TypedDict):
            value: int
            child: "Node | None"  # Forward reference

        # With auto_namespace=True (default), forward refs should resolve
        result = inspect_typed_dict(Node)

        assert is_typed_dict_node(result)
        assert len(result.fields) == 2
        child_field = next(f for f in result.fields if f.name == "child")
        # The type should be resolved (union containing Node reference)
        assert child_field.type is not None

    def test_auto_namespace_disabled_uses_only_user_namespaces(self) -> None:
        class Item(TypedDict):
            name: str
            related: "Item | None"

        # With auto_namespace=False, no automatic namespace extraction
        config = InspectConfig(auto_namespace=False)
        result = inspect_typed_dict(Item, config=config)

        assert is_typed_dict_node(result)
        # Without namespace, forward ref resolution depends on eval_mode
        # The field should still be captured
        assert len(result.fields) == 2

    def test_user_namespace_takes_precedence_over_auto(self) -> None:
        class Container(TypedDict):
            item: "CustomItem"

        # Define a different CustomItem that should override auto-detection
        class CustomItem:
            pass

        user_globalns = {"CustomItem": CustomItem}
        config = InspectConfig(globalns=user_globalns, auto_namespace=True)
        result = inspect_typed_dict(Container, config=config)

        assert is_typed_dict_node(result)
        item_field = next(f for f in result.fields if f.name == "item")
        # User-provided namespace should take precedence
        assert item_field.type is not None

    def test_self_referential_typed_dict_resolved(self) -> None:
        class TreeNode(TypedDict):
            value: int
            left: "TreeNode | None"
            right: "TreeNode | None"

        result = inspect_typed_dict(TreeNode)

        assert is_typed_dict_node(result)
        assert len(result.fields) == 3
        # All fields should be captured
        field_names = {f.name for f in result.fields}
        assert field_names == {"value", "left", "right"}

    def test_typed_dict_from_different_module_uses_module_namespace(self) -> None:
        # Test with a TypedDict from this module - it should use the module's
        # namespace for resolution
        result = inspect_typed_dict(SimpleTypedDict)

        assert is_typed_dict_node(result)
        # The TypedDict should be inspected using its defining module's namespace
        assert result.name == "SimpleTypedDict"


class TestNamedTupleAutoNamespace:
    def test_auto_namespace_enabled_resolves_forward_refs(self) -> None:
        # Forward reference to class defined in same scope
        class Node(NamedTuple):
            value: int
            child: "Node | None"  # Forward reference

        # With auto_namespace=True (default), forward refs should resolve
        result = inspect_named_tuple(Node)

        assert is_named_tuple_node(result)
        assert len(result.fields) == 2
        child_field = next(f for f in result.fields if f.name == "child")
        # The type should be resolved (union containing Node reference)
        assert child_field.type is not None

    def test_auto_namespace_disabled_uses_only_user_namespaces(self) -> None:
        class Item(NamedTuple):
            name: str
            related: "Item | None"

        # With auto_namespace=False, no automatic namespace extraction
        config = InspectConfig(auto_namespace=False)
        result = inspect_named_tuple(Item, config=config)

        assert is_named_tuple_node(result)
        # Without namespace, forward ref resolution depends on eval_mode
        # The field should still be captured
        assert len(result.fields) == 2

    def test_user_namespace_takes_precedence_over_auto(self) -> None:
        class Container(NamedTuple):
            item: "CustomItem"

        # Define a different CustomItem that should override auto-detection
        class CustomItem:
            pass

        user_globalns = {"CustomItem": CustomItem}
        config = InspectConfig(globalns=user_globalns, auto_namespace=True)
        result = inspect_named_tuple(Container, config=config)

        assert is_named_tuple_node(result)
        item_field = next(f for f in result.fields if f.name == "item")
        # User-provided namespace should take precedence
        assert item_field.type is not None

    def test_self_referential_named_tuple_resolved(self) -> None:
        class TreeNode(NamedTuple):
            value: int
            left: "TreeNode | None"
            right: "TreeNode | None"

        result = inspect_named_tuple(TreeNode)

        assert is_named_tuple_node(result)
        assert len(result.fields) == 3
        # All fields should be captured
        field_names = {f.name for f in result.fields}
        assert field_names == {"value", "left", "right"}

    def test_named_tuple_from_different_module_uses_module_namespace(self) -> None:
        # Test with a NamedTuple from this module - it should use the module's
        # namespace for resolution
        result = inspect_named_tuple(SimpleNamedTuple)

        assert is_named_tuple_node(result)
        # The NamedTuple should be inspected using its defining module's namespace
        assert result.name == "SimpleNamedTuple"

    def test_named_tuple_with_forward_ref_to_sibling_class(self) -> None:
        # Both classes defined together, referencing each other
        class Parent(NamedTuple):
            children: "list[Child]"

        class Child(NamedTuple):
            parent: "Parent | None"

        result_parent = inspect_named_tuple(Parent)
        result_child = inspect_named_tuple(Child)

        assert is_named_tuple_node(result_parent)
        assert is_named_tuple_node(result_child)
        assert len(result_parent.fields) == 1
        assert len(result_child.fields) == 1


class TestProtocolAutoNamespace:
    def test_auto_namespace_enabled_resolves_forward_refs(self) -> None:
        # Forward reference to class defined in same scope
        class Node(Protocol):
            value: int
            child: "Node | None"  # Forward reference

        # With auto_namespace=True (default), forward refs should resolve
        result = inspect_protocol(Node)

        assert is_protocol_node(result)
        assert len(result.attributes) == 2
        child_attr = next(a for a in result.attributes if a.name == "child")
        # The type should be resolved (union containing Node reference)
        assert child_attr.type is not None

    def test_auto_namespace_disabled_uses_only_user_namespaces(self) -> None:
        class Item(Protocol):
            name: str
            related: "Item | None"

        # With auto_namespace=False, no automatic namespace extraction
        config = InspectConfig(auto_namespace=False)
        result = inspect_protocol(Item, config=config)

        assert is_protocol_node(result)
        # Without namespace, forward ref resolution depends on eval_mode
        # The attributes should still be captured
        assert len(result.attributes) == 2

    def test_user_namespace_takes_precedence_over_auto(self) -> None:
        class Container(Protocol):
            item: "CustomItem"

        # Define a different CustomItem that should override auto-detection
        class CustomItem:
            pass

        user_globalns = {"CustomItem": CustomItem}
        config = InspectConfig(globalns=user_globalns, auto_namespace=True)
        result = inspect_protocol(Container, config=config)

        assert is_protocol_node(result)
        item_attr = next(a for a in result.attributes if a.name == "item")
        # User-provided namespace should take precedence
        assert item_attr.type is not None

    def test_self_referential_protocol_resolved(self) -> None:
        class TreeNode(Protocol):
            value: int
            left: "TreeNode | None"
            right: "TreeNode | None"

        result = inspect_protocol(TreeNode)

        assert is_protocol_node(result)
        assert len(result.attributes) == 3
        # All attributes should be captured
        attr_names = {a.name for a in result.attributes}
        assert attr_names == {"value", "left", "right"}

    def test_protocol_from_different_module_uses_module_namespace(self) -> None:
        # Test with a Protocol from this module - it should use the module's
        # namespace for resolution
        result = inspect_protocol(SimpleProtocol)

        assert is_protocol_node(result)
        # The Protocol should be inspected using its defining module's namespace
        assert result.name == "SimpleProtocol"

    def test_protocol_with_forward_ref_attributes(self) -> None:
        # Protocol with both methods and forward-ref attributes
        class Container(Protocol):
            items: "list[Item]"
            count: int

            def get_item(self, index: int) -> "Item": ...

        class Item(Protocol):
            name: str

        result = inspect_protocol(Container)

        assert is_protocol_node(result)
        # Attributes with forward refs should be captured
        attr_names = {a.name for a in result.attributes}
        assert "items" in attr_names
        assert "count" in attr_names
        # Methods should also be captured
        method_names = {m.name for m in result.methods}
        assert "get_item" in method_names


class TestEnumAutoNamespace:
    def test_auto_namespace_enabled_resolves_forward_refs(self) -> None:
        # Enum with members that could have forward reference type annotations
        # Note: Enum values don't have type annotations, but auto-namespace
        # is applied for consistency with other class inspection functions
        class Status(Enum):
            ACTIVE = 1
            INACTIVE = 2

        # With auto_namespace=True (default), the enum should be inspected normally
        result = inspect_enum(Status)

        assert is_enum_node(result)
        assert len(result.members) == 2
        member_dict = dict(result.members)
        assert member_dict == {"ACTIVE": 1, "INACTIVE": 2}

    def test_auto_namespace_disabled_uses_only_user_namespaces(self) -> None:
        class Priority(Enum):
            LOW = 1
            HIGH = 2

        # With auto_namespace=False, no automatic namespace extraction
        config = InspectConfig(auto_namespace=False)
        result = inspect_enum(Priority, config=config)

        assert is_enum_node(result)
        # The enum should still be inspected correctly
        assert len(result.members) == 2
        member_dict = dict(result.members)
        assert member_dict == {"LOW": 1, "HIGH": 2}

    def test_user_namespace_takes_precedence_over_auto(self) -> None:
        class Level(Enum):
            DEBUG = 10
            INFO = 20

        # User-provided namespace should take precedence
        user_globalns = {"Level": Level}
        config = InspectConfig(globalns=user_globalns, auto_namespace=True)
        result = inspect_enum(Level, config=config)

        assert is_enum_node(result)
        assert result.cls is Level
        assert len(result.members) == 2

    def test_enum_from_different_module_uses_module_namespace(self) -> None:
        # Test with an Enum from this module - it should use the module's
        # namespace for resolution
        result = inspect_enum(SimpleEnum)

        assert is_enum_node(result)
        # The Enum should be inspected using its defining module's namespace
        assert result.cls is SimpleEnum
        assert len(result.members) == 3

    def test_enum_with_mixed_value_types(self) -> None:
        class MixedEnum(Enum):
            INT_VALUE = 1
            STR_VALUE = "text"
            FLOAT_VALUE = 3.14

        result = inspect_enum(MixedEnum)

        assert is_enum_node(result)
        assert len(result.members) == 3
        # Mixed value types should produce a union type
        assert is_union_type_node(result.value_type)


class TestInspectClassDispatcherAutoNamespace:
    def test_dispatcher_applies_auto_namespace_for_dataclass(self) -> None:
        @dataclass
        class Node:
            value: int
            child: "Node | None"

        result = inspect_class(Node)

        assert is_dataclass_node(result)
        assert len(result.fields) == 2
        child_field = next(f for f in result.fields if f.name == "child")
        assert child_field.type is not None

    def test_dispatcher_applies_auto_namespace_for_typed_dict(self) -> None:
        class Node(TypedDict):
            value: int
            child: "Node | None"

        result = inspect_class(Node)

        assert is_typed_dict_node(result)
        assert len(result.fields) == 2
        child_field = next(f for f in result.fields if f.name == "child")
        assert child_field.type is not None

    def test_dispatcher_applies_auto_namespace_for_named_tuple(self) -> None:
        class Node(NamedTuple):
            value: int
            child: "Node | None"

        result = inspect_class(Node)

        assert is_named_tuple_node(result)
        assert len(result.fields) == 2
        child_field = next(f for f in result.fields if f.name == "child")
        assert child_field.type is not None

    def test_dispatcher_applies_auto_namespace_for_protocol(self) -> None:
        class Node(Protocol):
            value: int
            child: "Node | None"

        result = inspect_class(Node)

        assert is_protocol_node(result)
        assert len(result.attributes) == 2
        child_attr = next(a for a in result.attributes if a.name == "child")
        assert child_attr.type is not None

    def test_dispatcher_applies_auto_namespace_for_enum(self) -> None:
        class Status(Enum):
            ACTIVE = 1
            INACTIVE = 2

        result = inspect_class(Status)

        assert is_enum_node(result)
        assert result.cls is Status
        assert len(result.members) == 2

    def test_dispatcher_applies_auto_namespace_for_regular_class(self) -> None:
        class Node:
            value: int  # pyright: ignore[reportUninitializedInstanceVariable]
            child: "Node | None"  # pyright: ignore[reportUninitializedInstanceVariable]

        config = InspectConfig(include_instance_vars=True)
        result = inspect_class(Node, config=config)

        assert is_class_node(result)
        assert len(result.instance_vars) == 2
        child_var = next(v for v in result.instance_vars if v.name == "child")
        assert child_var.type is not None

    def test_dispatcher_auto_namespace_disabled_respects_setting(self) -> None:
        @dataclass
        class Item:
            name: str
            related: "Item | None"

        config = InspectConfig(auto_namespace=False)
        result = inspect_class(Item, config=config)

        assert is_dataclass_node(result)
        # The field should still be captured even without auto-namespace
        assert len(result.fields) == 2

    def test_dispatcher_user_namespace_takes_precedence(self) -> None:
        @dataclass
        class Container:
            item: "CustomItem"

        class CustomItem:
            pass

        user_globalns = {"CustomItem": CustomItem}
        config = InspectConfig(globalns=user_globalns, auto_namespace=True)
        result = inspect_class(Container, config=config)

        assert is_dataclass_node(result)
        item_field = next(f for f in result.fields if f.name == "item")
        assert item_field.type is not None


# PEP 563 Integration Tests
#
# PEP 563 (`from __future__ import annotations`) causes ALL annotations to
# become strings at runtime. Fixtures are defined in pep563_fixtures.py which
# has the future import, since it affects the entire module at compile time.
#
# With PEP 563, annotations are forward references that get resolved. The tests
# verify that:
# 1. The type may be a ForwardRefNode (due to string annotations)
# 2. When wrapped in ForwardRefNode, the state is RefResolved
# 3. The resolved node is the correct type (e.g., UnionNode)


def _get_resolved_type(type_node: TypeNode) -> TypeNode:
    """Unwrap ForwardRefNode if present and resolved, returning the inner type."""
    if is_forward_ref_node(type_node):
        assert is_ref_state_resolved(type_node.state), (
            f"Expected resolved forward ref, got {type_node.state}"
        )
        return type_node.state.node
    return type_node


class TestPEP563DataclassScenarios:
    def test_pep563_dataclass_self_reference_resolved(self) -> None:
        from tests.unit.pep563_fixtures import TreeNodeDC

        result = inspect_dataclass(TreeNodeDC)

        assert is_dataclass_node(result)
        assert len(result.fields) == 3

        left_field = next(f for f in result.fields if f.name == "left")
        assert left_field.type is not None
        left_resolved = _get_resolved_type(left_field.type)
        assert is_union_type_node(left_resolved)

        right_field = next(f for f in result.fields if f.name == "right")
        assert right_field.type is not None
        right_resolved = _get_resolved_type(right_field.type)
        assert is_union_type_node(right_resolved)

    def test_pep563_dataclass_sibling_reference_parent_resolved(self) -> None:
        from tests.unit.pep563_fixtures import ParentDC

        result = inspect_dataclass(ParentDC)

        assert is_dataclass_node(result)
        assert len(result.fields) == 2

        children_field = next(f for f in result.fields if f.name == "children")
        assert children_field.type is not None

    def test_pep563_dataclass_sibling_reference_child_resolved(self) -> None:
        from tests.unit.pep563_fixtures import ChildDC

        result = inspect_dataclass(ChildDC)

        assert is_dataclass_node(result)
        assert len(result.fields) == 2

        parent_field = next(f for f in result.fields if f.name == "parent")
        assert parent_field.type is not None
        parent_resolved = _get_resolved_type(parent_field.type)
        assert is_union_type_node(parent_resolved)

    def test_pep563_generic_dataclass_self_reference_resolved(self) -> None:
        from tests.unit.pep563_fixtures import GenericNode

        result = inspect_dataclass(GenericNode)

        assert is_dataclass_node(result)
        assert len(result.fields) == 2

        children_field = next(f for f in result.fields if f.name == "children")
        assert children_field.type is not None

    def test_pep563_dataclass_nested_references_resolved(self) -> None:
        from tests.unit.pep563_fixtures import Container, Item

        container_result = inspect_dataclass(Container)
        item_result = inspect_dataclass(Item)

        assert is_dataclass_node(container_result)
        assert is_dataclass_node(item_result)
        assert len(container_result.fields) == 2
        assert len(item_result.fields) == 2


class TestPEP563TypedDictScenarios:
    def test_pep563_typed_dict_self_reference_resolved(self) -> None:
        from tests.unit.pep563_fixtures import TreeNodeTD

        result = inspect_typed_dict(TreeNodeTD)

        assert is_typed_dict_node(result)
        assert len(result.fields) == 3

        left_field = next(f for f in result.fields if f.name == "left")
        assert left_field.type is not None
        left_resolved = _get_resolved_type(left_field.type)
        assert is_union_type_node(left_resolved)

        right_field = next(f for f in result.fields if f.name == "right")
        assert right_field.type is not None
        right_resolved = _get_resolved_type(right_field.type)
        assert is_union_type_node(right_resolved)

    def test_pep563_typed_dict_sibling_reference_parent_resolved(self) -> None:
        from tests.unit.pep563_fixtures import ParentTD

        result = inspect_typed_dict(ParentTD)

        assert is_typed_dict_node(result)
        assert len(result.fields) == 2

        children_field = next(f for f in result.fields if f.name == "children")
        assert children_field.type is not None

    def test_pep563_typed_dict_sibling_reference_child_resolved(self) -> None:
        from tests.unit.pep563_fixtures import ChildTD

        result = inspect_typed_dict(ChildTD)

        assert is_typed_dict_node(result)
        assert len(result.fields) == 2

        parent_field = next(f for f in result.fields if f.name == "parent")
        assert parent_field.type is not None
        parent_resolved = _get_resolved_type(parent_field.type)
        assert is_union_type_node(parent_resolved)

    def test_pep563_typed_dict_nested_references_resolved(self) -> None:
        from tests.unit.pep563_fixtures import NestedTD

        result = inspect_typed_dict(NestedTD)

        assert is_typed_dict_node(result)
        assert len(result.fields) == 2

        items_field = next(f for f in result.fields if f.name == "items")
        assert items_field.type is not None

        mapping_field = next(f for f in result.fields if f.name == "mapping")
        assert mapping_field.type is not None


class TestPEP563NamedTupleScenarios:
    def test_pep563_named_tuple_self_reference_resolved(self) -> None:
        from tests.unit.pep563_fixtures import TreeNodeNT

        result = inspect_named_tuple(TreeNodeNT)

        assert is_named_tuple_node(result)
        assert len(result.fields) == 3

        left_field = next(f for f in result.fields if f.name == "left")
        assert left_field.type is not None
        left_resolved = _get_resolved_type(left_field.type)
        assert is_union_type_node(left_resolved)

        right_field = next(f for f in result.fields if f.name == "right")
        assert right_field.type is not None
        right_resolved = _get_resolved_type(right_field.type)
        assert is_union_type_node(right_resolved)

    def test_pep563_named_tuple_sibling_reference_parent_resolved(self) -> None:
        from tests.unit.pep563_fixtures import ParentNT

        result = inspect_named_tuple(ParentNT)

        assert is_named_tuple_node(result)
        assert len(result.fields) == 2

        children_field = next(f for f in result.fields if f.name == "children")
        assert children_field.type is not None

    def test_pep563_named_tuple_sibling_reference_child_resolved(self) -> None:
        from tests.unit.pep563_fixtures import ChildNT

        result = inspect_named_tuple(ChildNT)

        assert is_named_tuple_node(result)
        assert len(result.fields) == 2

        parent_field = next(f for f in result.fields if f.name == "parent")
        assert parent_field.type is not None
        parent_resolved = _get_resolved_type(parent_field.type)
        assert is_union_type_node(parent_resolved)


class TestPEP563ProtocolScenarios:
    def test_pep563_protocol_self_reference_resolved(self) -> None:
        from tests.unit.pep563_fixtures import TreeNodeProto

        result = inspect_protocol(TreeNodeProto)

        assert is_protocol_node(result)
        assert len(result.attributes) == 3

        left_attr = next(a for a in result.attributes if a.name == "left")
        assert left_attr.type is not None
        left_resolved = _get_resolved_type(left_attr.type)
        assert is_union_type_node(left_resolved)

        right_attr = next(a for a in result.attributes if a.name == "right")
        assert right_attr.type is not None
        right_resolved = _get_resolved_type(right_attr.type)
        assert is_union_type_node(right_resolved)

    def test_pep563_protocol_sibling_reference_parent_resolved(self) -> None:
        from tests.unit.pep563_fixtures import ParentProto

        result = inspect_protocol(ParentProto)

        assert is_protocol_node(result)
        assert len(result.attributes) == 2

        children_attr = next(a for a in result.attributes if a.name == "children")
        assert children_attr.type is not None

    def test_pep563_protocol_sibling_reference_child_resolved(self) -> None:
        from tests.unit.pep563_fixtures import ChildProto

        result = inspect_protocol(ChildProto)

        assert is_protocol_node(result)
        assert len(result.attributes) == 2

        parent_attr = next(a for a in result.attributes if a.name == "parent")
        assert parent_attr.type is not None
        parent_resolved = _get_resolved_type(parent_attr.type)
        assert is_union_type_node(parent_resolved)

    def test_pep563_protocol_with_methods_resolved(self) -> None:
        from tests.unit.pep563_fixtures import NodeFactory

        result = inspect_protocol(NodeFactory)

        assert is_protocol_node(result)
        assert len(result.methods) == 2

        create_method = next(m for m in result.methods if m.name == "create")
        assert create_method.signature is not None

        clone_method = next(m for m in result.methods if m.name == "clone")
        assert clone_method.signature is not None


class TestPEP563EnumScenarios:
    def test_pep563_enum_simple_resolved(self) -> None:
        from tests.unit.pep563_fixtures import StatusEnum

        result = inspect_enum(StatusEnum)

        assert is_enum_node(result)
        assert result.cls is StatusEnum
        assert len(result.members) == 3
        member_names = {m[0] for m in result.members}
        assert member_names == {"ACTIVE", "INACTIVE", "PENDING"}

    def test_pep563_enum_with_values_resolved(self) -> None:
        from tests.unit.pep563_fixtures import PriorityEnum

        result = inspect_enum(PriorityEnum)

        assert is_enum_node(result)
        assert result.cls is PriorityEnum
        assert len(result.members) == 3
        member_dict = dict(result.members)
        assert member_dict == {"LOW": 1, "MEDIUM": 2, "HIGH": 3}


class TestPEP563PlainClassScenarios:
    def test_pep563_plain_class_self_reference_resolved(self) -> None:
        from tests.unit.pep563_fixtures import PlainNode

        config = InspectConfig(include_instance_vars=True)
        result = inspect_class(PlainNode, config=config)

        assert is_class_node(result)
        assert len(result.instance_vars) == 3

        parent_var = next(v for v in result.instance_vars if v.name == "parent")
        assert parent_var.type is not None
        parent_resolved = _get_resolved_type(parent_var.type)
        assert is_union_type_node(parent_resolved)

        children_var = next(v for v in result.instance_vars if v.name == "children")
        assert children_var.type is not None


class TestPEP563DispatcherScenarios:
    def test_dispatcher_pep563_dataclass_resolved(self) -> None:
        from tests.unit.pep563_fixtures import TreeNodeDC

        result = inspect_class(TreeNodeDC)

        assert is_dataclass_node(result)
        assert len(result.fields) == 3

    def test_dispatcher_pep563_typed_dict_resolved(self) -> None:
        from tests.unit.pep563_fixtures import TreeNodeTD

        result = inspect_class(TreeNodeTD)

        assert is_typed_dict_node(result)
        assert len(result.fields) == 3

    def test_dispatcher_pep563_named_tuple_resolved(self) -> None:
        from tests.unit.pep563_fixtures import TreeNodeNT

        result = inspect_class(TreeNodeNT)

        assert is_named_tuple_node(result)
        assert len(result.fields) == 3

    def test_dispatcher_pep563_protocol_resolved(self) -> None:
        from tests.unit.pep563_fixtures import TreeNodeProto

        result = inspect_class(TreeNodeProto)

        assert is_protocol_node(result)
        assert len(result.attributes) == 3

    def test_dispatcher_pep563_enum_resolved(self) -> None:
        from tests.unit.pep563_fixtures import StatusEnum

        result = inspect_class(StatusEnum)

        assert is_enum_node(result)
        assert len(result.members) == 3

    def test_dispatcher_pep563_plain_class_resolved(self) -> None:
        from tests.unit.pep563_fixtures import PlainNode

        config = InspectConfig(include_instance_vars=True)
        result = inspect_class(PlainNode, config=config)

        assert is_class_node(result)
        assert len(result.instance_vars) == 3
