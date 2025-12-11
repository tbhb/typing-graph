# How to use common helper functions

This guide shows you how to use typing-graph's built-in helper functions for common type inspection tasks. These functions simplify working with optional types, unions, and class detection.

## Check if a type is optional

Use [`is_optional_node()`][typing_graph.is_optional_node] to check if a type node represents an optional type (a union containing `None`):

```python
from typing import Optional
from typing_graph import inspect_type, is_optional_node

# All of these are optional
is_optional_node(inspect_type(int | None))  # True
is_optional_node(inspect_type(Optional[str]))  # True
is_optional_node(inspect_type(str | int | None))  # True

# These are not optional
is_optional_node(inspect_type(int | str))  # False
is_optional_node(inspect_type(int))  # False
```

## Extract the non-None type from an optional

Use [`unwrap_optional()`][typing_graph.unwrap_optional] to get the non-None member types from an optional:

```python
from typing_graph import inspect_type, unwrap_optional, is_concrete_node

# Simple optional
node = inspect_type(int | None)
unwrapped = unwrap_optional(node)
# unwrapped is a tuple with one element: the int node
if unwrapped and is_concrete_node(unwrapped[0]):
    print(unwrapped[0].cls)  # <class 'int'>

# Multi-type optional
node = inspect_type(str | int | None)
unwrapped = unwrap_optional(node)
# unwrapped contains both the str and int nodes
print(len(unwrapped))  # 2

# Returns None for non-optionals
unwrap_optional(inspect_type(int))  # None
```

!!! tip
    If you just need to check whether a type is optional, use `is_optional_node()` instead of checking whether `unwrap_optional()` returns `None`. It's clearer and more efficient.

## Check if a node represents a union

Use [`is_union_node()`][typing_graph.is_union_node] to check if a type node represents any union type. This handles both PEP 604 unions (`int | str`) and `typing.Union`:

```python
from typing import Literal
from typing_graph import inspect_type, is_union_node

# PEP 604 union (types.UnionType)
is_union_node(inspect_type(int | str))  # True

# typing.Union (from Literal combinations)
is_union_node(inspect_type(Literal["a"] | Literal["b"]))  # True

# Not unions
is_union_node(inspect_type(list[int]))  # False
is_union_node(inspect_type(int))  # False
```

!!! note "Why two union representations?"
    Python has two runtime forms for union types. PEP 604 unions with concrete types produce `types.UnionType`, which typing-graph represents as [`UnionNode`][typing_graph.UnionNode]. Unions involving typing special forms like `Literal` produce `typing.Union`, represented as [`SubscriptedGenericNode`][typing_graph.SubscriptedGenericNode]. The `is_union_node()` helper handles both.

## Extract members from a union

Use [`get_union_members()`][typing_graph.get_union_members] to extract member types from either union representation:

```python
from typing import Literal
from typing_graph import inspect_type, get_union_members

# Works with PEP 604 unions
node = inspect_type(int | str | float)
members = get_union_members(node)
print(len(members))  # 3

# Works with typing.Union
node = inspect_type(Literal["a"] | Literal["b"])
members = get_union_members(node)
print(len(members))  # 2

# Returns None for non-unions
get_union_members(inspect_type(int))  # None
```

Combining with `is_union_node()`:

```python
from typing_graph import inspect_type, is_union_node, get_union_members

def process_type(node):
    if is_union_node(node):
        members = get_union_members(node)
        for member in members:
            # Process each union member
            print(f"Union member: {member}")
    else:
        # Handle non-union type
        print(f"Single type: {node}")
```

## Check if a class is a dataclass

Use [`is_dataclass_class()`][typing_graph.is_dataclass_class] to check if a class is a dataclass:

```python
from dataclasses import dataclass
from typing_graph import is_dataclass_class

@dataclass
class User:
    name: str
    age: int

class RegularClass:
    pass

is_dataclass_class(User)  # True
is_dataclass_class(RegularClass)  # False
```

## Check if a class is an enum

Use [`is_enum_class()`][typing_graph.is_enum_class] to check if a class is an enum:

```python
from enum import Enum
from typing_graph import is_enum_class

class Status(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class NotAnEnum:
    pass

is_enum_class(Status)  # True
is_enum_class(NotAnEnum)  # False
```

The `is_enum_class()` function returns [`TypeIs[type[Enum]]`][typing_extensions.TypeIs], which provides type narrowing:

```python
from typing_graph import is_enum_class

def process_class(cls: type):
    if is_enum_class(cls):
        # cls is narrowed to type[Enum] here
        for member in cls:
            print(f"{member.name} = {member.value}")
```

## Other class type checks

typing-graph provides more class detection functions:

| Function | Checks for |
| -------- | ---------- |
| [`is_typeddict_class()`][typing_graph.is_typeddict_class] | TypedDict classes |
| [`is_namedtuple_class()`][typing_graph.is_namedtuple_class] | NamedTuple classes |
| [`is_protocol_class()`][typing_graph.is_protocol_class] | Protocol classes |

```python
from typing import NamedTuple, TypedDict
from typing_extensions import Protocol
from typing_graph import (
    is_typeddict_class,
    is_namedtuple_class,
    is_protocol_class,
)

class Person(TypedDict):
    name: str

class Point(NamedTuple):
    x: float
    y: float

class Comparable(Protocol):
    def __lt__(self, other) -> bool: ...

is_typeddict_class(Person)  # True
is_namedtuple_class(Point)  # True
is_protocol_class(Comparable)  # True
```

## Node type guards

typing-graph provides `is_*_node()` type guard functions for each node type. These narrow the type in conditionals:

```python
from typing_graph import (
    inspect_type,
    is_concrete_node,
    is_subscripted_generic_node,
    is_union_type_node,
)

node = inspect_type(list[int])

if is_subscripted_generic_node(node):
    # node is narrowed to SubscriptedGenericNode
    print(f"Origin: {node.origin.cls}")
    print(f"Args: {node.args}")

if is_concrete_node(node):
    # node is narrowed to ConcreteNode
    print(f"Class: {node.cls}")
```

For the complete list of type guards, see the [API reference](../reference/api.md#type-guards).

## Next steps

- [Understanding union types](../explanation/union-types.md) - Why Python has two union representations
- [Filtering with walk()](filtering-with-walk.md) - Use type guards with the walk iterator
- [API reference](../reference/api.md) - Complete function signatures and node types
