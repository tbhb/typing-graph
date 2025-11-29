# Type aliases

This page explains how typing-graph handles type aliases, including both traditional `TypeAlias` annotations and the newer PEP 695 `type` statement syntax.

## What are type aliases?

Type aliases give names to complex types, making code more readable:

```python
# Without alias
def process(data: dict[str, list[tuple[int, str]]]) -> None: ...

# With alias
DataMap = dict[str, list[tuple[int, str]]]
def process(data: DataMap) -> None: ...
```

Python has two syntaxes for type aliases: the traditional approach using assignments and the newer PEP 695 `type` statement.

## Traditional type aliases

Before Python 3.12, developers created type aliases through simple assignment:

```python
from typing import TypeAlias

# Implicit alias (just assignment)
UserId = int

# Explicit alias annotation (Python 3.10+)
Vector: TypeAlias = list[float]
```

Python evaluates these aliases at definition time, and they exist as regular Python objects at runtime.

### Inspecting traditional aliases

Use [`inspect_type_alias()`][typing_graph.inspect_type_alias] to inspect traditional aliases. This produces a [`TypeAliasNode`][typing_graph.TypeAliasNode] containing the alias name and its underlying [`TypeNode`][typing_graph.TypeNode] value:

```python
from typing import TypeAlias
from typing_graph import inspect_type_alias, TypeAliasNode

Vector: TypeAlias = list[float]

node = inspect_type_alias(Vector, name="Vector")
print(type(node).__name__)  # TypeAliasNode
print(node.name)            # Vector
print(node.value)           # SubscriptedGenericNode(origin=list, args=(ConcreteNode(cls=float),))
```

You must provide the `name` parameter because simple type aliases don't inherently carry their name at runtime—they're just references to the aliased type.

## Type aliases with PEP 695 (Python 3.12+)

[PEP 695](https://peps.python.org/pep-0695/) introduced a dedicated `type` statement for defining type aliases:

```python
# Python 3.12+
# Simple alias
type UserId = int

# Generic alias with type parameter
type Vector[T] = list[T]

# Alias with bounds
type NumberList[T: (int, float)] = list[T]
```

This syntax offers key advantages:

- **Explicit declaration**: Clear that this is a type alias, not a variable
- **Lazy evaluation**: The aliased type isn't evaluated until used
- **Scoped type parameters**: Type parameters are local to the alias
- **Runtime introspectable**: The alias carries its name and parameters

### Inspecting aliases defined with PEP 695

typing-graph represents PEP 695 type aliases as [`GenericAliasNode`][typing_graph.GenericAliasNode] when they have type parameters:

```python
# snippet - PEP 695 alias inspection not yet implemented
from typing_graph import inspect_type_alias, GenericAliasNode

type Vector[T] = list[T]

node = inspect_type_alias(Vector)
print(type(node).__name__)  # GenericAliasNode
print(node.name)            # Vector
print(node.type_params)     # (TypeVarNode(name='T', ...),)
print(node.value)           # SubscriptedGenericNode referencing T
```

Simple PEP 695 aliases without type parameters still produce `GenericAliasNode` nodes with empty `type_params`:

```python
# snippet - PEP 695 alias inspection not yet implemented
type UserId = int

node = inspect_type_alias(UserId)
print(node.type_params)  # ()
print(node.value)        # ConcreteNode(cls=int)
```

## How type aliases differ from direct types

When inspecting a type directly, typing-graph produces a node for that type:

```python
from typing_graph import inspect_type

# Direct inspection produces ConcreteNode
node = inspect_type(int)
print(type(node).__name__)  # ConcreteNode
```

When inspecting a type alias, typing-graph preserves the alias wrapper:

```python
from typing import TypeAlias
from typing_graph import inspect_type_alias

UserId: TypeAlias = int

# Alias inspection preserves the wrapper
node = inspect_type_alias(UserId, name="UserId")
print(type(node).__name__)  # TypeAliasNode
print(node.value)           # ConcreteNode(cls=int)
```

If you use `inspect_type()` on an alias value, it sees through the alias to the underlying type.

## Scoped type parameters

PEP 695 scopes type parameters to their alias. This prevents naming conflicts:

```python
# Python 3.12+
# Each alias has its own T, they don't conflict
type Container[T] = list[T]
type Mapping[T, U] = dict[T, U]
```

typing-graph captures these scoped parameters in the [`GenericAliasNode.type_params`][typing_graph.GenericAliasNode] tuple. Each parameter becomes a [`TypeVarNode`][typing_graph.TypeVarNode], [`ParamSpecNode`][typing_graph.ParamSpecNode], or [`TypeVarTupleNode`][typing_graph.TypeVarTupleNode]:

```python
# snippet - PEP 695 alias inspection not yet implemented
type Transform[T, **P, *Ts] = Callable[P, tuple[T, *Ts]]

node = inspect_type_alias(Transform)
for param in node.type_params:
    print(f"{param.name}: {type(param).__name__}")
# T: TypeVarNode
# P: ParamSpecNode
# Ts: TypeVarTupleNode
```

## Type parameter bounds and constraints

Type parameters can have bounds or constraints:

```python
# Python 3.12+
from typing import Protocol

class Comparable(Protocol):
    def __lt__(self, other: object) -> bool: ...

# Bounded type parameter
type SortedList[T: Comparable] = list[T]

# Constrained type parameter
type Number[T: (int, float, complex)] = T
```

typing-graph captures these on the [`TypeVarNode`][typing_graph.TypeVarNode]:

```python
# snippet - PEP 695 alias inspection not yet implemented
type SortedList[T: Comparable] = list[T]

node = inspect_type_alias(SortedList)
type_var = node.type_params[0]
print(type_var.bound)        # ConcreteNode for Comparable
print(type_var.constraints)  # ()

type Number[T: (int, float, complex)] = T

node = inspect_type_alias(Number)
type_var = node.type_params[0]
print(type_var.bound)        # None
print(type_var.constraints)  # (ConcreteNode(int), ConcreteNode(float), ConcreteNode(complex))
```

## Node types summary

| Alias style | Node type | Has type params |
| ----------- | --------- | --------------- |
| Traditional (`TypeAlias`) | `TypeAliasNode` | No |
| PEP 695 simple (`type X = T`) | `GenericAliasNode` | Empty tuple |
| PEP 695 generic (`type X[T] = ...`) | `GenericAliasNode` | Contains params |

## See also

- [Generics and variance](generics.md) - Deep dive into type parameters and variance
- [Architecture overview](architecture.md) - How alias inspection fits into the design
- [PEP 695](https://peps.python.org/pep-0695/) - The specification for the `type` statement
