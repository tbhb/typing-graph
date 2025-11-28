# Inspecting structured types

In this tutorial, you'll learn how to inspect dataclasses, TypedDict, and NamedTuple to extract field definitions and their types.

## What you'll learn

- How to inspect dataclasses with `inspect_dataclass()`
- How to access field definitions and their properties
- How to work with TypedDict using `inspect_typed_dict()`
- How to use `inspect_class()` for auto-detection

## Prerequisites

- Completed the [Your first type inspection](first-inspection.md) tutorial
- Familiarity with Python dataclasses

## Defining a dataclass

Start with a dataclass that has annotated fields:

```python
from dataclasses import dataclass, field
from typing import Annotated
from typing_extensions import Doc

# Custom metadata for validation
@dataclass(frozen=True)
class MinLen:
    value: int

@dataclass(frozen=True)
class Gt:
    value: int | float

# A domain model
@dataclass(frozen=True, slots=True)
class Order:
    """An order with validated fields."""

    id: Annotated[str, MinLen(1), Doc("Unique order identifier")]
    customer_email: Annotated[str, MinLen(5)]
    total: Annotated[float, Gt(0), Doc("Order total in dollars")]
    items: list[str] = field(default_factory=list)
    notes: str | None = None
```

## Inspecting a dataclass

Use [`inspect_dataclass()`][typing_graph.inspect_dataclass] to analyze a dataclass:

```python
from typing_graph import inspect_dataclass

node = inspect_dataclass(Order)
print(type(node))  # <class 'typing_graph.DataclassType'>
```

The [`DataclassType`][typing_graph.DataclassType] node provides access to dataclass-specific information:

```python
print(node.cls)     # <class '__main__.Order'>
print(node.frozen)  # True
print(node.slots)   # True
print(len(node.fields))  # 5
```

## Accessing field definitions

The `fields` attribute returns a tuple of [`DataclassFieldDef`][typing_graph.DataclassFieldDef] objects, one for each field:

```python
for field_def in node.fields:
    print(f"Field: {field_def.name}")
    print(f"  Required: {field_def.required}")
    print(f"  Has default: {field_def.default is not None or field_def.default_factory is not None}")
    print()
```

Output:

```text
Field: id
  Required: True
  Has default: False

Field: customer_email
  Required: True
  Has default: False

Field: total
  Required: True
  Has default: False

Field: items
  Required: False
  Has default: True

Field: notes
  Required: False
  Has default: True
```

## Inspecting field types

Each field definition has a `type` attribute containing the inspected type node:

```python
from typing_graph import ConcreteType, SubscriptedGeneric, UnionTypeNode

for field_def in node.fields:
    type_node = field_def.type
    print(f"{field_def.name}: {type(type_node).__name__}")

    # Access metadata on the field type
    if type_node.metadata:
        print(f"  Metadata: {type_node.metadata}")
```

Output:

```text
id: ConcreteType
  Metadata: (MinLen(value=1), Doc(documentation='Unique order identifier'))
customer_email: ConcreteType
  Metadata: (MinLen(value=5),)
total: ConcreteType
  Metadata: (Gt(value=0), Doc(documentation='Order total in dollars'))
items: SubscriptedGeneric
notes: UnionType
```

### Traversing field types

Use `children()` to traverse into complex field types:

```python
# Get the 'items' field
items_field = next(f for f in node.fields if f.name == "items")
items_type = items_field.type

print(f"Type: {items_type.origin.cls}")  # <class 'list'>
print(f"Element type: {items_type.args[0].cls}")  # <class 'str'>

# Get the 'notes' field (str | None)
notes_field = next(f for f in node.fields if f.name == "notes")
notes_type = notes_field.type

print(f"Union members: {len(notes_type.members)}")  # 2
for member in notes_type.members:
    if isinstance(member, ConcreteType):
        print(f"  - {member.cls}")
```

## Typed dictionaries

[`inspect_typed_dict()`][typing_graph.inspect_typed_dict] analyzes TypedDict classes:

```python
from typing import TypedDict

from typing_extensions import NotRequired, Required

from typing_graph import inspect_typed_dict

class UserProfile(TypedDict, total=False):
    username: Required[str]
    email: Required[str]
    bio: NotRequired[str]
    age: int

node = inspect_typed_dict(UserProfile)
print(type(node))  # <class 'typing_graph.TypedDictType'>
print(node.total)  # False
```

The [`TypedDictType`][typing_graph.TypedDictType] node provides field information through its `fields` attribute:

```python
for field_def in node.fields:
    print(f"{field_def.name}: required={field_def.required}")
```

Output:

```text
username: required=True
email: required=True
bio: required=False
age: required=False
```

## Auto-detection with inspect_class

When you don't know the specific class kind, use [`inspect_class()`][typing_graph.inspect_class] for auto-detection:

```python
from typing_graph import inspect_class, DataclassType, TypedDictType

# Works with dataclasses
order_node = inspect_class(Order)
print(isinstance(order_node, DataclassType))  # True

# Works with TypedDict
profile_node = inspect_class(UserProfile)
print(isinstance(profile_node, TypedDictType))  # True
```

This function returns the appropriate node type based on the input class.

## Named tuples

NamedTuple classes work similarly with [`inspect_named_tuple()`][typing_graph.inspect_named_tuple]:

```python
from typing import NamedTuple
from typing_graph import inspect_named_tuple

class Point(NamedTuple):
    x: float
    y: float
    label: str = "origin"

node = inspect_named_tuple(Point)
print(type(node))  # <class 'typing_graph.NamedTupleType'>

for field_def in node.fields:
    print(f"{field_def.name}: {field_def.type.cls.__name__}, required={field_def.required}")
```

The [`NamedTupleType`][typing_graph.NamedTupleType] node provides field access through its `fields` attribute, just like dataclasses and TypedDict.

Output:

```text
x: float, required=True
y: float, required=True
label: str, required=False
```

## Next steps

- [Inspecting functions](functions.md) - Analyze function signatures
- [Extracting metadata](../guides/extracting-metadata.md) - Patterns for processing field metadata
- [Walking the type graph](../guides/walking-type-graph.md) - Traverse complex type structures
