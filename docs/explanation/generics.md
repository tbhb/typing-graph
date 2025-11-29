# Generics and variance

This page explains how typing-graph represents generic types, type parameters, and variance.

## What are generics?

Generics let you parameterize types with other types. Instead of writing separate container classes for each element type, you write one generic class that works with any type:

```python
from typing import Generic, TypeVar

T = TypeVar('T')

class Box(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value

int_box: Box[int] = Box(42)
str_box: Box[str] = Box("hello")
```

Python's built-in types like `list`, `dict`, and `set` are all generic.

## Type parameters

Type parameters are placeholders that get filled in when you use a generic type. Python has three kinds:

### Using TypeVar for single types

[`TypeVar`](https://docs.python.org/3/library/typing.html#typing.TypeVar) represents a single type:

```python
from typing import TypeVar

T = TypeVar('T')  # Can be any type
N = TypeVar('N', bound=int)  # Must be int or subtype
S = TypeVar('S', str, bytes)  # Must be exactly str or bytes
```

typing-graph represents these as [`TypeVarNode`][typing_graph.TypeVarNode]:

```python
from typing import TypeVar
from typing_graph import inspect_type

T = TypeVar('T', bound=int)
node = inspect_type(T)

print(node.name)        # T
print(node.bound)       # ConcreteNode(cls=int)
print(node.constraints) # ()
print(node.variance)    # Variance.INVARIANT
```

### The ParamSpec type

[`ParamSpec`](https://docs.python.org/3/library/typing.html#typing.ParamSpec) (PEP 612) captures the entire parameter list of a callable:

```python
from typing import Callable, ParamSpec, TypeVar

P = ParamSpec('P')
R = TypeVar('R')

def decorator(f: Callable[P, R]) -> Callable[P, R]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return f(*args, **kwargs)
    return wrapper
```

typing-graph represents these as [`ParamSpecNode`][typing_graph.ParamSpecNode]:

```python
from typing import ParamSpec
from typing_graph import inspect_type

P = ParamSpec('P')
node = inspect_type(P)

print(type(node).__name__)  # ParamSpecNode
print(node.name)            # P
```

### Using TypeVarTuple for variadic types

[`TypeVarTuple`](https://docs.python.org/3/library/typing.html#typing.TypeVarTuple) (PEP 646) captures a variable number of types:

```python
# snippet - PEP 646 unpack syntax requires Python 3.11+
from typing import TypeVarTuple

Ts = TypeVarTuple('Ts')

def concat(*args: *Ts) -> tuple[*Ts]:
    return args
```

typing-graph represents these as [`TypeVarTupleNode`][typing_graph.TypeVarTupleNode]:

```python
from typing_extensions import TypeVarTuple
from typing_graph import inspect_type

Ts = TypeVarTuple('Ts')
node = inspect_type(Ts)

print(type(node).__name__)  # TypeVarTupleNode
print(node.name)            # Ts
```

## Comparing unsubscripted and subscripted generics

A generic type can appear in two forms:

1. **Unsubscripted**: The generic without type arguments (`list`, `Dict`)
2. **Subscripted**: The generic with type arguments applied (`list[int]`, `Dict[str, Any]`)

typing-graph represents these as [`GenericTypeNode`][typing_graph.GenericTypeNode] and [`SubscriptedGenericNode`][typing_graph.SubscriptedGenericNode] respectively:

```python
from typing_graph import inspect_type, GenericTypeNode, SubscriptedGenericNode

# Unsubscripted generic
node = inspect_type(list)
print(type(node).__name__)  # GenericTypeNode
print(node.cls)             # <class 'list'>

# Subscripted generic
node = inspect_type(list[int])
print(type(node).__name__)  # SubscriptedGenericNode
print(node.origin)          # GenericTypeNode for list
print(node.args)            # (ConcreteNode(cls=int),)
```

### Nested generics

You can nest generics arbitrarily:

```python
from typing_graph import inspect_type

# dict[str, list[int]]
node = inspect_type(dict[str, list[int]])

print(type(node).__name__)    # SubscriptedGenericNode
print(len(node.args))         # 2

key_node = node.args[0]       # ConcreteNode(cls=str)
value_node = node.args[1]     # SubscriptedGenericNode for list[int]
```

## Variance

Variance describes how subtyping of type parameters relates to subtyping of the generic type itself.

### Invariance (default)

With an invariant type parameter, `Box[Cat]` is neither a subtype nor supertype of `Box[Animal]`:

```python
from typing import TypeVar, Generic

T = TypeVar('T')  # Invariant by default

class Box(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value

# Box[Cat] is NOT compatible with Box[Animal]
```

### Covariance

With a covariant type parameter, if `Cat` is a subtype of `Animal`, then `Box[Cat]` is a subtype of `Box[Animal]`:

```python
from typing import TypeVar, Generic

T_co = TypeVar('T_co', covariant=True)

class ReadOnlyBox(Generic[T_co]):
    def __init__(self, value: T_co) -> None:
        self._value = value

    def get(self) -> T_co:
        return self._value

# ReadOnlyBox[Cat] IS compatible with ReadOnlyBox[Animal]
```

Covariance is safe when the type parameter only appears in output positions (return types).

### Contravariance

With a contravariant type parameter, if `Cat` is a subtype of `Animal`, then `Handler[Animal]` is a subtype of `Handler[Cat]`:

```python
from typing import TypeVar, Generic

T_contra = TypeVar('T_contra', contravariant=True)

class Handler(Generic[T_contra]):
    def handle(self, value: T_contra) -> None:
        ...

# Handler[Animal] IS compatible with Handler[Cat]
```

Contravariance is safe when the type parameter only appears in input positions (parameter types).

### Checking variance

typing-graph captures variance on [`TypeVarNode`][typing_graph.TypeVarNode]:

```python
from typing import TypeVar
from typing_graph import inspect_type, Variance

T_co = TypeVar('T_co', covariant=True)
T_contra = TypeVar('T_contra', contravariant=True)
T = TypeVar('T')

print(inspect_type(T_co).variance)      # Variance.COVARIANT
print(inspect_type(T_contra).variance)  # Variance.CONTRAVARIANT
print(inspect_type(T).variance)         # Variance.INVARIANT
```

### Automatic variance inference in PEP 695

PEP 695 introduced automatic variance inference. When you use the `type` statement, Python infers variance from how you use the type parameter:

```python
# snippet - PEP 695 syntax requires Python 3.12+
type ReadOnlyBox[T] = ...  # Variance inferred from usage
```

typing-graph captures this with the `infer_variance` flag:

```python
# snippet - illustrative
# For PEP 695 type parameters
print(type_var_node.infer_variance)  # True if auto-inferred
```

## Type parameter bounds and constraints

### Bounds

A bound restricts a type parameter to a type or its subtypes:

```python
from typing import TypeVar

T = TypeVar('T', bound=int)  # T must be int or a subtype

def double(x: T) -> T:
    return x * 2  # Works because int supports *
```

```python
from typing import TypeVar
from typing_graph import inspect_type

T = TypeVar('T', bound=int)
node = inspect_type(T)

print(node.bound)  # ConcreteNode(cls=int)
```

### Constraints

Constraints restrict a type parameter to specific types (not subtypes):

```python
from typing import TypeVar

T = TypeVar('T', str, bytes)  # T must be exactly str or bytes

def process(data: T) -> T:
    return data.upper()  # Works because both str and bytes have upper()
```

```python
from typing import TypeVar
from typing_graph import inspect_type

T = TypeVar('T', str, bytes)
node = inspect_type(T)

print(node.constraints)  # (ConcreteNode(cls=str), ConcreteNode(cls=bytes))
```

## Type parameter defaults (PEP 696)

Python 3.13 introduces default values for type parameters:

```python
# snippet - PEP 696 requires Python 3.13+
from typing import TypeVar

T = TypeVar('T', default=int)

class Container(Generic[T]):
    ...

# Container() is equivalent to Container[int]
```

typing-graph captures defaults on all type parameter nodes:

```python
# snippet - illustrative
print(type_var_node.default)  # TypeNode or None
```

## Node summary

| Concept | Node type | Key attributes |
| ------- | --------- | -------------- |
| Type variable | `TypeVarNode` | `name`, `variance`, `bound`, `constraints`, `default` |
| Parameter spec | `ParamSpecNode` | `name`, `default` |
| Variadic type | `TypeVarTupleNode` | `name`, `default` |
| Unsubscripted generic | `GenericTypeNode` | `cls`, `type_params` |
| Subscripted generic | `SubscriptedGenericNode` | `origin`, `args` |

## See also

- [Type aliases](type-aliases.md) - How typing-graph represents generic type aliases
- [Architecture overview](architecture.md) - How generic inspection fits into the design
- [PEP 484](https://peps.python.org/pep-0484/) - Type hints specification
- [PEP 612](https://peps.python.org/pep-0612/) - ParamSpec
- [PEP 646](https://peps.python.org/pep-0646/) - TypeVarTuple
- [PEP 695](https://peps.python.org/pep-0695/) - Type parameter syntax
- [PEP 696](https://peps.python.org/pep-0696/) - Type parameter defaults
