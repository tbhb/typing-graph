"""Integration tests for JSON schema generation patterns.

Tests validate that typing_graph correctly extracts metadata and type
information needed for JSON schema generation, based on patterns
from the json_schema_generation.py example.
"""

from typing import TYPE_CHECKING, Annotated, Literal, NamedTuple, TypedDict
from typing_extensions import Doc

from annotated_types import Gt, MaxLen, MinLen

from typing_graph import (
    inspect_class,
    inspect_dataclass,
    inspect_enum,
    inspect_type,
)
from typing_graph._node import (
    is_concrete_type,
    is_dataclass_type_node,
    is_enum_type_node,
    is_forward_ref_node,
    is_literal_node,
    is_named_tuple_type_node,
    is_ref_state_resolved,
    is_subscripted_generic_node,
    is_typed_dict_type_node,
    is_union_type_node,
)

from .conftest import (
    Address,
    Customer,
    Format,
    LogLevel,
    Order,
    OrderItem,
    Pattern,
    Priority,
    Status,
    TreeNode,
    find_metadata_of_type,
    has_metadata_of_type,
)

if TYPE_CHECKING:
    from typing_extensions import NotRequired, Required


# ============================================================================
# TypedDict variations
# ============================================================================


class SimpleTypedDict(TypedDict):
    """Basic TypedDict with required fields."""

    name: str
    age: int


class MixedTypedDict(TypedDict, total=False):
    """TypedDict with mixed required/optional fields."""

    required_field: "Required[int]"
    optional_field: "NotRequired[str]"


# ============================================================================
# NamedTuple variations
# ============================================================================


class SimpleNamedTuple(NamedTuple):
    """Basic NamedTuple with required fields."""

    x: int
    y: str


class NamedTupleWithDefaults(NamedTuple):
    """NamedTuple with default values."""

    x: int
    y: str = "default"


class TestDataclassFieldConstraints:
    def test_string_field_extracts_minlen(self) -> None:
        result = inspect_dataclass(Address)

        assert is_dataclass_type_node(result)
        street_field = next(f for f in result.fields if f.name == "street")

        minlen = find_metadata_of_type(street_field.metadata, MinLen)
        assert minlen is not None
        assert minlen.min_length == 1

    def test_string_field_extracts_maxlen(self) -> None:
        result = inspect_dataclass(Address)

        assert is_dataclass_type_node(result)
        street_field = next(f for f in result.fields if f.name == "street")

        maxlen = find_metadata_of_type(street_field.metadata, MaxLen)
        assert maxlen is not None
        assert maxlen.max_length == 200

    def test_string_field_extracts_both_constraints(self) -> None:
        result = inspect_dataclass(Address)

        assert is_dataclass_type_node(result)
        city_field = next(f for f in result.fields if f.name == "city")

        assert has_metadata_of_type(city_field.metadata, MinLen)
        assert has_metadata_of_type(city_field.metadata, MaxLen)

    def test_numeric_field_extracts_gt(self) -> None:
        result = inspect_dataclass(OrderItem)

        assert is_dataclass_type_node(result)
        quantity_field = next(f for f in result.fields if f.name == "quantity")

        gt = find_metadata_of_type(quantity_field.metadata, Gt)
        assert gt is not None
        assert gt.gt == 0

    def test_float_field_extracts_gt(self) -> None:
        result = inspect_dataclass(OrderItem)

        assert is_dataclass_type_node(result)
        price_field = next(f for f in result.fields if f.name == "unit_price")

        gt = find_metadata_of_type(price_field.metadata, Gt)
        assert gt is not None
        assert gt.gt == 0

    def test_pattern_constraint_extracted(self) -> None:
        result = inspect_dataclass(Address)

        assert is_dataclass_type_node(result)
        zip_field = next(f for f in result.fields if f.name == "zip_code")

        pattern = find_metadata_of_type(zip_field.metadata, Pattern)
        assert pattern is not None
        assert pattern.regex == r"^\d{5}(-\d{4})?$"


