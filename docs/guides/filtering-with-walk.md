# How to filter type graphs with walk()

This guide shows you how to use [`walk()`][typing_graph.walk] to filter type graphs with type-safe predicates. You'll learn to use built-in type guards for automatic type narrowing, write custom [`TypeIs`][typing_extensions.TypeIs] predicates for metadata-based filtering, and combine predicates with depth limits for efficient traversal.

For comprehensive traversal patterns including manual recursion and `children()`, see [Walking the type graph](walking-type-graph.md).

## Using built-in type guards

The library provides type guard functions that narrow the return type of `walk()` automatically. When you pass a type guard as a predicate, the yielded nodes are typed as the specific node type.

### Available type guards

| Type guard                                                                  | Narrows to                                                      | Use for                                    |
| --------------------------------------------------------------------------- | --------------------------------------------------------------- | ------------------------------------------ |
| [`is_concrete_node`][typing_graph.is_concrete_node]                         | [`ConcreteNode`][typing_graph.ConcreteNode]                     | Plain types like `str`, `int`              |
| [`is_subscripted_generic_node`][typing_graph.is_subscripted_generic_node]   | [`SubscriptedGenericNode`][typing_graph.SubscriptedGenericNode] | Parameterized generics like `list[int]`    |
| [`is_union_type_node`][typing_graph.is_union_type_node]                     | [`UnionNode`][typing_graph.UnionNode]                           | Union types like `int \| str`              |
| [`is_literal_node`][typing_graph.is_literal_node]                           | [`LiteralNode`][typing_graph.LiteralNode]                       | Literal types like `Literal["a", "b"]`     |
| [`is_tuple_node`][typing_graph.is_tuple_node]                               | [`TupleNode`][typing_graph.TupleNode]                           | Tuple types                                |
| [`is_callable_node`][typing_graph.is_callable_node]                         | [`CallableNode`][typing_graph.CallableNode]                     | Callable types                             |
| [`is_dataclass_node`][typing_graph.is_dataclass_node]                       | [`DataclassNode`][typing_graph.DataclassNode]                   | Dataclass types                            |
| [`is_typed_dict_node`][typing_graph.is_typed_dict_node]                     | [`TypedDictNode`][typing_graph.TypedDictNode]                   | TypedDict types                            |
| [`is_forward_ref_node`][typing_graph.is_forward_ref_node]                   | [`ForwardRefNode`][typing_graph.ForwardRefNode]                 | Forward references                         |

See the [API reference][typing_graph.is_type_node] for the complete list of type guards.

### Filtering to concrete nodes

Find all concrete types in a complex type annotation:

```python
from typing_graph import inspect_type, walk, is_concrete_node

node = inspect_type(dict[str, list[tuple[int, float]]])

for concrete in walk(node, predicate=is_concrete_node):
    # Type narrowed: concrete is ConcreteNode
    print(concrete.cls.__name__)
```

Output:

```text
str
int
float
```

### Filtering to union nodes

Find all union types for special handling:

```python
from typing_graph import inspect_type, walk, is_union_type_node

node = inspect_type(dict[str | None, list[int] | tuple[float, ...]])

for union in walk(node, predicate=is_union_type_node):
    # Type narrowed: union is UnionNode
    member_names = [type(m).__name__ for m in union.members]
    print(f"Union with {len(union.members)} members: {member_names}")
```

Output:

```text
Union with 2 members: ['ConcreteNode', 'ConcreteNode']
Union with 2 members: ['SubscriptedGenericNode', 'TupleNode']
```

## Writing custom TypeIs predicates

When built-in type guards don't match your needs, write custom predicates. Using [`TypeIs`][typing_extensions.TypeIs] ensures type narrowing works correctly.

### Why TypeIs matters for type safety

A regular `bool` predicate filters correctly but doesn't narrow the type:

```python
from typing_graph import TypeNode

def has_metadata(n: TypeNode) -> bool:
    return len(n.metadata) > 0

# filtered is Iterator[TypeNode] - no narrowing
filtered = walk(node, predicate=has_metadata)
```

With `TypeIs`, the type checker knows the exact type:

```python
from typing_extensions import TypeIs
from typing_graph import TypeNode, ConcreteNode

def is_concrete_with_metadata(n: TypeNode) -> TypeIs[ConcreteNode]:
    return isinstance(n, ConcreteNode) and len(n.metadata) > 0

# filtered is Iterator[ConcreteNode] - narrowed!
filtered = walk(node, predicate=is_concrete_with_metadata)
```

