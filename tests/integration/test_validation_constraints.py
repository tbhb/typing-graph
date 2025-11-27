"""Integration tests for recursive validation constraint discovery.

Tests validate that typing_graph correctly extracts validation constraints
at all nesting levels for recursive validation, based on patterns
from the recursive_validation.py example.
"""

from dataclasses import dataclass
from typing import Annotated
from typing_extensions import Doc

from annotated_types import Gt, Lt, MaxLen, MinLen

from typing_graph import (
    inspect_dataclass,
    inspect_type,
)
from typing_graph._node import (
    is_concrete_type,
    is_dataclass_type_node,
    is_forward_ref_node,
    is_ref_state_resolved,
    is_subscripted_generic_node,
    is_union_type_node,
)

from .conftest import (
    Address,
    Customer,
    Format,
    Order,
    OrderItem,
    Pattern,
    TreeNode,
    find_all_metadata_of_type,
    find_metadata_of_type,
    has_metadata_of_type,
)


class TestTopLevelConstraints:
    def test_direct_field_gt_constraint(self) -> None:
        result = inspect_dataclass(OrderItem)

        assert is_dataclass_type_node(result)
        quantity_field = next(f for f in result.fields if f.name == "quantity")

        gt = find_metadata_of_type(quantity_field.metadata, Gt)
        assert gt is not None
        assert gt.gt == 0

    def test_direct_field_pattern_constraint(self) -> None:
        result = inspect_dataclass(OrderItem)

        assert is_dataclass_type_node(result)
        product_field = next(f for f in result.fields if f.name == "product_id")

        pattern = find_metadata_of_type(product_field.metadata, Pattern)
        assert pattern is not None
        assert pattern.regex == r"^SKU-\d+$"

    def test_direct_field_multiple_constraints(self) -> None:
        result = inspect_dataclass(Address)

        assert is_dataclass_type_node(result)
        street_field = next(f for f in result.fields if f.name == "street")

        # Should have both MinLen and MaxLen
        minlen = find_metadata_of_type(street_field.metadata, MinLen)
        maxlen = find_metadata_of_type(street_field.metadata, MaxLen)

        assert minlen is not None
        assert minlen.min_length == 1

        assert maxlen is not None
        assert maxlen.max_length == 200

    def test_all_constraints_on_field_extracted(self) -> None:
        result = inspect_dataclass(Customer)

        assert is_dataclass_type_node(result)
        name_field = next(f for f in result.fields if f.name == "name")

        # name has MinLen(1), MaxLen(100), doc("Customer full name")
        minlen = find_metadata_of_type(name_field.metadata, MinLen)
        maxlen = find_metadata_of_type(name_field.metadata, MaxLen)
        doc_info = find_metadata_of_type(name_field.metadata, Doc)

        assert minlen is not None
        assert maxlen is not None
        assert doc_info is not None


class TestNestedFieldConstraints:
    def test_nested_dataclass_field_constraint(self) -> None:
        # Order -> Customer -> name has MinLen constraint
        order_result = inspect_dataclass(Order)
        assert is_dataclass_type_node(order_result)

        customer_field = next(f for f in order_result.fields if f.name == "customer")
        assert is_concrete_type(customer_field.type)
        assert customer_field.type.cls is Customer

        # Now inspect Customer to get name constraints
        customer_result = inspect_dataclass(Customer)
        assert is_dataclass_type_node(customer_result)

        name_field = next(f for f in customer_result.fields if f.name == "name")
        minlen = find_metadata_of_type(name_field.metadata, MinLen)
        assert minlen is not None
        assert minlen.min_length == 1

    def test_deeply_nested_constraint(self) -> None:
        # Order -> Customer -> Address -> zip_code has Pattern
        customer_result = inspect_dataclass(Customer)
        assert is_dataclass_type_node(customer_result)

        address_field = next(f for f in customer_result.fields if f.name == "address")
        # address is Address | None
        assert is_union_type_node(address_field.type)

        # Find Address type
        address_type = None
        for member in address_field.type.members:
            if is_concrete_type(member) and member.cls is Address:
                address_type = member
                break

        assert address_type is not None

        # Inspect Address
        address_result = inspect_dataclass(Address)
        assert is_dataclass_type_node(address_result)

        zip_field = next(f for f in address_result.fields if f.name == "zip_code")
        pattern = find_metadata_of_type(zip_field.metadata, Pattern)
        assert pattern is not None

    def test_constraint_discovery_path(self) -> None:
        # Test that we can discover constraints at each level
        # Level 1: Order.id has Pattern
        order_result = inspect_dataclass(Order)
        id_field = next(f for f in order_result.fields if f.name == "id")
        assert has_metadata_of_type(id_field.metadata, Pattern)

        # Level 2: Order.customer -> Customer.email has Format
        customer_result = inspect_dataclass(Customer)
        email_field = next(f for f in customer_result.fields if f.name == "email")
        assert has_metadata_of_type(email_field.metadata, Format)

        # Level 3: Customer.address -> Address.city has MinLen
        address_result = inspect_dataclass(Address)
        city_field = next(f for f in address_result.fields if f.name == "city")
        assert has_metadata_of_type(city_field.metadata, MinLen)