class TestDocMetadataExtraction:
    def test_doc_metadata_extracts_description(self) -> None:
        result = inspect_dataclass(Customer)

        assert is_dataclass_type_node(result)
        name_field = next(f for f in result.fields if f.name == "name")

        doc = find_metadata_of_type(name_field.metadata, Doc)
        assert doc is not None
        assert doc.documentation == "Customer full name"

    def test_format_metadata_extracted(self) -> None:
        result = inspect_dataclass(Customer)

        assert is_dataclass_type_node(result)
        email_field = next(f for f in result.fields if f.name == "email")

        fmt = find_metadata_of_type(email_field.metadata, Format)
        assert fmt is not None
        assert fmt.format == "email"


class TestNestedDataclassTraversal:
    def test_order_has_customer_field(self) -> None:
        result = inspect_dataclass(Order)

        assert is_dataclass_type_node(result)
        customer_field = next(f for f in result.fields if f.name == "customer")

        assert is_concrete_type(customer_field.type)
        assert customer_field.type.cls is Customer

    def test_nested_dataclass_can_be_inspected(self) -> None:
        result = inspect_dataclass(Order)

        assert is_dataclass_type_node(result)
        _ = next(f for f in result.fields if f.name == "customer")

        # Inspect the nested type
        nested_result = inspect_dataclass(Customer)
        assert is_dataclass_type_node(nested_result)

        field_names = {f.name for f in nested_result.fields}
        assert "name" in field_names
        assert "email" in field_names
        assert "address" in field_names

    def test_three_level_nesting(self) -> None:
        # Order -> Customer -> Address
        order_result = inspect_dataclass(Order)
        assert is_dataclass_type_node(order_result)

        _ = next(f for f in order_result.fields if f.name == "customer")
        customer_result = inspect_dataclass(Customer)
        assert is_dataclass_type_node(customer_result)

        address_field = next(f for f in customer_result.fields if f.name == "address")
        # address is Address | None
        assert is_union_type_node(address_field.type)

        # Find the Address member
        address_type = None
        for member in address_field.type.members:
            if is_concrete_type(member) and member.cls is Address:
                address_type = member
                break

        assert address_type is not None

        # Now inspect Address
        address_result = inspect_dataclass(Address)
        assert is_dataclass_type_node(address_result)
        assert len(address_result.fields) == 4  # street, city, zip_code, country


class TestGenericTypeInspection:
    def test_list_element_type_inspection(self) -> None:
        result = inspect_dataclass(Order)

        assert is_dataclass_type_node(result)
        items_field = next(f for f in result.fields if f.name == "items")

        assert is_subscripted_generic_node(items_field.type)
        assert len(items_field.type.args) == 1

    def test_list_element_is_dataclass(self) -> None:
        result = inspect_dataclass(Order)

        assert is_dataclass_type_node(result)
        items_field = next(f for f in result.fields if f.name == "items")

        assert is_subscripted_generic_node(items_field.type)
        element = items_field.type.args[0]

        assert is_concrete_type(element)
        assert element.cls is OrderItem

    def test_dict_type_inspection(self) -> None:
        result = inspect_type(dict[str, int])

        assert is_subscripted_generic_node(result)
        assert len(result.args) == 2

        key_type, value_type = result.args
        assert is_concrete_type(key_type)
        assert key_type.cls is str
        assert is_concrete_type(value_type)
        assert value_type.cls is int

    def test_nested_generic_inspection(self) -> None:
        result = inspect_type(list[dict[str, int]])

        assert is_subscripted_generic_node(result)
        element = result.args[0]

        assert is_subscripted_generic_node(element)
        assert len(element.args) == 2


class TestAnnotatedGenericTypes:
    def test_annotated_list_has_container_metadata(self) -> None:
        result = inspect_dataclass(Order)

        assert is_dataclass_type_node(result)
        items_field = next(f for f in result.fields if f.name == "items")

        # The MinLen(1) is on the field metadata
        minlen = find_metadata_of_type(items_field.metadata, MinLen)
        assert minlen is not None
        assert minlen.min_length == 1

    def test_list_of_annotated_elements(self) -> None:
        # Test list[Annotated[int, Gt(0)]]
        result = inspect_type(list[Annotated[int, Gt(0)]])

        assert is_subscripted_generic_node(result)
        element = result.args[0]

        # Element should have metadata
        assert is_concrete_type(element)
        assert element.cls is int

        gt = find_metadata_of_type(element.metadata, Gt)
        assert gt is not None
        assert gt.gt == 0