Use `TypeIs` when you need to access type-specific attributes after filtering.

### Creating a metadata-based predicate

Filter nodes that have specific metadata types:

```python
from dataclasses import dataclass
from typing import Annotated
from typing_extensions import TypeIs
from typing_graph import inspect_type, walk, TypeNode

@dataclass(frozen=True)
class MaxLength:
    value: int

@dataclass(frozen=True)
class MinLength:
    value: int

def has_length_constraint(n: TypeNode) -> TypeIs[TypeNode]:
    """Check if node has MaxLength or MinLength metadata."""
    return any(isinstance(m, (MaxLength, MinLength)) for m in n.metadata)

# Complex nested type with constraints
UserName = Annotated[str, MinLength(1), MaxLength(50)]
Email = Annotated[str, MaxLength(255)]
UserData = dict[UserName, list[Email]]

node = inspect_type(UserData)
for constrained in walk(node, predicate=has_length_constraint):
    for meta in constrained.metadata:
        if isinstance(meta, (MaxLength, MinLength)):
            print(f"{type(meta).__name__}({meta.value})")
```

Output:

```text
MinLength(1)
MaxLength(50)
MaxLength(255)
```

### Creating a structural predicate

Filter based on node structure or properties:

```python
from typing import Callable
from typing_extensions import TypeIs
from typing_graph import (
    inspect_type,
    walk,
    TypeNode,
    SubscriptedGenericNode,
    is_subscripted_generic_node,
)

def is_collection_type(n: TypeNode) -> TypeIs[SubscriptedGenericNode]:
    """Check if node is a parameterized collection (list, set, dict, etc.)."""
    if not is_subscripted_generic_node(n):
        return False
    origin = n.origin.cls
    return origin in (list, set, frozenset, dict, tuple)

node = inspect_type(
    Callable[[list[int], dict[str, float]], set[str]]
)

for collection in walk(node, predicate=is_collection_type):
    origin_name = collection.origin.cls.__name__
    print(f"Found {origin_name} with {len(collection.args)} type argument(s)")
```

Output:

```text
Found list with 1 type argument(s)
Found dict with 2 type argument(s)
Found set with 1 type argument(s)
```

### Combining predicates

Compose multiple conditions for complex filtering:

```python
from typing import Annotated
from typing_extensions import TypeIs
from typing_graph import (
    inspect_type,
    walk,
    TypeNode,
    ConcreteNode,
    is_concrete_node,
)

def is_string_with_metadata(n: TypeNode) -> TypeIs[ConcreteNode]:
    """Match only string types that have metadata."""
    return (
        is_concrete_node(n)
        and n.cls is str
        and len(n.metadata) > 0
    )

Name = Annotated[str, "name"]
Age = Annotated[int, "age"]
Data = dict[Name, tuple[Age, Annotated[str, "description"]]]

node = inspect_type(Data)
for string_node in walk(node, predicate=is_string_with_metadata):
    print(f"String with metadata: {string_node.metadata}")
```

Output:

```text
String with metadata: MetadataCollection(['name'])
String with metadata: MetadataCollection(['description'])
```

## Controlling traversal depth

The `max_depth` parameter limits how deep `walk()` descends into the type graph.

### Understanding depth semantics

```text
dict[str, list[int]]
  ^        ^     ^
  |        |     +-- depth 2 (int)
  |        +-------- depth 1 (list[int], str)
  +----------------- depth 0 (root: dict[str, list[int]])
```

- `max_depth=0`: Yields only the root node
- `max_depth=1`: Yields root and its immediate children
- `max_depth=2`: Yields root, children, and grandchildren
- `max_depth=None` (default): No limit, traverses entire graph

```python
from typing_graph import inspect_type, walk

node = inspect_type(dict[str, list[tuple[int, float]]])

for depth in range(4):
    count = len(list(walk(node, max_depth=depth)))
    print(f"max_depth={depth}: {count} nodes")
```

Output:

```text
max_depth=0: 1 nodes
max_depth=1: 4 nodes
max_depth=2: 6 nodes
max_depth=3: 8 nodes
```

### Shallow scanning patterns

Examine only top-level structure without descending:

