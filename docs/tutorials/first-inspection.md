# Your first type inspection

In this tutorial, you'll learn the fundamentals of using typing-graph to inspect Python type annotations.

## What you'll learn

- How to install typing-graph
- How to use `inspect_type()` to inspect any type
- What type nodes are and how to work with them
- How to access metadata from `Annotated` types
- How to traverse child types with `children()`

## Prerequisites

- Python 3.10 or later
- Basic understanding of Python type hints

## Installation

Install typing-graph using your preferred package manager:

=== "pip"

    ```bash
    pip install typing-graph
    ```

=== "uv"

    ```bash
    uv add typing-graph
    ```

=== "Poetry"

    ```bash
    poetry add typing-graph
    ```

## Inspecting simple types

The [`inspect_type()`][typing_graph.inspect_type] function is your primary entry point for type inspection. Pass any type and receive a structured node representation.

```python
from typing_graph import inspect_type, ConcreteNode

# Inspect a simple type
node = inspect_type(int)
print(type(node))  # <class 'typing_graph.ConcreteNode'>
print(node.cls)    # <class 'int'>
```

Simple types like `int`, `str`, `float`, and custom classes return a [`ConcreteNode`][typing_graph.ConcreteNode] node. This node provides access to the underlying class through its `cls` attribute.

```python
# Inspect a string type
str_node = inspect_type(str)
print(str_node.cls)  # <class 'str'>

# Inspect a custom class
class User:
    pass

user_node = inspect_type(User)
print(user_node.cls)  # <class '__main__.User'>
```

## Inspecting generic types

Generic types like `list[int]` or `dict[str, float]` return a [`SubscriptedGenericNode`][typing_graph.SubscriptedGenericNode] node. This node captures both the origin type (for example, `list`) and the type arguments (for example, `int`).

```python
from typing_graph import inspect_type, SubscriptedGenericNode, GenericTypeNode

# Inspect a generic type
node = inspect_type(list[int])
print(type(node))  # SubscriptedGenericNode

# Access the origin (the generic type itself)
print(node.origin)      # GenericTypeNode for 'list'
print(node.origin.cls)  # <class 'list'>

# Access the type arguments
print(node.args)        # (ConcreteNode for 'int',)
print(node.args[0].cls) # <class 'int'>
```

More complex generics work the same way:

```python
# A dictionary with string keys and float values
dict_node = inspect_type(dict[str, float])
print(dict_node.origin.cls)  # <class 'dict'>
print(dict_node.args[0].cls) # <class 'str'>  (key type)
print(dict_node.args[1].cls) # <class 'float'> (value type)
```

## Working with annotated types

The real power of typing-graph emerges when working with `Annotated` types. These allow you to attach metadata to types, and typing-graph extracts this metadata for you.

```python
from typing import Annotated
from dataclasses import dataclass
from typing_graph import inspect_type

# Define some metadata classes
@dataclass(frozen=True)
class MinLen:
    value: int

@dataclass(frozen=True)
class MaxLen:
    value: int

# Create an annotated type
ValidatedString = Annotated[str, MinLen(1), MaxLen(100)]

# Inspect it
node = inspect_type(ValidatedString)
```

By default, typing-graph "hoists" metadata from `Annotated` wrappers to the base type node. This means you get a `ConcreteNode` for `str` with the metadata attached:

```python
print(type(node))   # ConcreteNode
print(node.cls)     # <class 'str'>
print(node.metadata)  # (MinLen(value=1), MaxLen(value=100))
```

You can iterate over the metadata to process it:

```python
for meta in node.metadata:
    if isinstance(meta, MinLen):
        print(f"Minimum length: {meta.value}")
    elif isinstance(meta, MaxLen):
        print(f"Maximum length: {meta.value}")
```

### Nested annotated types

Metadata hoisting works at each level of nested types, keeping metadata properly scoped:

```python
from typing import Annotated
from typing_graph import inspect_type

@dataclass(frozen=True)
class Description:
    text: str

# Metadata on the list itself
# Metadata on the element type (via a type alias)
URL = Annotated[str, Description("A URL string")]
URLs = Annotated[list[URL], Description("A list of URLs")]

node = inspect_type(URLs)

# The list node has its own metadata
print(node.metadata)  # (Description(text='A list of URLs'),)

# The element type has its metadata
element = node.args[0]
print(element.metadata)  # (Description(text='A URL string'),)
```

## Traversing child types

Every type node has a `children()` method that returns its child nodes. This enables recursive traversal of the type graph.

```python
from typing_graph import inspect_type, ConcreteNode, SubscriptedGenericNode

def print_type_tree(node, indent=0):
    """Recursively print a type tree."""
    prefix = "  " * indent
    node_name = type(node).__name__

    # Add details based on node type
    if isinstance(node, ConcreteNode):
        print(f"{prefix}{node_name}: {node.cls.__name__}")
    elif isinstance(node, SubscriptedGenericNode):
        print(f"{prefix}{node_name}: {node.origin.cls.__name__}[...]")
    else:
        print(f"{prefix}{node_name}")

    # Recurse into children
    for child in node.children():
        print_type_tree(child, indent + 1)

# Try it out
node = inspect_type(dict[str, list[int]])
print_type_tree(node)
```

Output:

```text
SubscriptedGenericNode: dict[...]
  ConcreteNode: str
  SubscriptedGenericNode: list[...]
    ConcreteNode: int
```

## Next steps

Now that you understand the basics, explore these topics:

- [Inspecting structured types](structured-types.md) - Work with dataclasses, TypedDict, and NamedTuple
- [Inspecting functions](functions.md) - Analyze function signatures and parameters
- [Extracting metadata](../guides/extracting-metadata.md) - Patterns for filtering and processing metadata
- [Walking the type graph](../guides/walking-type-graph.md) - Advanced traversal techniques