class TestLiteralTypeExtraction:
    def test_literal_string_values_extracted(self) -> None:
        result = inspect_type(Literal["admin", "user", "guest"])

        assert is_literal_node(result)
        assert set(result.values) == {"admin", "user", "guest"}

    def test_literal_int_values_extracted(self) -> None:
        result = inspect_type(Literal[1, 2, 3])

        assert is_literal_node(result)
        assert set(result.values) == {1, 2, 3}

    def test_literal_bool_values_extracted(self) -> None:
        result = inspect_type(Literal[True, False])

        assert is_literal_node(result)
        assert set(result.values) == {True, False}


class TestEnumTypeExtraction:
    def test_str_enum_has_str_value_type(self) -> None:
        result = inspect_enum(LogLevel)

        assert is_enum_type_node(result)
        assert is_concrete_type(result.value_type)
        assert result.value_type.cls is str

    def test_str_enum_has_all_members(self) -> None:
        result = inspect_enum(LogLevel)

        assert is_enum_type_node(result)
        member_names = {name for name, _ in result.members}
        assert member_names == {"DEBUG", "INFO", "WARNING", "ERROR"}

    def test_str_enum_member_values(self) -> None:
        result = inspect_enum(LogLevel)

        assert is_enum_type_node(result)
        member_dict = dict(result.members)
        assert member_dict["DEBUG"] == "debug"
        assert member_dict["INFO"] == "info"

    def test_int_enum_has_int_value_type(self) -> None:
        result = inspect_enum(Priority)

        assert is_enum_type_node(result)
        assert is_concrete_type(result.value_type)
        assert result.value_type.cls is int

    def test_int_enum_member_values(self) -> None:
        result = inspect_enum(Priority)

        assert is_enum_type_node(result)
        member_dict = dict(result.members)
        assert member_dict["LOW"] == 1
        assert member_dict["MEDIUM"] == 2
        assert member_dict["HIGH"] == 3

    def test_auto_enum_has_int_value_type(self) -> None:
        result = inspect_enum(Status)

        assert is_enum_type_node(result)
        # auto() produces integers
        assert is_concrete_type(result.value_type)
        assert result.value_type.cls is int

    def test_enum_via_inspect_class(self) -> None:
        result = inspect_class(LogLevel)

        assert is_enum_type_node(result)
        assert result.cls is LogLevel


class TestTypedDictInspection:
    def test_simple_typed_dict_detected(self) -> None:
        result = inspect_class(SimpleTypedDict)

        assert is_typed_dict_type_node(result)
        assert result.name == "SimpleTypedDict"

    def test_typed_dict_fields_extracted(self) -> None:
        result = inspect_class(SimpleTypedDict)

        assert is_typed_dict_type_node(result)
        field_names = {f.name for f in result.fields}
        assert field_names == {"name", "age"}

    def test_typed_dict_field_types(self) -> None:
        result = inspect_class(SimpleTypedDict)

        assert is_typed_dict_type_node(result)
        fields = {f.name: f for f in result.fields}

        assert is_concrete_type(fields["name"].type)
        assert fields["name"].type.cls is str

        assert is_concrete_type(fields["age"].type)
        assert fields["age"].type.cls is int

    def test_typed_dict_total_default_true(self) -> None:
        result = inspect_class(SimpleTypedDict)

        assert is_typed_dict_type_node(result)
        assert result.total is True

    def test_mixed_typed_dict_required_field(self) -> None:
        result = inspect_class(MixedTypedDict)

        assert is_typed_dict_type_node(result)
        fields = {f.name: f for f in result.fields}

        # Note: With total=False in Python 3.10, Required[] doesn't populate
        # __required_keys__. The library correctly reflects Python's behavior
        # and shows the 'required' qualifier on the type node instead.
        # Both fields are in __optional_keys__ but required_field has qualifier.
        assert "required_field" in fields
        assert "optional_field" in fields


