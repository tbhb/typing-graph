# Inspecting structured types

In this tutorial, you'll inspect dataclasses, TypedDict, and NamedTuple to extract field definitions and their types. By the end, you'll be able to analyze any [structured type](../reference/glossary.md#structured-type) and access its fields with their metadata.

??? info "Prerequisites"
    Before starting, ensure you have:

    - Completed the [Your first type inspection](first-inspection.md) tutorial
    - Basic familiarity with Python dataclasses

    You don't need prior experience with TypedDict or NamedTuple.

## Step 1: Create the script file

Create a new file called `structured_types.py`:

```python title="structured_types.py"
from dataclasses import dataclass

print("Ready to inspect structured types")
```

Run the script:

```bash title="Terminal"
python structured_types.py
```

You should see:

```text title="Output"
Ready to inspect structured types
```

## Step 2: Define metadata constraint classes

Create metadata classes to attach to your dataclass fields:

```python title="structured_types.py"
from dataclasses import dataclass


@dataclass(frozen=True)
class MinLen:
    value: int


@dataclass(frozen=True)
class Gt:
    value: int | float


print("Constraint classes defined")
```

Run the script:

```bash title="Terminal"
python structured_types.py
```

You should see:

```text title="Output"
Constraint classes defined
```

## Step 3: Define a dataclass with annotations

Create a dataclass with annotated fields:

```python title="structured_types.py"
from dataclasses import dataclass, field
from typing import Annotated

from typing_extensions import Doc


@dataclass(frozen=True)
class MinLen:
    value: int


@dataclass(frozen=True)
class Gt:
    value: int | float


@dataclass(frozen=True, slots=True)
class Order:
    """An order with validated fields."""

    id: Annotated[str, MinLen(1), Doc("Unique order identifier")]
    customer_email: Annotated[str, MinLen(5)]
    total: Annotated[float, Gt(0), Doc("Order total in dollars")]
    items: list[str] = field(default_factory=list)
    notes: str | None = None


print(f"Order class defined with {len(Order.__dataclass_fields__)} fields")
```

Run the script:

```bash title="Terminal"
python structured_types.py
```

You should see:

```text title="Output"
Order class defined with 5 fields
```

## Step 4: Inspect the dataclass

Use [`inspect_dataclass()`][typing_graph.inspect_dataclass] to analyze your dataclass:

```python title="structured_types.py"
from dataclasses import dataclass, field
from typing import Annotated

from typing_extensions import Doc

from typing_graph import inspect_dataclass


@dataclass(frozen=True)
class MinLen:
    value: int


@dataclass(frozen=True)
class Gt:
    value: int | float


@dataclass(frozen=True, slots=True)
class Order:
    """An order with validated fields."""

    id: Annotated[str, MinLen(1), Doc("Unique order identifier")]
    customer_email: Annotated[str, MinLen(5)]
    total: Annotated[float, Gt(0), Doc("Order total in dollars")]
    items: list[str] = field(default_factory=list)
    notes: str | None = None


node = inspect_dataclass(Order)
print(f"Node type: {type(node).__name__}")
```

Run the script:

```bash title="Terminal"
python structured_types.py
```

You should see:

```text title="Output"
Node type: DataclassNode
```

## Step 5: Access dataclass properties

The [`DataclassNode`][typing_graph.DataclassNode] provides access to dataclass-specific information:

```python title="structured_types.py"
from dataclasses import dataclass, field
from typing import Annotated

from typing_extensions import Doc

from typing_graph import inspect_dataclass


@dataclass(frozen=True)
class MinLen:
    value: int


@dataclass(frozen=True)
class Gt:
    value: int | float


@dataclass(frozen=True, slots=True)
class Order:
    """An order with validated fields."""

    id: Annotated[str, MinLen(1), Doc("Unique order identifier")]
    customer_email: Annotated[str, MinLen(5)]
    total: Annotated[float, Gt(0), Doc("Order total in dollars")]
    items: list[str] = field(default_factory=list)
    notes: str | None = None


node = inspect_dataclass(Order)
print(f"Class: {node.cls.__name__}")
print(f"Frozen: {node.frozen}")
print(f"Slots: {node.slots}")
print(f"Number of fields: {len(node.fields)}")
```

Run the script:

```bash title="Terminal"
python structured_types.py
```

You should see:

```text title="Output"
Class: Order
Frozen: True
Slots: True
Number of fields: 5
```

!!! success "Checkpoint"
    At this point, you have:

    - Defined a dataclass with annotated fields
    - Inspected it using `inspect_dataclass()`
    - Accessed class-level properties like `frozen` and `slots`

## Step 6: Iterate over field definitions

The `fields` attribute returns a tuple of [`DataclassFieldDef`][typing_graph.DataclassFieldDef] objects. Each field definition provides access to the field's name, type, default values, and whether it's required:

```python title="structured_types.py"
from dataclasses import dataclass, field
from typing import Annotated

from typing_extensions import Doc

from typing_graph import inspect_dataclass


@dataclass(frozen=True)
class MinLen:
    value: int


@dataclass(frozen=True)
class Gt:
    value: int | float


@dataclass(frozen=True, slots=True)
class Order:
    """An order with validated fields."""

    id: Annotated[str, MinLen(1), Doc("Unique order identifier")]
    customer_email: Annotated[str, MinLen(5)]
    total: Annotated[float, Gt(0), Doc("Order total in dollars")]
    items: list[str] = field(default_factory=list)
    notes: str | None = None


node = inspect_dataclass(Order)

for field_def in node.fields:
    has_default = field_def.default is not None or field_def.default_factory is not None
    print(f"{field_def.name}: required={field_def.required}, has_default={has_default}")
```

Run the script:

```bash title="Terminal"
python structured_types.py
```

You should see:

```text title="Output"
id: required=True, has_default=False
customer_email: required=True, has_default=False
total: required=True, has_default=False
items: required=False, has_default=True
notes: required=False, has_default=True
```

## Step 7: Access field type nodes and metadata

Each field definition has a `type` attribute containing the inspected type node:

```python title="structured_types.py"
from dataclasses import dataclass, field
from typing import Annotated

from typing_extensions import Doc

from typing_graph import inspect_dataclass


@dataclass(frozen=True)
class MinLen:
    value: int


@dataclass(frozen=True)
class Gt:
    value: int | float


@dataclass(frozen=True, slots=True)
class Order:
    """An order with validated fields."""

    id: Annotated[str, MinLen(1), Doc("Unique order identifier")]
    customer_email: Annotated[str, MinLen(5)]
    total: Annotated[float, Gt(0), Doc("Order total in dollars")]
    items: list[str] = field(default_factory=list)
    notes: str | None = None


node = inspect_dataclass(Order)

for field_def in node.fields:
    type_node = field_def.type
    print(f"{field_def.name}: {type(type_node).__name__}")
    if type_node.metadata:
        print(f"  Metadata: {list(type_node.metadata)}")
```

Run the script:

```bash title="Terminal"
python structured_types.py
```

You should see:

```text title="Output"
id: ConcreteNode
  Metadata: [MinLen(value=1), Doc(documentation='Unique order identifier')]
customer_email: ConcreteNode
  Metadata: [MinLen(value=5)]
total: ConcreteNode
  Metadata: [Gt(value=0), Doc(documentation='Order total in dollars')]
items: SubscriptedGenericNode
notes: UnionNode
```

## Step 8: Traverse into complex field types

Use the node's properties to explore complex field types:

```python title="structured_types.py"
from dataclasses import dataclass, field
from typing import Annotated

from typing_extensions import Doc

from typing_graph import inspect_dataclass, ConcreteNode


@dataclass(frozen=True)
class MinLen:
    value: int


@dataclass(frozen=True)
class Gt:
    value: int | float


@dataclass(frozen=True, slots=True)
class Order:
    """An order with validated fields."""

    id: Annotated[str, MinLen(1), Doc("Unique order identifier")]
    customer_email: Annotated[str, MinLen(5)]
    total: Annotated[float, Gt(0), Doc("Order total in dollars")]
    items: list[str] = field(default_factory=list)
    notes: str | None = None


node = inspect_dataclass(Order)

# Get the 'items' field (list[str])
items_field = next(f for f in node.fields if f.name == "items")
items_type = items_field.type
print(f"Items origin: {items_type.origin.cls}")
print(f"Items element type: {items_type.args[0].cls}")

# Get the 'notes' field (str | None)
notes_field = next(f for f in node.fields if f.name == "notes")
notes_type = notes_field.type
print(f"\nNotes union members: {len(notes_type.members)}")
for member in notes_type.members:
    if isinstance(member, ConcreteNode):
        print(f"  - {member.cls}")
```

Run the script:

```bash title="Terminal"
python structured_types.py
```

You should see:

```text title="Output"
Items origin: <class 'list'>
Items element type: <class 'str'>

Notes union members: 2
  - <class 'str'>
  - <class 'NoneType'>
```

!!! success "Checkpoint"
    At this point, you have:

    - Iterated over field definitions
    - Accessed field type nodes and their metadata
    - Traversed into complex field types like `list[str]` and `str | None`

## Step 9: Define a TypedDict

Create a TypedDict class to inspect:

```python title="structured_types.py"
from typing import TypedDict

from typing_extensions import NotRequired, Required


class UserProfile(TypedDict, total=False):
    username: Required[str]
    email: Required[str]
    bio: NotRequired[str]
    age: int


print(f"UserProfile defined with total={UserProfile.__total__}")
```

Run the script:

```bash title="Terminal"
python structured_types.py
```

You should see:

```text title="Output"
UserProfile defined with total=False
```

## Step 10: Inspect the TypedDict

Use [`inspect_typed_dict()`][typing_graph.inspect_typed_dict] to analyze it:

```python title="structured_types.py"
from typing import TypedDict

from typing_extensions import NotRequired, Required

from typing_graph import inspect_typed_dict


class UserProfile(TypedDict, total=False):
    username: Required[str]
    email: Required[str]
    bio: NotRequired[str]
    age: int


node = inspect_typed_dict(UserProfile)
print(f"Node type: {type(node).__name__}")
print(f"Total: {node.total}")
```

Run the script:

```bash title="Terminal"
python structured_types.py
```

You should see:

```text title="Output"
Node type: TypedDictNode
Total: False
```

## Step 11: Access TypedDict field requirements

The [`TypedDictNode`][typing_graph.TypedDictNode] provides field information with required status:

```python title="structured_types.py"
from typing import TypedDict

from typing_extensions import NotRequired, Required

from typing_graph import inspect_typed_dict


class UserProfile(TypedDict, total=False):
    username: Required[str]
    email: Required[str]
    bio: NotRequired[str]
    age: int


node = inspect_typed_dict(UserProfile)

for field_def in node.fields:
    print(f"{field_def.name}: required={field_def.required}")
```

Run the script:

```bash title="Terminal"
python structured_types.py
```

You should see:

```text title="Output"
username: required=True
email: required=True
bio: required=False
age: required=False
```

!!! success "Checkpoint"
    At this point, you have:

    - Defined a TypedDict with `Required` and `NotRequired` fields
    - Inspected it using `inspect_typed_dict()`
    - Accessed field requirement status

## Step 12: Use inspect_class() for auto-detection

When you don't know the specific class kind, use [`inspect_class()`][typing_graph.inspect_class]:

```python title="structured_types.py"
from dataclasses import dataclass
from typing import TypedDict

from typing_graph import inspect_class, DataclassNode, TypedDictNode


@dataclass
class Point:
    x: float
    y: float


class Config(TypedDict):
    name: str
    value: int


# Works with dataclasses
point_node = inspect_class(Point)
print(f"Point: {type(point_node).__name__}, is DataclassNode: {isinstance(point_node, DataclassNode)}")

# Works with TypedDict
config_node = inspect_class(Config)
print(f"Config: {type(config_node).__name__}, is TypedDictNode: {isinstance(config_node, TypedDictNode)}")
```

Run the script:

```bash title="Terminal"
python structured_types.py
```

You should see:

```text title="Output"
Point: DataclassNode, is DataclassNode: True
Config: TypedDictNode, is TypedDictNode: True
```

## Step 13: Define and inspect a NamedTuple

[`NamedTuple`](https://docs.python.org/3/library/typing.html#typing.NamedTuple) classes work similarly with [`inspect_named_tuple()`][typing_graph.inspect_named_tuple]. The resulting [`NamedTupleNode`][typing_graph.NamedTupleNode] provides field definitions with name, type, and required status:

```python title="structured_types.py"
from typing import NamedTuple

from typing_graph import inspect_named_tuple


class Point(NamedTuple):
    x: float
    y: float
    label: str = "origin"


node = inspect_named_tuple(Point)
print(f"Node type: {type(node).__name__}")

for field_def in node.fields:
    print(f"{field_def.name}: {field_def.type.cls.__name__}, required={field_def.required}")
```

Run the script:

```bash title="Terminal"
python structured_types.py
```

You should see:

```text title="Output"
Node type: NamedTupleNode
x: float, required=True
y: float, required=True
label: str, required=False
```

!!! success "Checkpoint"
    You've completed this tutorial. You can now:

    - Inspect dataclasses with `inspect_dataclass()`
    - Inspect TypedDict with `inspect_typed_dict()`
    - Inspect NamedTuple with `inspect_named_tuple()`
    - Use `inspect_class()` for auto-detection
    - Access field definitions, types, and metadata

## Summary

You've learned how to inspect structured types and extract their field definitions. The key functions are:

- [`inspect_dataclass()`][typing_graph.inspect_dataclass] for dataclasses
- [`inspect_typed_dict()`][typing_graph.inspect_typed_dict] for TypedDict
- [`inspect_named_tuple()`][typing_graph.inspect_named_tuple] for NamedTuple
- [`inspect_class()`][typing_graph.inspect_class] for auto-detection

Each returns a node with a `fields` attribute containing field definitions with name, type, and requirement status.

!!! tip "Next steps"
    Now that you can inspect structured types, explore:

    - [Inspecting functions](functions.md) - Analyze function signatures
    - [Metadata queries](../guides/metadata-queries.md) - Patterns for processing field metadata
    - [Walking the type graph](../guides/walking-type-graph.md) - Traverse complex type structures

    For background on why structured types are handled this way, see the [Architecture overview](../explanation/architecture.md).
