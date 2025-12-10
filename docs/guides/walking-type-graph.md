# How to traverse a type graph

This guide shows you how to traverse [type graphs](../reference/glossary.md#type-graph) to visit nodes, collect information, and process nested type structures. You'll learn to use the [`walk()`][typing_graph.walk] iterator for efficient depth-first traversal, filter nodes with predicates, control traversal depth, and fall back to manual recursion when needed.

## Using the walk() iterator

The [`walk()`][typing_graph.walk] function provides depth-first traversal of type graphs. It handles visited-node tracking internally and supports filtering and depth limits.

### Basic traversal

Iterate over all nodes in a type graph:

```python
from typing_graph import inspect_type, walk

node = inspect_type(dict[str, list[int]])
for n in walk(node):
    print(type(n).__name__)
```

Output:

```text
SubscriptedGenericNode
GenericTypeNode
ConcreteNode
SubscriptedGenericNode
GenericTypeNode
ConcreteNode
```

### Filtering with predicates

Pass a predicate function to yield only matching nodes. When using a type guard with [`TypeIs`][typing_extensions.TypeIs], the return type narrows automatically:

```python
from typing_graph import inspect_type, walk, ConcreteNode, is_concrete_node

node = inspect_type(dict[str, list[int]])

# Filter to concrete nodes only
for concrete in walk(node, predicate=is_concrete_node):
    print(concrete.cls.__name__)  # Type narrowed to ConcreteNode
```

Output:

```text
str
int
```

You can also use custom predicates:

```python
from typing_graph import inspect_type, walk, TypeNode

def has_metadata(n: TypeNode) -> bool:
    return len(n.metadata) > 0

from typing import Annotated

Inner = Annotated[int, "inner"]
Outer = Annotated[list[Inner], "outer"]

node = inspect_type(Outer)
annotated_nodes = list(walk(node, predicate=has_metadata))
print(len(annotated_nodes))  # 2
```

### Limiting traversal depth

Use `max_depth` to limit how deep the traversal goes:

```python
from typing_graph import inspect_type, walk

node = inspect_type(dict[str, list[tuple[int, float]]])

# Depth 0: only root node
print(len(list(walk(node, max_depth=0))))  # 1

# Depth 1: root + immediate children
print(len(list(walk(node, max_depth=1))))  # 3

# Depth 2: root + children + grandchildren
print(len(list(walk(node, max_depth=2))))  # 5
```

### Combining predicate and depth limit

Filter and limit depth together:

```python
from typing_graph import inspect_type, walk, is_concrete_node

node = inspect_type(dict[str, list[tuple[int, float]]])

# Only concrete nodes within 2 levels
shallow_concrete = list(walk(node, predicate=is_concrete_node, max_depth=2))
print([n.cls.__name__ for n in shallow_concrete])  # ['str']
```

## Manual traversal with children()

When you need fine-grained control over traversal order, path construction, or custom visited-node tracking, use the [`children()`][typing_graph.TypeNode.children] method directly.

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

## Writing recursive traversal functions

For cases where `walk()` doesn't fit your needs, write your own recursive traversal. This gives you control over:

- Custom path tracking (building path strings as you recurse)
- Non-standard traversal order (breadth-first, post-order)
- Selective recursion (skip certain branches)
- Accumulating results during traversal

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
Visiting: GenericTypeNode
Visiting: ConcreteNode
Visiting: SubscriptedGenericNode
Visiting: GenericTypeNode
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

## Practical example: collecting all types

Use `walk()` for the simplest approach:

```python
from typing import Callable
from typing_graph import inspect_type, walk, is_concrete_node

node = inspect_type(Callable[[str, int], dict[str, list[float]]])
types = {n.cls for n in walk(node, predicate=is_concrete_node)}
print(types)  # {<class 'str'>, <class 'int'>, <class 'dict'>, <class 'list'>, <class 'float'>}
```

??? note "Alternative: manual recursion"
    If you need custom behavior during collection, use manual recursion:

    ```python
    from typing_graph import TypeNode, inspect_type, is_concrete_node

    def collect_concrete_types(node: TypeNode) -> set[type]:
        """Collect all concrete types in a type graph."""
        types: set[type] = set()

        def recurse(n: TypeNode) -> None:
            if is_concrete_node(n):
                types.add(n.cls)
            for child in n.children():
                recurse(child)

        recurse(node)
        return types

    # Example
    from typing import Callable
    node = inspect_type(Callable[[str, int], dict[str, list[float]]])
    types = collect_concrete_types(node)
    print(types)  # {<class 'str'>, <class 'int'>, <class 'dict'>, <class 'list'>, <class 'float'>}
    ```

## Collecting metadata during traversal

Use `walk()` to find nodes with metadata:

```python
from typing import Annotated
from dataclasses import dataclass
from typing_graph import inspect_type, walk, TypeNode

@dataclass(frozen=True)
class Constraint:
    name: str

def has_constraint(n: TypeNode) -> bool:
    return any(isinstance(m, Constraint) for m in n.metadata)

Inner = Annotated[int, Constraint("inner")]
Outer = Annotated[list[Inner], Constraint("outer")]

node = inspect_type(Outer)
for n in walk(node, predicate=has_constraint):
    for meta in n.metadata:
        if isinstance(meta, Constraint):
            print(meta.name)
```

Output:

```text
outer
inner
```

??? note "Alternative: manual recursion with path tracking"
    When you need to track the path to each constraint:

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

        def recurse(n: TypeNode, path: str) -> None:
            # Check metadata at this node
            for meta in n.metadata:
                if isinstance(meta, Constraint):
                    results.append((path, meta))

            # Recurse
            for i, child in enumerate(n.children()):
                recurse(child, f"{path}[{i}]")

        recurse(node, "root")
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

You can now traverse type graphs using `walk()` for standard depth-first iteration with predicates and depth limits. For advanced cases requiring custom path tracking or non-standard traversal order, you know how to write recursive functions using `children()`.

## See also

- [`walk()`][typing_graph.walk] - API reference for the walk iterator
- [Your first type inspection](../tutorials/first-inspection.md) - Basics of `children()`
- [Metadata queries](metadata-queries.md) - Processing metadata during traversal
- [Inspecting structured types](../tutorials/structured-types.md) - Dataclass field traversal
- [Architecture overview](../explanation/architecture.md) - How the node hierarchy is designed
- [Type graph](../reference/glossary.md#type-graph) - Glossary definition