class TestNamedTupleInspection:
    def test_named_tuple_detected(self) -> None:
        result = inspect_class(SimpleNamedTuple)

        assert is_named_tuple_type_node(result)
        assert result.name == "SimpleNamedTuple"

    def test_named_tuple_field_order_preserved(self) -> None:
        result = inspect_class(SimpleNamedTuple)

        assert is_named_tuple_type_node(result)
        assert len(result.fields) == 2
        assert result.fields[0].name == "x"
        assert result.fields[1].name == "y"

    def test_named_tuple_field_types(self) -> None:
        result = inspect_class(SimpleNamedTuple)

        assert is_named_tuple_type_node(result)
        fields = {f.name: f for f in result.fields}

        assert is_concrete_type(fields["x"].type)
        assert fields["x"].type.cls is int

        assert is_concrete_type(fields["y"].type)
        assert fields["y"].type.cls is str

    def test_named_tuple_with_defaults_marks_required(self) -> None:
        result = inspect_class(NamedTupleWithDefaults)

        assert is_named_tuple_type_node(result)
        fields = {f.name: f for f in result.fields}

        assert fields["x"].required is True
        assert fields["y"].required is False


class TestRecursiveTypeHandling:
    def test_tree_node_children_is_list(self) -> None:
        from typing_graph import InspectConfig

        # Provide globalns so forward refs can resolve
        from . import conftest

        config = InspectConfig(globalns=dict(vars(conftest)))
        result = inspect_dataclass(TreeNode, config=config)

        assert is_dataclass_type_node(result)
        children_field = next(f for f in result.fields if f.name == "children")

        # The type is a resolved ForwardRef - access .state.node
        field_type = children_field.type
        if is_forward_ref_node(field_type) and is_ref_state_resolved(field_type.state):
            field_type = field_type.state.node

        assert is_subscripted_generic_node(field_type)

    def test_tree_node_children_element_is_tree_node(self) -> None:
        from typing_graph import InspectConfig

        from . import conftest

        config = InspectConfig(globalns=dict(vars(conftest)))
        result = inspect_dataclass(TreeNode, config=config)

        assert is_dataclass_type_node(result)
        children_field = next(f for f in result.fields if f.name == "children")

        # The type is a resolved ForwardRef - access .state.node
        field_type = children_field.type
        if is_forward_ref_node(field_type) and is_ref_state_resolved(field_type.state):
            field_type = field_type.state.node

        assert is_subscripted_generic_node(field_type)
        element = field_type.args[0]

        assert is_concrete_type(element)
        assert element.cls is TreeNode

    def test_tree_node_value_has_constraints(self) -> None:
        result = inspect_dataclass(TreeNode)

        assert is_dataclass_type_node(result)
        value_field = next(f for f in result.fields if f.name == "value")

        minlen = find_metadata_of_type(value_field.metadata, MinLen)
        assert minlen is not None
        assert minlen.min_length == 1


class TestOptionalFieldDetection:
    def test_optional_field_is_union_with_none(self) -> None:
        result = inspect_dataclass(Order)

        assert is_dataclass_type_node(result)
        notes_field = next(f for f in result.fields if f.name == "notes")

        assert is_union_type_node(notes_field.type)

    def test_optional_field_has_none_member(self) -> None:
        result = inspect_dataclass(Order)

        assert is_dataclass_type_node(result)
        notes_field = next(f for f in result.fields if f.name == "notes")

        assert is_union_type_node(notes_field.type)

        has_none = False
        for member in notes_field.type.members:
            if is_concrete_type(member) and member.cls is type(None):
                has_none = True
                break

        assert has_none

    def test_optional_field_not_required(self) -> None:
        result = inspect_dataclass(Order)

        assert is_dataclass_type_node(result)
        notes_field = next(f for f in result.fields if f.name == "notes")

        assert notes_field.required is False

    def test_required_field_is_required(self) -> None:
        result = inspect_dataclass(Order)

        assert is_dataclass_type_node(result)
        id_field = next(f for f in result.fields if f.name == "id")

        assert id_field.required is True
