# How to traverse a type graph

This guide shows you how to traverse [type graphs](../reference/glossary.md#type-graph) recursively to visit all nodes, collect information, and process nested type structures. You'll learn to write recursive traversal functions, handle different [node types](../reference/glossary.md#type-node), track paths, and collect metadata during traversal.

!!! note "Upcoming API improvements"

    A dedicated **graph traversal API** is coming soon with a `walk()` generator, visitor pattern support, and path tracking. The patterns shown here use the current stable `children()` method. See the [roadmap](../roadmap.md#graph-traversal-api) for details on planned features.

## The children method

Every [`TypeNode`][typing_graph.TypeNode] has a `children()` method that returns an iterable of its child nodes. What counts as a "child" depends on the node type:

| Node type                                                        | Children                        |
| ---------------------------------------------------------------- | ------------------------------- |
| [`ConcreteNode`][typing_graph.ConcreteNode]                      | None (leaf node)                |
| [`SubscriptedGenericNode`][typing_graph.SubscriptedGenericNode]  | Type arguments                  |
| [`UnionNode`][typing_graph.UnionNode]                            | Union members                   |
| [`TupleNode`][typing_graph.TupleNode]                            | Element types                   |
| [`CallableNode`][typing_graph.CallableNode]                      | Parameter types and return type |
| [`DataclassNode`][typing_graph.DataclassNode]                    | Field types                     |
| [`TypedDictNode`][typing_graph.TypedDictNode]                    | Field types                     |

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

    for child in node.children():  # (1)!
        traverse(child)  # (2)!

# Try it
node = inspect_type(dict[str, list[int]])
traverse(node)
```

1. `children()` returns the immediate children of this node (type arguments for generics).
2. Recursive call processes the entire subtree depth-first.

Output:

```text
Visiting: SubscriptedGenericNode
Visiting: ConcreteNode
Visiting: SubscriptedGenericNode
Visiting: ConcreteNode
```

## Handling different node types

Use the library's type guard functions to handle different node types. These provide proper type narrowing with `TypeIs`:

```python
from typing_graph import (
    TypeNode,
    inspect_type,
    is_concrete_node,
    is_subscripted_generic_node,
    is_union_type_node,
    is_literal_node,
)

def describe_type(node: TypeNode, indent: int = 0) -> None:
    """Describe a type and its structure."""
    prefix = "  " * indent

    if is_concrete_node(node):
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
    is_concrete_node,
    is_subscripted_generic_node,
    is_dataclass_node,
)

def traverse_with_path(node: TypeNode, path: str = "root") -> None:
    """Traverse and print the path to each node."""
    # Report this node
    if is_concrete_node(node):
        print(f"{path} -> {node.cls.__name__}")
    else:
        print(f"{path} -> {type(node).__name__}")

    # Build paths for children based on node type
    if is_subscripted_generic_node(node):
        for i, child in enumerate(node.args):  # (1)!
            traverse_with_path(child, f"{path}[{i}]")

    elif is_dataclass_node(node):
        for field in node.fields:  # (2)!
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

1. For generics, use index notation (for example, `emails[0]` for element type).
2. For dataclasses, use field names (for example, `root.name`, `root.emails`).

Output:

```text
root -> DataclassNode
root.name -> str
root.emails -> SubscriptedGenericNode
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
    if current_depth >= max_depth:  # (1)!
        print(f"{'  ' * current_depth}... (max depth reached)")
        return

    print(f"{'  ' * current_depth}{type(node).__name__}")

    for child in node.children():
        traverse_limited(child, max_depth, current_depth + 1)  # (2)!

# Limit to 2 levels
node = inspect_type(dict[str, list[tuple[int, float]]])
traverse_limited(node, max_depth=2)
```

1. Base case: stop recursion when depth limit reached.
2. Increment depth counter with each recursive call.

Output:

```text
SubscriptedGenericNode
  ConcreteNode
  SubscriptedGenericNode
    ... (max depth reached)
```

## Practical example: collecting all types

Here's a complete example that collects all concrete types in a graph:

```python
from typing_graph import TypeNode, inspect_type, is_concrete_node

def collect_concrete_types(node: TypeNode) -> set[type]:
    """Collect all concrete types in a type graph."""
    types: set[type] = set()

    def walk(n: TypeNode) -> None:
        if is_concrete_node(n):
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

## Result

You can now write recursive traversal functions using `children()`, handle different node types with type guards, track paths through the graph, limit recursion depth, and collect both types and metadata during traversal.

## See also

- [Your first type inspection](../tutorials/first-inspection.md) - Basics of `children()`
- [Metadata queries](metadata-queries.md) - Processing metadata during traversal
- [Inspecting structured types](../tutorials/structured-types.md) - Dataclass field traversal
- [Architecture overview](../explanation/architecture.md) - How the node hierarchy is designed
- [Type graph](../reference/glossary.md#type-graph) - Glossary definition
