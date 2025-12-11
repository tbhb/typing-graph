# Union types

This page explains how typing-graph handles union types. With the default configuration, all unions are represented uniformly as [`UnionNode`][typing_graph.UnionNode], regardless of how they were created in Python.

## How typing-graph represents unions

By default, typing-graph normalizes all union types to [`UnionNode`][typing_graph.UnionNode]:

```python
from typing import Literal, Union
from typing_graph import inspect_type

# Both union syntaxes produce UnionNode
node1 = inspect_type(int | str)
node2 = inspect_type(Literal['a'] | Literal['b'])
node3 = inspect_type(Union[int, str])

print(type(node1).__name__)  # UnionNode
print(type(node2).__name__)  # UnionNode
print(type(node3).__name__)  # UnionNode

# Access members uniformly
print(node1.members)  # (ConcreteNode(cls=int), ConcreteNode(cls=str))
print(node2.members)  # (LiteralNode(...), LiteralNode(...))
```

This normalization matches Python 3.14 behavior, where all union expressions produce the same runtime type. typing-graph brings this consistency to all Python versions.

### Working with unions

Use the helper functions to work with union nodes:

```python
from typing import Literal
from typing_graph import inspect_type, is_union_node, get_union_members

node = inspect_type(int | str | None)

# Check if it's a union
print(is_union_node(node))  # True

# Get all members
print(get_union_members(node))  # (ConcreteNode(cls=int), ConcreteNode(cls=str), NoneTypeNode())
```

For `Optional` types (unions containing `None`):

```python
from typing_graph import inspect_type, is_optional_node, unwrap_optional

node = inspect_type(int | None)

print(is_optional_node(node))  # True
print(unwrap_optional(node))   # (ConcreteNode(cls=int),)
```

## Why typing-graph normalizes by default

This normalization simplifies your code by providing a consistent interface for all union types.

!!! note "Benefits of normalization"

    1. **Simplified code** - Handle all unions uniformly with `UnionNode`
    2. **Forward compatibility** - Code written today works identically on Python 3.14+
    3. **Consistent API** - No need to check for two different union representations

## Preserving native representation

Set [`normalize_unions=False`][typing_graph.InspectConfig] when you need to see exactly what Python created at runtime:

```python
from typing import Literal
from typing_graph import InspectConfig, inspect_type

config = InspectConfig(normalize_unions=False)

# types.UnionType → UnionNode (unchanged)
node1 = inspect_type(int | str, config=config)
print(type(node1).__name__)  # UnionNode

# typing.Union → SubscriptedGenericNode (preserved)
node2 = inspect_type(Literal['a'] | Literal['b'], config=config)
print(type(node2).__name__)  # SubscriptedGenericNode
print(node2.origin.cls)      # typing.Union
print(node2.args)            # (LiteralNode(...), LiteralNode(...))
```

!!! tip "When to turn off normalization"

    - **Round-trip fidelity** - Reconstruct the exact original type annotation
    - **Debugging** - See exactly what Python created at runtime
    - **Legacy compatibility** - Match behavior of typing-graph < 1.0

    For most use cases, the default normalization simplifies code by ensuring all unions are handled uniformly.

## Background: Python's union duality

Python's type system evolved in stages, creating an inconsistency that typing-graph abstracts away.

[PEP 484](https://peps.python.org/pep-0484/) (2014) introduced `typing.Union` as a way to express that a value could be one of several types. Later, [PEP 604](https://peps.python.org/pep-0604/) (2020) added the `|` operator syntax, which creates a `types.UnionType` object for concrete types.

However, the `|` operator also needed to work with typing special forms like `Literal` and `Optional`. These types already had their own `__or__` methods that returned `typing.Union`. Changing this behavior would break backward compatibility.

The result: `int | str` creates `types.UnionType`, but `Literal[1] | Literal[2]` creates `typing.Union`. Same operator, different result types:

| Type              | Created by                                                            | Example                                       |
| ----------------- | --------------------------------------------------------------------- | --------------------------------------------- |
| `types.UnionType` | [PEP 604](https://peps.python.org/pep-0604/) `\|` with concrete types | `int \| str`                                  |
| `typing.Union`    | `typing.Union[...]` or `\|` with typing special forms                 | `Union[int, str]`, `Literal[1] \| Literal[2]` |

You can see this directly in Python:

```python
from typing import Literal, get_origin, Union
import types

# Concrete types → types.UnionType
concrete_union = int | str
print(isinstance(concrete_union, types.UnionType))  # True

# Literal types → typing.Union (!)
literal_union = Literal['a'] | Literal['b']
print(isinstance(literal_union, types.UnionType))   # False
print(get_origin(literal_union) is Union)           # True
```

Python 3.14 fixes this by unifying both forms. In Python 3.14, `types.UnionType` becomes an alias for `typing.Union`, and all union expressions produce the same runtime type. typing-graph brings this consistency to all Python versions through its default `normalize_unions=True` behavior, so code you write today will work identically on Python 3.14+ without changes.

## Practical application

Whether you're building a validation library, serialization framework, or code analysis tool, typing-graph's union normalization means you can focus on your application logic rather than Python's union implementation details. Use `normalize_unions=False` only when you specifically need to distinguish between the underlying representations.

- **Complete guide to union handling** in [Working with unions](../guides/working-with-unions.md)
- **Handle unions during traversal** with [Walking the type graph](../guides/walking-type-graph.md)
- **Inspect union type parameters** in [Inspecting functions](../tutorials/functions.md)

## See also

**Helper functions:**

- [`is_union_node()`][typing_graph.is_union_node] - Check if a node represents any union type
- [`get_union_members()`][typing_graph.get_union_members] - Extract members from either union form
- [`is_optional_node()`][typing_graph.is_optional_node] - Check if a union contains `None`
- [`unwrap_optional()`][typing_graph.unwrap_optional] - Extract non-None types from an optional

**Related:**

- [Architecture overview](architecture.md) - How unions fit into the node hierarchy
- [Type node](../reference/glossary.md#type-node) - Glossary definition
- [Modernizing Union and Optional](https://typing.python.org/en/latest/guides/modernizing.html#typing-union-and-typing-optional) - Python typing docs on modern union syntax
- [PEP 604](https://peps.python.org/pep-0604/) - Union types via `X | Y` syntax
- [PEP 586](https://peps.python.org/pep-0586/) - Literal types

**Python standard library:**

- [`types.UnionType`](https://docs.python.org/3/library/types.html#types.UnionType) - The native union type ([PEP 604](https://peps.python.org/pep-0604/))
- [`typing.Union`](https://docs.python.org/3/library/typing.html#typing.Union) - The typing module union
- [`typing.Optional`](https://docs.python.org/3/library/typing.html#typing.Optional) - Shorthand for `Union[X, None]`
- [Union type expressions](https://docs.python.org/3/library/stdtypes.html#types-union) - `X | Y` syntax documentation
