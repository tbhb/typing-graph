# Union types

This page explains how Python represents union types and how typing-graph handles them. Union types have different runtime representations depending on how they are created, which typing-graph helps you navigate.

## Why two union types exist

Python has two different union representations due to how the type system evolved. This history explains the behavior you'll encounter when inspecting union types.

Python's type system evolved in stages. PEP 484 (2014) introduced `typing.Union` as a way to express that a value could be one of several types. This worked through the typing module's special form machinery.

Later, PEP 604 (2020) added the `|` operator syntax for unions: `int | str` instead of `Union[int, str]`. For concrete types, this operator creates a new `types.UnionType` object, which is a true Python type rather than a typing module construct.

However, the `|` operator also needed to work with typing special forms like `Literal` and `Optional`. These types already had their own `__or__` methods that returned `typing.Union`. Changing this behavior would break backward compatibility.

The result: `int | str` creates `types.UnionType`, but `Literal[1] | Literal[2]` creates `typing.Union`. Same operator, different result types.

## Two kinds of unions

Python has two different runtime representations for union types:

| Type              | Created by                                            | Example                                       |
| ----------------- | ----------------------------------------------------- | --------------------------------------------- |
| `types.UnionType` | PEP 604 `\|` with concrete types                      | `int \| str`                                  |
| `typing.Union`    | `typing.Union[...]` or `\|` with typing special forms | `Union[int, str]`, `Literal[1] \| Literal[2]` |

typing-graph represents these differently:

- `types.UnionType` → [`UnionNode`][typing_graph.UnionNode]
- `typing.Union` → [`SubscriptedGenericNode`][typing_graph.SubscriptedGenericNode] with `origin.cls=typing.Union`

## The `|` operator quirk

You might expect `Literal['a'] | Literal['b']` to produce `types.UnionType` since it uses the PEP 604 `|` syntax. However, it produces `typing.Union`:

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

This happens because `typing` module special forms like `Literal`, `List`, and `Optional` implement their own `__or__` method that returns `typing.Union` instead of delegating to Python's native union machinery.

### Which types produce which union?

| Expression                 | Result type       | Why                                  |
| -------------------------- | ----------------- | ------------------------------------ |
| `int \| str`               | `types.UnionType` | Concrete types use native `\|`       |
| `list[int] \| list[str]`   | `types.UnionType` | Built-in generics use native `\|`    |
| `Literal[1] \| Literal[2]` | `typing.Union`    | `typing._LiteralGenericAlias.__or__` |
| `List[int] \| List[str]`   | `typing.Union`    | `typing._GenericAlias.__or__`        |
| `Optional[int] \| str`     | `typing.Union`    | `typing._SpecialForm.__or__`         |

## How typing-graph represents unions

typing-graph reflects what Python provides at runtime. On Python < 3.14, the two union forms produce different node types:

```python
# Python < 3.14
from typing import Literal, Union
from typing_graph import inspect_type

# types.UnionType → UnionNode
node1 = inspect_type(int | str)
print(type(node1).__name__)  # UnionNode
print(node1.members)         # (ConcreteNode(cls=int), ConcreteNode(cls=str))

# typing.Union → SubscriptedGenericNode
node2 = inspect_type(Literal['a'] | Literal['b'])
print(type(node2).__name__)  # SubscriptedGenericNode
print(node2.origin.cls)      # typing.Union
print(node2.args)            # (LiteralNode(...), LiteralNode(...))
```

On Python 3.14+, `types.UnionType` is an alias for `typing.Union`, so both forms produce `UnionNode`:

```python
# Python 3.14+
from typing import Literal, Union
from typing_graph import inspect_type

# Both union forms now produce UnionNode
node1 = inspect_type(int | str)
print(type(node1).__name__)  # UnionNode

node2 = inspect_type(Literal['a'] | Literal['b'])
print(type(node2).__name__)  # UnionNode
print(node2.members)         # (LiteralNode(...), LiteralNode(...))
```

!!! warning "Check order matters on Python < 3.14"

    When handling unions in conditional logic, always check `is_union_node()` **before**
    `is_subscripted_generic_node()`. Both `UnionNode` and `typing.Union`
    (represented as `SubscriptedGenericNode`) are valid union forms.

    ```python
    # snippet - illustrative pattern
    from typing_graph import (
        is_union_node,
        is_subscripted_generic_node,
        get_union_members,
    )

    # Correct order
    if is_union_node(node):
        members = get_union_members(node)
    elif is_subscripted_generic_node(node):
        # Handle other subscripted generics like list[int]
        ...
    ```

    Using the helper functions `is_union_node()` and `get_union_members()` handles
    both union forms uniformly and is the recommended approach.

### Working with both forms

Use the helper functions to handle both union forms uniformly:

```python
from typing import Literal
from typing_graph import inspect_type, is_union_node, get_union_members

# is_union_node() returns True for either form
node1 = inspect_type(int | str)
node2 = inspect_type(Literal['a'] | Literal['b'])

print(is_union_node(node1))  # True
print(is_union_node(node2))  # True

# get_union_members() extracts members from either form
print(get_union_members(node1))  # (ConcreteNode(cls=int), ConcreteNode(cls=str))
print(get_union_members(node2))  # (LiteralNode(...), LiteralNode(...))
```

## Why typing-graph preserves the distinction

typing-graph reflects what Python gives it rather than normalizing union forms. This design decision deserves explanation because the alternative (always producing `UnionNode`) would simplify the API.

!!! note "Design trade-off: preservation vs normalization"

    We chose preservation because normalization loses information that some use cases need:

    1. **Round-trip fidelity** - You can reconstruct the original type annotation
    2. **Debugging accuracy** - The node structure matches what Python actually creates
    3. **Future compatibility** - If Python's behavior changes, typing-graph reflects those changes

    The trade-off is API complexity: code that handles unions must consider both forms on Python < 3.14. The helper functions `is_union_node()` and `get_union_members()` exist specifically to make this easier.

    We considered automatic normalization but rejected it because it would hide real differences in Python's runtime behavior. These differences can matter for serialization, debugging, and understanding edge cases.

## Implications for type checking

This distinction rarely matters in practice because static type checkers treat both union forms equivalently. However, if you're doing runtime introspection on Python < 3.14, be aware that:

- `int | str` produces `UnionNode` with a `members` attribute
- `Literal[1] | Literal[2]` produces `SubscriptedGenericNode` with `origin.cls=typing.Union` and `args`

On Python 3.14+, both forms produce `UnionNode`, so you only need to handle one case.

??? info "Python 3.14: union unification"

    Python 3.14 unifies `types.UnionType` and `typing.Union`. The `types.UnionType` type becomes an alias for `typing.Union`, and all union expressions produce the same runtime type.

    This unification simplifies the landscape considerably. If you're writing new code that only needs to support Python 3.14+, you can ignore the distinction entirely and always use `UnionNode`.

    For libraries that need to support older Python versions, the helper functions remain the best approach. They abstract over the version differences and will continue working correctly on Python 3.14+.

## Practical application

Now that you understand union types, apply this knowledge:

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

- [`types.UnionType`](https://docs.python.org/3/library/types.html#types.UnionType) - The native union type (PEP 604)
- [`typing.Union`](https://docs.python.org/3/library/typing.html#typing.Union) - The typing module union
- [`typing.Optional`](https://docs.python.org/3/library/typing.html#typing.Optional) - Shorthand for `Union[X, None]`
- [Union type expressions](https://docs.python.org/3/library/stdtypes.html#types-union) - `X | Y` syntax documentation