class TestCollectionElementConstraints:
    def test_list_has_container_constraint(self) -> None:
        result = inspect_dataclass(Order)

        assert is_dataclass_type_node(result)
        items_field = next(f for f in result.fields if f.name == "items")

        # The list has MinLen(1) on the field metadata
        minlen = find_metadata_of_type(items_field.metadata, MinLen)
        assert minlen is not None
        assert minlen.min_length == 1

    def test_list_element_type_has_constraints(self) -> None:
        # Order.items is list[OrderItem]
        # OrderItem.quantity has Gt(0)
        result = inspect_dataclass(Order)

        assert is_dataclass_type_node(result)
        items_field = next(f for f in result.fields if f.name == "items")

        assert is_subscripted_generic_node(items_field.type)
        element = items_field.type.args[0]

        assert is_concrete_type(element)
        assert element.cls is OrderItem

        # Inspect OrderItem
        item_result = inspect_dataclass(OrderItem)
        quantity_field = next(f for f in item_result.fields if f.name == "quantity")

        gt = find_metadata_of_type(quantity_field.metadata, Gt)
        assert gt is not None

    def test_list_of_annotated_elements(self) -> None:
        # list[Annotated[int, Gt(0)]]
        result = inspect_type(list[Annotated[int, Gt(0)]])

        assert is_subscripted_generic_node(result)
        element = result.args[0]

        assert is_concrete_type(element)
        gt = find_metadata_of_type(element.metadata, Gt)
        assert gt is not None
        assert gt.gt == 0

    def test_annotated_list_with_element_constraints(self) -> None:
        # Annotated[list[Annotated[str, MaxLen(100)]], MinLen(1)]
        result = inspect_type(Annotated[list[Annotated[str, MaxLen(100)]], MinLen(1)])

        # Container level
        assert is_subscripted_generic_node(result)
        container_minlen = find_metadata_of_type(result.metadata, MinLen)
        assert container_minlen is not None
        assert container_minlen.min_length == 1

        # Element level
        element = result.args[0]
        assert is_concrete_type(element)
        element_maxlen = find_metadata_of_type(element.metadata, MaxLen)
        assert element_maxlen is not None
        assert element_maxlen.max_length == 100


class TestUnionMemberConstraints:
    def test_optional_field_inner_type_accessible(self) -> None:
        result = inspect_dataclass(Customer)

        assert is_dataclass_type_node(result)
        address_field = next(f for f in result.fields if f.name == "address")

        assert is_union_type_node(address_field.type)

        # Should be able to find Address member
        address_member = None
        for member in address_field.type.members:
            if is_concrete_type(member) and member.cls is Address:
                address_member = member
                break

        assert address_member is not None

    def test_union_member_constraint_via_type_inspection(self) -> None:
        # Annotated[int | str, MinLen(1)] - metadata on union
        result = inspect_type(Annotated[int | str, MinLen(1)])

        assert is_union_type_node(result)
        minlen = find_metadata_of_type(result.metadata, MinLen)
        assert minlen is not None

    def test_constraint_on_individual_union_member(self) -> None:
        # Union where one member has constraints
        # Note: The representation varies by Python version:
        # - Python < 3.14: SubscriptedGeneric(Union) with .args
        # - Python 3.14+: UnionType with .members
        result = inspect_type(Annotated[int, Gt(0)] | str)

        # Accept either representation
        assert is_subscripted_generic_node(result) or is_union_type_node(result)

        # Get union members - handle both node types
        members = result.args if is_subscripted_generic_node(result) else result.members

        # Find the int member
        int_member = None
        for member in members:
            if is_concrete_type(member) and member.cls is int:
                int_member = member
                break

        assert int_member is not None
        gt = find_metadata_of_type(int_member.metadata, Gt)
        assert gt is not None


