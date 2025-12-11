# How to work with union types

This guide shows you how to handle union types in typing-graph. You'll learn to detect unions, extract their members, handle optional types, and dispatch on type structure.

## Prerequisites

- Familiarity with typing-graph's [`inspect_type()`][typing_graph.inspect_type] function
- Understanding of Python's union syntax (`int | str`, `Optional[int]`)

## Detecting unions in your code

Use [`is_union_node()`][typing_graph.is_union_node] to check if a node represents a union type:

```python
from typing_graph import inspect_type, is_union_node

node = inspect_type(int | str)
print(is_union_node(node))  # True

node = inspect_type(list[int])
print(is_union_node(node))  # False
```

This works regardless of how the union was created or whether normalization is enabled. See [Common helper functions](common-helpers.md#check-if-a-node-represents-a-union) for more examples.

## Processing union members

Once you've identified a union, use [`get_union_members()`][typing_graph.get_union_members] to iterate over its members:

```python
from typing_graph import inspect_type, is_union_node, get_union_members

node = inspect_type(int | str | float)

if is_union_node(node):
    members = get_union_members(node)
    for member in members:
        print(f"Member type: {member}")
```

A common pattern is collecting information from each member:

```python
from typing_graph import inspect_type, is_union_node, get_union_members, is_concrete_node


def get_concrete_classes(node):
    """Extract concrete classes from a union type."""
    if not is_union_node(node):
        return []

    classes = []
    members = get_union_members(node)
    for member in members:
        if is_concrete_node(member):
            classes.append(member.cls)
    return classes


node = inspect_type(int | str | list[int])
print(get_concrete_classes(node))  # [<class 'int'>, <class 'str'>]
```

See [Common helper functions](common-helpers.md#extract-members-from-a-union) for the function signature and basic examples.

## Handling optional types

Optional types (`T | None`, `Optional[T]`) deserve special handling because they're so common. typing-graph provides dedicated helpers for them.

### Detecting optionals

Use [`is_optional_node()`][typing_graph.is_optional_node] to check if a type includes `None`:

```python
from typing import Optional
from typing_graph import inspect_type, is_optional_node

# All of these are optional
print(is_optional_node(inspect_type(int | None)))  # True
print(is_optional_node(inspect_type(Optional[str])))  # True
print(is_optional_node(inspect_type(str | int | None)))  # True

# These are not optional
print(is_optional_node(inspect_type(int | str)))  # False
print(is_optional_node(inspect_type(int)))  # False
```

### Extracting the inner type

Use [`unwrap_optional()`][typing_graph.unwrap_optional] to get the non-None types:

```python
from typing_graph import inspect_type, unwrap_optional, is_concrete_node

# Simple optional: one inner type
node = inspect_type(int | None)
unwrapped = unwrap_optional(node)
if unwrapped and is_concrete_node(unwrapped[0]):
    print(unwrapped[0].cls)  # <class 'int'>

# Multi-type optional: multiple inner types
node = inspect_type(str | int | None)
unwrapped = unwrap_optional(node)
print(len(unwrapped))  # 2
```

!!! warning "Always check the return value"
    `unwrap_optional()` returns `None` for non-optional types. Always check before accessing the result:

    ```python
    unwrapped = unwrap_optional(node)
    if unwrapped is None:
        # Handle non-optional type
        pass
    elif len(unwrapped) == 1:
        # Simple optional like `int | None`
        inner_type = unwrapped[0]
    else:
        # Multi-type optional like `str | int | None`
        inner_types = unwrapped
    ```

## Dispatching on type structure

When building type-aware code (validators, serializers, schema generators), you often need different logic for different type structures. The recommended check order is:

1. **Optional first** - Handle `None` cases before general unions
2. **Union second** - Process union members
3. **Other types last** - Handle concrete types, generics, etc.

Here's a complete dispatch pattern:

```python
from typing_graph import (
    TypeNode,
    get_union_members,
    inspect_type,
    is_concrete_node,
    is_optional_node,
    is_subscripted_generic_node,
    is_union_node,
    unwrap_optional,
)


def describe_type(node: TypeNode) -> str:
    """Generate a human-readable description of a type."""
    # 1. Check optional first (before general union)
    if is_optional_node(node):
        unwrapped = unwrap_optional(node)
        if unwrapped and len(unwrapped) == 1:
            inner = describe_type(unwrapped[0])
            return f"optional {inner}"
        elif unwrapped:
            inner_types = [describe_type(t) for t in unwrapped]
            return f"optional ({' or '.join(inner_types)})"

    # 2. Check union second
    if is_union_node(node):
        members = get_union_members(node)
        if members:
            member_descs = [describe_type(m) for m in members]
            return " or ".join(member_descs)

    # 3. Handle other types
    if is_concrete_node(node):
        return node.cls.__name__

    if is_subscripted_generic_node(node):
        origin = node.origin.cls.__name__
        args = ", ".join(describe_type(arg) for arg in node.args)
        return f"{origin}[{args}]"

    return "unknown"


# Test the dispatcher
print(describe_type(inspect_type(int)))  # int
print(describe_type(inspect_type(int | str)))  # int or str
print(describe_type(inspect_type(int | None)))  # optional int
print(describe_type(inspect_type(list[int])))  # list[int]
print(describe_type(inspect_type(str | int | None)))  # optional (str or int)
```

!!! tip "Why check optional before union?"
    Optional types *are* unions (they contain `None`), so `is_union_node()` returns `True` for them. Checking `is_optional_node()` first lets you handle the `None` case specially.

## Understanding union normalization

By default, typing-graph normalizes all union types to [`UnionNode`][typing_graph.UnionNode], regardless of how Python created them at runtime. This means your code doesn't need to handle different union representations.

```python
from typing import Literal, Union
from typing_graph import inspect_type

# All produce UnionNode with default settings
node1 = inspect_type(int | str)
node2 = inspect_type(Union[int, str])
node3 = inspect_type(Literal["a"] | Literal["b"])

print(type(node1).__name__)  # UnionNode
print(type(node2).__name__)  # UnionNode
print(type(node3).__name__)  # UnionNode
```

For the rationale behind [normalization](../explanation/union-types.md#why-typing-graph-normalizes-by-default) and details on [Python's union duality](../explanation/union-types.md#background-pythons-union-duality), see the [Union types](../explanation/union-types.md) explanation page.

## Opting out of normalization

Sometimes you need to see exactly what Python created at runtime. Set `normalize_unions=False` to [preserve the native representation](../explanation/union-types.md#preserving-native-representation):

```python
from typing import Literal
from typing_graph import InspectConfig, inspect_type

config = InspectConfig(normalize_unions=False)

# types.UnionType stays as UnionNode
node1 = inspect_type(int | str, config=config)
print(type(node1).__name__)  # UnionNode

# typing.Union becomes SubscriptedGenericNode
node2 = inspect_type(Literal["a"] | Literal["b"], config=config)
print(type(node2).__name__)  # SubscriptedGenericNode
```

When you turn off normalization, you'll need to handle both representations:

```python
from typing import Union
from typing_graph import (
    InspectConfig,
    SubscriptedGenericNode,
    TypeNode,
    UnionNode,
    inspect_type,
)

config = InspectConfig(normalize_unions=False)


def get_members_without_normalization(node: TypeNode) -> tuple[TypeNode, ...] | None:
    """Extract union members when normalization is turned off."""
    if isinstance(node, UnionNode):
        return node.members

    if isinstance(node, SubscriptedGenericNode) and node.origin.cls is Union:
        return node.args

    return None
```

!!! note "When to turn off normalization"
    - **Round-trip fidelity** - Reconstructing the exact original annotation
    - **Debugging** - Investigating Python's runtime type representation
    - **Legacy compatibility** - Matching pre-1.0 typing-graph behavior

    For most use cases, leave normalization enabled.

See [Configuration options](configuration.md) for more on `InspectConfig`.

## Result

You can now detect union types, extract their members, handle optional types correctly, and build dispatch logic for type-aware applications. Whether you're validating data, generating schemas, or building serializers, these patterns provide a solid foundation for union handling.

## Next steps

- [Common helper functions](common-helpers.md) - Function signatures and basic examples
- [Union types](../explanation/union-types.md) - Why Python has two union representations
- [Configuration options](configuration.md) - All `InspectConfig` settings
- [Filtering with walk()](filtering-with-walk.md) - Use type guards with graph traversal
