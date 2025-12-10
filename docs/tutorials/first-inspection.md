# Your first type inspection

In this tutorial, you'll inspect Python type annotations and extract metadata from them using [`inspect_type()`][typing_graph.inspect_type]. By the end, you'll have a working script that traverses a [type graph](../reference/glossary.md#type-graph) and prints its structure.

??? info "Prerequisites"
    Before starting, ensure you have:

    - Python 3.10 or later installed
    - A terminal or command prompt
    - Basic familiarity with Python type hints

    You don't need prior experience with typing-graph.

## Step 1: Install typing-graph

Install the package using pip:

```bash title="Terminal"
pip install typing-graph
```

You should see output indicating a successful installation:

```text title="Output"
Successfully installed typing-graph-x.x.x
```

## Step 2: Create the script file

Create a new file called `inspect_types.py`:

```python title="inspect_types.py"
from typing_graph import inspect_type, ConcreteNode
```

## Step 3: Inspect a simple type

Add code to inspect the `int` type:

```python title="inspect_types.py"
from typing_graph import inspect_type, ConcreteNode

# Inspect a simple type
node = inspect_type(int)
print(f"Node type: {type(node).__name__}")
print(f"Class: {node.cls}")
```

Run the script:

```bash title="Terminal"
python inspect_types.py
```

You should see:

```text title="Output"
Node type: ConcreteNode
Class: <class 'int'>
```

## Step 4: Verify the node type and class

Simple types like `int`, `str`, and custom classes return a [`ConcreteNode`][typing_graph.ConcreteNode]. All [type nodes](../reference/glossary.md#type-node) inherit from [`TypeNode`][typing_graph.TypeNode]. The `cls` attribute gives you the underlying Python class.

Update your script to also inspect a custom class:

```python title="inspect_types.py"
from typing_graph import inspect_type, ConcreteNode

# Inspect a simple type
node = inspect_type(int)
print(f"Node type: {type(node).__name__}")
print(f"Class: {node.cls}")

# Inspect a custom class
class User:
    pass

user_node = inspect_type(User)
print(f"\nUser node type: {type(user_node).__name__}")
print(f"User class: {user_node.cls}")
```

Run the script:

```bash title="Terminal"
python inspect_types.py
```

You should see:

```text title="Output"
Node type: ConcreteNode
Class: <class 'int'>

User node type: ConcreteNode
User class: <class '__main__.User'>
```

!!! success "Checkpoint"
    At this point, you have:

    - Installed typing-graph
    - Inspected simple types using `inspect_type()`
    - Accessed the underlying class via the `cls` attribute

## Step 5: Inspect a generic type

Replace your script contents with code to inspect a generic type:

```python title="inspect_types.py"
from typing_graph import inspect_type, SubscriptedGenericNode

# Inspect a generic type
node = inspect_type(list[int])
print(f"Node type: {type(node).__name__}")
```

Run the script:

```bash title="Terminal"
python inspect_types.py
```

You should see:

```text title="Output"
Node type: SubscriptedGenericNode
```

## Step 6: Access generic origin and arguments

Generic types like `list[int]` return a [`SubscriptedGenericNode`][typing_graph.SubscriptedGenericNode]. This node provides access to both the origin type and its type arguments.

Update your script:

```python title="inspect_types.py"
from typing_graph import inspect_type, SubscriptedGenericNode

# Inspect a generic type
node = inspect_type(list[int])
print(f"Node type: {type(node).__name__}")

# Access the origin (the generic type itself)
print(f"Origin class: {node.origin.cls}")

# Access the type arguments
print(f"Number of args: {len(node.args)}")
print(f"First arg class: {node.args[0].cls}")
```

Run the script:

```bash title="Terminal"
python inspect_types.py
```

You should see:

```text title="Output"
Node type: SubscriptedGenericNode
Origin class: <class 'list'>
Number of args: 1
First arg class: <class 'int'>
```

!!! success "Checkpoint"
    At this point, you have:

    - Inspected generic types like `list[int]`
    - Accessed the origin class via `node.origin.cls`
    - Accessed type arguments via `node.args`

## Step 7: Define metadata classes

Now create metadata classes that you'll attach to types. Replace your script:

```python title="inspect_types.py"
from dataclasses import dataclass

# Define some metadata classes
@dataclass(frozen=True)
class MinLen:
    value: int

@dataclass(frozen=True)
class MaxLen:
    value: int

print("Metadata classes defined")
```

Run the script:

```bash title="Terminal"
python inspect_types.py
```

You should see:

```text title="Output"
Metadata classes defined
```

## Step 8: Create an annotated type

Add an annotated type using your metadata classes:

```python title="inspect_types.py"
from dataclasses import dataclass
from typing import Annotated

# Define some metadata classes
@dataclass(frozen=True)
class MinLen:
    value: int

@dataclass(frozen=True)
class MaxLen:
    value: int

# Create an annotated type
ValidatedString = Annotated[str, MinLen(1), MaxLen(100)]
print(f"Type alias created: {ValidatedString}")
```

Run the script:

```bash title="Terminal"
python inspect_types.py
```

You should see:

```text title="Output"
Type alias created: typing.Annotated[str, MinLen(value=1), MaxLen(value=100)]
```

## Step 9: Inspect the annotated type

Add inspection of the annotated type:

```python title="inspect_types.py"
from dataclasses import dataclass
from typing import Annotated

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
print(f"Node type: {type(node).__name__}")
print(f"Class: {node.cls}")
```

Run the script:

```bash title="Terminal"
python inspect_types.py
```

You should see:

```text title="Output"
Node type: ConcreteNode
Class: <class 'str'>
```

Notice that you get a `ConcreteNode` for `str`, not an `AnnotatedNode`. typing-graph "hoists" metadata from `Annotated` wrappers to the base type node. See [metadata hoisting](../reference/glossary.md#metadata-hoisting) for more details.

## Step 10: Access metadata from the node

Add code to access the metadata:

```python title="inspect_types.py"
from dataclasses import dataclass
from typing import Annotated

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
print(f"Node type: {type(node).__name__}")
print(f"Class: {node.cls}")

# Access metadata
print(f"\nMetadata: {node.metadata}")
for meta in node.metadata:
    if isinstance(meta, MinLen):
        print(f"  Minimum length: {meta.value}")
    elif isinstance(meta, MaxLen):
        print(f"  Maximum length: {meta.value}")
```

Run the script:

```bash title="Terminal"
python inspect_types.py
```

You should see:

```text title="Output"
Node type: ConcreteNode
Class: <class 'str'>

Metadata: MetadataCollection([MinLen(value=1), MaxLen(value=100)])
  Minimum length: 1
  Maximum length: 100
```

!!! success "Checkpoint"
    At this point, you have:

    - Created metadata classes using frozen dataclasses
    - Attached metadata to types using `Annotated`
    - Extracted metadata from inspected type nodes

## Step 11: Define a nested annotated type

Replace your script with code that creates nested annotated types:

```python title="inspect_types.py"
from dataclasses import dataclass
from typing import Annotated

from typing_graph import inspect_type

@dataclass(frozen=True)
class Description:
    text: str

# Metadata on the element type (via a type alias)
URL = Annotated[str, Description("A URL string")]

# Metadata on the list itself
URLs = Annotated[list[URL], Description("A list of URLs")]

# Inspect the outer type
node = inspect_type(URLs)

# The list node has its own metadata
print(f"List metadata: {list(node.metadata)}")

# The element type has its metadata
element = node.args[0]
print(f"Element metadata: {list(element.metadata)}")
```

Run the script:

```bash title="Terminal"
python inspect_types.py
```

You should see:

```text title="Output"
List metadata: [Description(text='A list of URLs')]
Element metadata: [Description(text='A URL string')]
```

## Step 12: Traverse the type tree

Replace your script with a recursive traversal function:

```python title="inspect_types.py"
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

Run the script:

```bash title="Terminal"
python inspect_types.py
```

You should see:

```text title="Output"
SubscriptedGenericNode: dict[...]
  ConcreteNode: str
  SubscriptedGenericNode: list[...]
    ConcreteNode: int
```

!!! success "Checkpoint"
    You've completed this tutorial. You can now:

    - Inspect any Python type annotation
    - Access the underlying class and type arguments
    - Extract metadata from `Annotated` types
    - Traverse nested type structures using `children()`

!!! tip "Prefer walk() for traversal"
    The `children()` method gives you direct access to child nodes, but for most traversal tasks, the [`walk()`][typing_graph.walk] iterator is simpler. It handles depth-first traversal automatically and supports filtering with predicates. See [How to filter type graphs with walk()](../guides/filtering-with-walk.md) for practical examples.

## Summary

You've built a script that inspects Python type annotations and traverses the type graph. The key functions are:

- [`inspect_type()`][typing_graph.inspect_type] inspects any type annotation
- `node.cls` accesses the underlying class
- `node.metadata` accesses attached metadata
- `node.children()` returns child nodes for traversal

!!! tip "Next steps"
    Now that you understand the basics, explore:

    - [Working with metadata](working-with-metadata.md) - Query and filter metadata collections
    - [Inspecting structured types](structured-types.md) - Work with dataclasses, TypedDict, and NamedTuple
    - [Inspecting functions](functions.md) - Analyze function signatures and parameters
    - [Filtering with walk()](../guides/filtering-with-walk.md) - Use the walk() iterator for efficient graph traversal

    For practical applications of type graph traversal, see [Walking the type graph](../guides/walking-type-graph.md).