class TestRecursiveTypeConstraints:
    def test_tree_node_value_constraint(self) -> None:
        result = inspect_dataclass(TreeNode)

        assert is_dataclass_type_node(result)
        value_field = next(f for f in result.fields if f.name == "value")

        minlen = find_metadata_of_type(value_field.metadata, MinLen)
        assert minlen is not None
        assert minlen.min_length == 1

    def test_tree_node_children_element_is_self(self) -> None:
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

        # Element is TreeNode itself
        assert is_concrete_type(element)
        assert element.cls is TreeNode

    def test_recursive_type_constraint_accessible(self) -> None:
        from typing_graph import InspectConfig

        from . import conftest

        config = InspectConfig(globalns=dict(vars(conftest)))
        # Inspecting the child TreeNode should give same constraints
        result = inspect_dataclass(TreeNode, config=config)

        children_field = next(f for f in result.fields if f.name == "children")

        # The type is a resolved ForwardRef - access .state.node
        field_type = children_field.type
        if is_forward_ref_node(field_type) and is_ref_state_resolved(field_type.state):
            field_type = field_type.state.node

        assert is_subscripted_generic_node(field_type)
        _ = field_type.args[0]  # Element is TreeNode

        # The element is TreeNode - if we inspect it, same constraints
        child_result = inspect_dataclass(TreeNode)
        assert is_dataclass_type_node(child_result)

        value_field = next(f for f in child_result.fields if f.name == "value")
        minlen = find_metadata_of_type(value_field.metadata, MinLen)
        assert minlen is not None


class TestConstraintCounting:
    def test_count_constraints_on_dataclass(self) -> None:
        result = inspect_dataclass(Address)

        assert is_dataclass_type_node(result)

        total_constraints = 0
        for field_def in result.fields:
            total_constraints += len(
                find_all_metadata_of_type(field_def.metadata, MinLen)
            )
            total_constraints += len(
                find_all_metadata_of_type(field_def.metadata, MaxLen)
            )
            total_constraints += len(
                find_all_metadata_of_type(field_def.metadata, Pattern)
            )

        # street: MinLen, MaxLen (2)
        # city: MinLen, MaxLen (2)
        # zip_code: Pattern (1)
        # country: MinLen, MaxLen (2)
        assert total_constraints == 7

    def test_find_all_gt_constraints(self) -> None:
        result = inspect_dataclass(OrderItem)

        assert is_dataclass_type_node(result)

        gt_constraints: list[Gt] = []
        for field_def in result.fields:
            gt_constraints.extend(find_all_metadata_of_type(field_def.metadata, Gt))

        # quantity: Gt(0), unit_price: Gt(0)
        assert len(gt_constraints) == 2


class TestDynamicTypeConstraints:
    def test_dynamically_defined_type_with_constraints(self) -> None:
        @dataclass
        class DynamicData:
            value: Annotated[int, Gt(0), Lt(100)]
            name: Annotated[str, MinLen(1), MaxLen(50)]

        result = inspect_dataclass(DynamicData)
        assert is_dataclass_type_node(result)

        value_field = next(f for f in result.fields if f.name == "value")
        gt = find_metadata_of_type(value_field.metadata, Gt)
        lt = find_metadata_of_type(value_field.metadata, Lt)

        assert gt is not None
        assert gt.gt == 0
        assert lt is not None
        assert lt.lt == 100

    def test_nested_annotated_in_dynamic_type(self) -> None:
        @dataclass
        class Container:
            items: Annotated[list[Annotated[int, Gt(0)]], MinLen(1)]

        result = inspect_dataclass(Container)
        assert is_dataclass_type_node(result)

        items_field = next(f for f in result.fields if f.name == "items")

        # Container constraint
        container_minlen = find_metadata_of_type(items_field.metadata, MinLen)
        assert container_minlen is not None

        # Element constraint
        assert is_subscripted_generic_node(items_field.type)
        element = items_field.type.args[0]
        element_gt = find_metadata_of_type(element.metadata, Gt)
        assert element_gt is not None