```python
from typing_graph import inspect_type, walk, is_subscripted_generic_node

# Complex nested type
node = inspect_type(dict[str, list[dict[int, set[float]]]])

# Only check immediate children for generics
for child in walk(node, predicate=is_subscripted_generic_node, max_depth=1):
    print(f"Top-level generic: {child.origin.cls.__name__}")
```

Output:

```text
Top-level generic: dict
Top-level generic: list
```

### Performance optimization

Limit depth when you only need shallow information:

```python
from typing_graph import inspect_type, walk, is_union_type_node

# For API validation, you might only care about top-level optionality
def check_top_level_unions(annotation: type) -> list[str]:
    """Find union types at the top two levels only."""
    node = inspect_type(annotation)
    unions = []
    for union in walk(node, predicate=is_union_type_node, max_depth=2):
        member_types = [type(m).__name__ for m in union.members]
        unions.append(f"Union: {member_types}")
    return unions

result = check_top_level_unions(dict[str | None, list[int | float]])
for u in result:
    print(u)
```

Output:

```text
Union: ['ConcreteNode', 'ConcreteNode']
Union: ['ConcreteNode', 'ConcreteNode']
```

## Practical patterns

### Finding all types matching a constraint

Collect specific node types for analysis:

```python
from typing import Callable
from typing_graph import inspect_type, walk, is_concrete_node

def find_numeric_types(annotation: type) -> set[type]:
    """Find all numeric types used in an annotation."""
    numeric = (int, float, complex)
    node = inspect_type(annotation)
    return {
        n.cls
        for n in walk(node, predicate=is_concrete_node)
        if n.cls in numeric
    }

result = find_numeric_types(
    Callable[[int, str], dict[float, list[complex]]]
)
print(result)  # {<class 'int'>, <class 'float'>, <class 'complex'>}
```

### Building a type registry

Collect all concrete types for dependency analysis:

```python
from typing_graph import inspect_type, walk, is_concrete_node, ConcreteNode

def build_type_registry(
    annotations: dict[str, type]
) -> dict[str, set[type]]:
    """Map annotation names to the concrete types they use."""
    registry: dict[str, set[type]] = {}
    for name, annotation in annotations.items():
        node = inspect_type(annotation)
        registry[name] = {
            n.cls for n in walk(node, predicate=is_concrete_node)
        }
    return registry

# Example API type annotations
api_types = {
    "UserResponse": dict[str, list[int]],
    "Config": tuple[str, bool, float],
}

registry = build_type_registry(api_types)
for name, types in registry.items():
    type_names = sorted(t.__name__ for t in types)
    print(f"{name}: {type_names}")
```

Output:

```text
UserResponse: ['int', 'str']
Config: ['bool', 'float', 'str']
```

### Validating type structures

Check that types meet specific criteria:

```python
from typing_graph import (
    inspect_type,
    walk,
    is_forward_ref_node,
    is_any_node,
)

def validate_no_forward_refs(annotation: type) -> list[str]:
    """Return warnings for any unresolved forward references."""
    node = inspect_type(annotation)
    warnings = []
    for ref in walk(node, predicate=is_forward_ref_node):
        warnings.append(f"Unresolved forward reference: {ref.ref}")
    return warnings

def validate_no_any(annotation: type) -> list[str]:
    """Return warnings for Any usage."""
    node = inspect_type(annotation)
    warnings = []
    for _ in walk(node, predicate=is_any_node):
        warnings.append("Found 'Any' type - consider using a more specific type")
    return warnings

# Combine validators
def validate_type(annotation: type) -> list[str]:
    """Run all type validations."""
    return validate_no_forward_refs(annotation) + validate_no_any(annotation)
```

## Result

You can now filter type graphs efficiently using `walk()` with built-in type guards for automatic narrowing, custom `TypeIs` predicates for domain-specific filtering, and depth limits for performance. These techniques enable type-safe iteration over exactly the nodes you need.

## See also

- [`walk()`][typing_graph.walk] - API reference for the walk iterator
- [Walking the type graph](walking-type-graph.md) - Manual recursion with `children()`
- [Type guards][typing_graph.is_type_node] - Complete list of built-in type guards
- [Your first type inspection](../tutorials/first-inspection.md) - Tutorial basics
- [`TypeIs`](https://typing-extensions.readthedocs.io/en/latest/index.html#typeis) - External typing-extensions reference
