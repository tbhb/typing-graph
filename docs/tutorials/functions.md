# Inspecting functions

In this tutorial, you'll learn how to inspect function signatures to extract parameter and return type information.

## What you'll learn

- How to use `inspect_function()` to analyze functions
- How to access parameter information
- How to work with return types
- How to inspect class methods

## Prerequisites

- Completed the [Your first type inspection](first-inspection.md) tutorial

## Defining a typed function

Start with a function that has type annotations:

```python
from typing import Annotated
from dataclasses import dataclass

@dataclass(frozen=True)
class Positive:
    """Marks a value that must be positive."""
    pass

def calculate_total(
    items: list[float],
    tax_rate: Annotated[float, Positive()],
    discount: float = 0.0,
) -> float:
    """Calculate the total price with tax and discount."""
    subtotal = sum(items)
    return subtotal * (1 + tax_rate) - discount
```

## Inspecting a function

Use [`inspect_function()`][typing_graph.inspect_function] to analyze a function:

```python
from typing_graph import inspect_function

func = inspect_function(calculate_total)
print(type(func))  # <class 'typing_graph.FunctionNode'>
print(func.name)   # calculate_total
```

The [`FunctionNode`][typing_graph.FunctionNode] provides access to the function's signature through its `signature` attribute:

```python
sig = func.signature
print(type(sig))  # <class 'typing_graph.SignatureNode'>
```

The [`SignatureNode`][typing_graph.SignatureNode] contains the parameters and return type information.

## Accessing parameters

The signature's `parameters` attribute returns a tuple of [`Parameter`][typing_graph.Parameter] objects:

```python
for param in sig.parameters:
    print(f"Parameter: {param.name}")
    print(f"  Kind: {param.kind}")
    print(f"  Has default: {param.default is not None}")
    print()
```

Output:

```text
Parameter: items
  Kind: ParameterKind.POSITIONAL_OR_KEYWORD
  Has default: False

Parameter: tax_rate
  Kind: ParameterKind.POSITIONAL_OR_KEYWORD
  Has default: False

Parameter: discount
  Kind: ParameterKind.POSITIONAL_OR_KEYWORD
  Has default: True
```

### Parameter kinds

The `kind` attribute indicates how to pass the parameter:

- `POSITIONAL_ONLY` - Only positional (`param, /`)
- `POSITIONAL_OR_KEYWORD` - Either way (default)
- `VAR_POSITIONAL` - `*args`
- `KEYWORD_ONLY` - Only keyword (`*, param`)
- `VAR_KEYWORD` - `**kwargs`

### Accessing parameter types

Each parameter has a `type` attribute containing the inspected type node:

```python
from typing_graph import ConcreteNode, SubscriptedGenericNode

for param in sig.parameters:
    type_node = param.type
    print(f"{param.name}: {type(type_node).__name__}")

    # Check for metadata
    if type_node.metadata:
        print(f"  Metadata: {type_node.metadata}")
```

Output:

```text
items: SubscriptedGenericNode
tax_rate: ConcreteNode
  Metadata: (Positive(),)
discount: ConcreteNode
```

## Accessing the return type

The signature's `returns` attribute contains the return type node:

```python
return_type = sig.returns
print(type(return_type))  # <class 'typing_graph.ConcreteNode'>
print(return_type.cls)    # <class 'float'>
```

For functions returning complex types:

```python
def get_users() -> list[dict[str, str]]:
    return []

func = inspect_function(get_users)
return_node = func.signature.returns

print(return_node.origin.cls)  # <class 'list'>
element_type = return_node.args[0]
print(element_type.origin.cls)  # <class 'dict'>
```

## Inspecting methods

Class methods work the same way:

```python
from typing_graph import inspect_function

class Calculator:
    def __init__(self, precision: int = 2) -> None:
        self.precision = precision

    def add(self, a: float, b: float) -> float:
        return round(a + b, self.precision)

    @classmethod
    def create(cls, precision: int) -> "Calculator":
        return cls(precision)

# Inspect instance method
add_func = inspect_function(Calculator.add)
print(add_func.name)  # add
print(len(add_func.signature.parameters))  # 3 (self, a, b)

# Inspect class method
create_func = inspect_function(Calculator.create)
print(create_func.name)  # create
```

Note that `self` and `cls` parameters appear in the signature when inspecting unbound methods.

## Using inspect_signature directly

For callable objects where you only need the signature, use [`inspect_signature()`][typing_graph.inspect_signature]:

```python
from typing_graph import inspect_signature

sig = inspect_signature(calculate_total)
print(type(sig))  # <class 'typing_graph.SignatureNode'>
```

This also works with classes (inspecting `__init__`) and callable objects:

```python
class Greeter:
    def __call__(self, name: str) -> str:
        return f"Hello, {name}!"

greeter = Greeter()
sig = inspect_signature(greeter)
print(sig.parameters[0].name)  # name
```

## Next steps

- [Extracting metadata](../guides/extracting-metadata.md) - Process parameter metadata for validation
- [Configuration options](../guides/configuration.md) - Control forward reference handling
