# Walking the type graph

!!! note "Upcoming API improvements"

    A dedicated **graph traversal API** is coming soon with a `walk()` generator, visitor pattern support, and path tracking. The patterns shown here use the current stable `children()` method. See the [roadmap](../roadmap.md#graph-traversal-api) for details on planned features.

This guide shows how to traverse the type graph recursively using the `children()` method available on all type nodes.

## The children method

Every [`TypeNode`][typing_graph.TypeNode] has a `children()` method that returns an iterable of its child nodes. What counts as a "child" depends on the node type:

| Node type                                                | Children                        |
| -------------------------------------------------------- | ------------------------------- |
| [`ConcreteType`][typing_graph.ConcreteType]              | None (leaf node)                |
| [`SubscriptedGeneric`][typing_graph.SubscriptedGeneric]  | Type arguments                  |
| [`UnionType`][typing_graph.UnionType]                    | Union members                   |
| [`TupleType`][typing_graph.TupleType]                    | Element types                   |
| [`CallableType`][typing_graph.CallableType]              | Parameter types and return type |
| [`DataclassType`][typing_graph.DataclassType]            | Field types                     |
| [`TypedDictType`][typing_graph.TypedDictType]            | Field types                     |

```python
from typing_graph import inspect_type

# A generic type's children are its type arguments
node = inspect_type(dict[str, list[int]])
children = list(node.children())
print(len(children))  # 2 (str and list[int])

# A concrete type has no children
str_node = inspect_type(str)
print(list(str_node.children()))  # []
```

## Writing a recursive traversal

Here's a basic depth-first traversal function:

```python
from typing_graph import TypeNode, inspect_type

def traverse(node: TypeNode) -> None:
    """Visit every node in the type graph."""
    print(f"Visiting: {type(node).__name__}")

    for child in node.children():
        traverse(child)

# Try it
node = inspect_type(dict[str, list[int]])
traverse(node)
```

Output:

```text
Visiting: SubscriptedGeneric
Visiting: ConcreteType
Visiting: SubscriptedGeneric
Visiting: ConcreteType
```

## Handling different node types

Use the library's type guard functions to handle different node types. These provide proper type narrowing with `TypeIs`:

```python
from typing_graph import (
    TypeNode,
    inspect_type,
    is_concrete_type,
    is_subscripted_generic_node,
    is_union_type_node,
    is_literal_node,
)

def describe_type(node: TypeNode, indent: int = 0) -> None:
    """Describe a type and its structure."""
    prefix = "  " * indent

    if is_concrete_type(node):
        print(f"{prefix}Concrete: {node.cls.__name__}")

    elif is_subscripted_generic_node(node):
        origin_name = node.origin.cls.__name__
        print(f"{prefix}Generic: {origin_name}[...]")

    elif is_union_type_node(node):
        print(f"{prefix}Union of {len(node.members)} types:")

    elif is_literal_node(node):
        print(f"{prefix}Literal: {node.values}")

    else:
        print(f"{prefix}{type(node).__name__}")

    # Recurse
    for child in node.children():
        describe_type(child, indent + 1)

# Example
from typing import Literal
node = inspect_type(dict[str, int | None])
describe_type(node)
```

Output:

```text
Generic: dict[...]
  Concrete: str
  Union of 2 types:
    Concrete: int
    Concrete: NoneType
```

## Tracking paths

When traversing, you often need to know where you are in the graph. Build path strings as you recurse:

```python
from typing_graph import (
    TypeNode,
    inspect_type,
    inspect_dataclass,
    is_concrete_type,
    is_subscripted_generic_node,
    is_dataclass_type_node,
)

def traverse_with_path(node: TypeNode, path: str = "root") -> None:
    """Traverse and print the path to each node."""
    # Report this node
    if is_concrete_type(node):
        print(f"{path} -> {node.cls.__name__}")
    else:
        print(f"{path} -> {type(node).__name__}")

    # Build paths for children based on node type
    if is_subscripted_generic_node(node):
        for i, child in enumerate(node.args):
            traverse_with_path(child, f"{path}[{i}]")

    elif is_dataclass_type_node(node):
        for field in node.fields:
            traverse_with_path(field.type, f"{path}.{field.name}")

    else:
        for i, child in enumerate(node.children()):
            traverse_with_path(child, f"{path}.{i}")

# Example with a dataclass
from dataclasses import dataclass
from typing import Annotated

@dataclass
class User:
    name: str
    emails: list[str]

node = inspect_dataclass(User)
traverse_with_path(node)
```

Output:

```text
root -> DataclassType
root.name -> str
root.emails -> SubscriptedGeneric
root.emails[0] -> str
```

## Limiting recursion depth

Prevent infinite recursion or excessive depth with a limit:

```python
from typing_graph import TypeNode, inspect_type

def traverse_limited(
    node: TypeNode,
    max_depth: int = 10,
    current_depth: int = 0,
) -> None:
    """Traverse with a depth limit."""
    if current_depth >= max_depth:
        print(f"{'  ' * current_depth}... (max depth reached)")
        return

    print(f"{'  ' * current_depth}{type(node).__name__}")

    for child in node.children():
        traverse_limited(child, max_depth, current_depth + 1)

# Limit to 2 levels
node = inspect_type(dict[str, list[tuple[int, float]]])
traverse_limited(node, max_depth=2)
```

Output:

```text
SubscriptedGeneric
  ConcreteType
  SubscriptedGeneric
    ... (max depth reached)
```

## Practical example: collecting all types

Here's a complete example that collects all concrete types in a graph:

```python
from typing_graph import TypeNode, inspect_type, is_concrete_type

def collect_concrete_types(node: TypeNode) -> set[type]:
    """Collect all concrete types in a type graph."""
    types: set[type] = set()

    def walk(n: TypeNode) -> None:
        if is_concrete_type(n):
            types.add(n.cls)
        for child in n.children():
            walk(child)

    walk(node)
    return types

# Example
from typing import Callable
node = inspect_type(Callable[[str, int], dict[str, list[float]]])
types = collect_concrete_types(node)
print(types)  # {<class 'str'>, <class 'int'>, <class 'dict'>, <class 'list'>, <class 'float'>}
```

## Collecting metadata during traversal

Combine traversal with metadata extraction:

```python
from typing import Annotated, Any
from dataclasses import dataclass
from typing_graph import TypeNode, inspect_type

@dataclass(frozen=True)
class Constraint:
    name: str

def collect_constraints(node: TypeNode) -> list[tuple[str, Constraint]]:
    """Collect all constraints with their paths."""
    results: list[tuple[str, Constraint]] = []

    def walk(n: TypeNode, path: str) -> None:
        # Check metadata at this node
        for meta in n.metadata:
            if isinstance(meta, Constraint):
                results.append((path, meta))

        # Recurse
        for i, child in enumerate(n.children()):
            walk(child, f"{path}[{i}]")

    walk(node, "root")
    return results

# Example
Inner = Annotated[int, Constraint("inner")]
Outer = Annotated[list[Inner], Constraint("outer")]

node = inspect_type(Outer)
for path, constraint in collect_constraints(node):
    print(f"{path}: {constraint.name}")
```

Output:

```text
root: outer
root[0]: inner
```

## See also

- [Your first type inspection](../tutorials/first-inspection.md) - Basics of `children()`
- [Extracting metadata](extracting-metadata.md) - Processing metadata during traversal
- [Inspecting structured types](../tutorials/structured-types.md) - Dataclass field traversal
