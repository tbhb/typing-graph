# Inspecting functions

In this tutorial, you'll inspect function signatures to extract parameter and return type information. By the end, you'll be able to analyze any callable and access its parameters with their metadata.

??? info "Prerequisites"
    Before starting, ensure you have:

    - Completed the [Your first type inspection](first-inspection.md) tutorial
    - Basic familiarity with Python function signatures

    You don't need prior experience with the `inspect` module.

## Step 1: Create the script file

Create a new file called `function_inspection.py`:

```python title="function_inspection.py"
from typing import Annotated

print("Ready to inspect functions")
```

Run the script:

```bash title="Terminal"
python function_inspection.py
```

You should see:

```text title="Output"
Ready to inspect functions
```

## Step 2: Define a typed function

Create a function with type annotations:

```python title="function_inspection.py"
from dataclasses import dataclass
from typing import Annotated


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


print(f"Function defined: {calculate_total.__name__}")
```

Run the script:

```bash title="Terminal"
python function_inspection.py
```

You should see:

```text title="Output"
Function defined: calculate_total
```

## Step 3: Inspect the function

Use [`inspect_function()`][typing_graph.inspect_function] to analyze the function:

```python title="function_inspection.py"
from dataclasses import dataclass
from typing import Annotated

from typing_graph import inspect_function


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


func = inspect_function(calculate_total)
print(f"Node type: {type(func).__name__}")
print(f"Function name: {func.name}")
```

Run the script:

```bash title="Terminal"
python function_inspection.py
```

You should see:

```text title="Output"
Node type: FunctionNode
Function name: calculate_total
```

## Step 4: Access the signature

The [`FunctionNode`][typing_graph.FunctionNode] provides access to the function's signature:

```python title="function_inspection.py"
from dataclasses import dataclass
from typing import Annotated

from typing_graph import inspect_function


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


func = inspect_function(calculate_total)
sig = func.signature

print(f"Signature node type: {type(sig).__name__}")
print(f"Number of parameters: {len(sig.parameters)}")
```

Run the script:

```bash title="Terminal"
python function_inspection.py
```

You should see:

```text title="Output"
Signature node type: SignatureNode
Number of parameters: 3
```

!!! success "Checkpoint"
    At this point, you have:

    - Defined a typed function with annotations
    - Inspected it using `inspect_function()`
    - Accessed the signature via `func.signature`

## Step 5: Iterate over parameters

The [`SignatureNode`][typing_graph.SignatureNode]'s `parameters` attribute returns a tuple of [`Parameter`][typing_graph.Parameter] objects:

```python title="function_inspection.py"
from dataclasses import dataclass
from typing import Annotated

from typing_graph import inspect_function


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


func = inspect_function(calculate_total)

for param in func.signature.parameters:
    print(f"Parameter: {param.name}")
    print(f"  Kind: {param.kind}")
    print(f"  Has default: {param.default is not None}")
    print()
```

Run the script:

```bash title="Terminal"
python function_inspection.py
```

You should see:

```text title="Output"
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

## Step 6: Check parameter kinds and defaults

??? info "Parameter kinds reference"
    The `kind` attribute indicates how the parameter can be passed:

    | Kind | Syntax | Example |
    |------|--------|---------|
    | `POSITIONAL_ONLY` | `param, /` | `def f(x, /): ...` |
    | `POSITIONAL_OR_KEYWORD` | `param` | `def f(x): ...` |
    | `VAR_POSITIONAL` | `*args` | `def f(*args): ...` |
    | `KEYWORD_ONLY` | `*, param` | `def f(*, x): ...` |
    | `VAR_KEYWORD` | `**kwargs` | `def f(**kwargs): ...` |

Access the default value when present:

```python title="function_inspection.py"
from dataclasses import dataclass
from typing import Annotated

from typing_graph import inspect_function


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


func = inspect_function(calculate_total)

for param in func.signature.parameters:
    if param.default is not None:
        print(f"{param.name} has default: {param.default}")
```

Run the script:

```bash title="Terminal"
python function_inspection.py
```

You should see:

```text title="Output"
discount has default: 0.0
```

## Step 7: Access parameter type nodes

Each parameter has a `type` attribute containing the inspected type node:

```python title="function_inspection.py"
from dataclasses import dataclass
from typing import Annotated

from typing_graph import inspect_function


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


func = inspect_function(calculate_total)

for param in func.signature.parameters:
    type_node = param.type
    print(f"{param.name}: {type(type_node).__name__}")
    if type_node.metadata:
        print(f"  Metadata: {list(type_node.metadata)}")
```

Run the script:

```bash title="Terminal"
python function_inspection.py
```

You should see:

```text title="Output"
items: SubscriptedGenericNode
tax_rate: ConcreteNode
  Metadata: [Positive()]
discount: ConcreteNode
```

!!! success "Checkpoint"
    At this point, you have:

    - Iterated over function parameters
    - Accessed parameter kinds and defaults
    - Retrieved type nodes with metadata from parameters

## Step 8: Access the return type

The signature's `returns` attribute contains the return type node:

```python title="function_inspection.py"
from dataclasses import dataclass
from typing import Annotated

from typing_graph import inspect_function


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


func = inspect_function(calculate_total)
return_type = func.signature.returns

print(f"Return type node: {type(return_type).__name__}")
print(f"Return class: {return_type.cls}")
```

Run the script:

```bash title="Terminal"
python function_inspection.py
```

You should see:

```text title="Output"
Return type node: ConcreteNode
Return class: <class 'float'>
```

!!! success "Checkpoint"
    At this point, you have:

    - Accessed the return type from the signature
    - Retrieved the underlying class from the type node

## Step 9: Inspect a function with complex return type

Functions can return complex types:

```python title="function_inspection.py"
from typing_graph import inspect_function


def get_users() -> list[dict[str, str]]:
    return []


func = inspect_function(get_users)
return_node = func.signature.returns

print(f"Return type: {type(return_node).__name__}")
print(f"Origin: {return_node.origin.cls}")

element_type = return_node.args[0]
print(f"Element type: {type(element_type).__name__}")
print(f"Element origin: {element_type.origin.cls}")
```

Run the script:

```bash title="Terminal"
python function_inspection.py
```

You should see:

```text title="Output"
Return type: SubscriptedGenericNode
Origin: <class 'list'>
Element type: SubscriptedGenericNode
Element origin: <class 'dict'>
```

## Step 10: Define a class with methods

Create a class to show method inspection:

```python title="function_inspection.py"
class Calculator:
    def __init__(self, precision: int = 2) -> None:
        self.precision = precision

    def add(self, a: float, b: float) -> float:
        return round(a + b, self.precision)

    @classmethod
    def create(cls, precision: int) -> "Calculator":
        return cls(precision)


print(f"Calculator class defined with {len(Calculator.__dict__)} attributes")
```

Run the script:

```bash title="Terminal"
python function_inspection.py
```

You should see:

```text title="Output"
Calculator class defined with 6 attributes
```

## Step 11: Inspect instance and class methods

Methods work the same way as functions:

```python title="function_inspection.py"
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
print(f"Method: {add_func.name}")
print(f"Parameters: {len(add_func.signature.parameters)}")  # Includes 'self'

# Inspect class method
create_func = inspect_function(Calculator.create)
print(f"\nClass method: {create_func.name}")
print(f"Parameters: {len(create_func.signature.parameters)}")  # Includes 'cls'
```

Run the script:

```bash title="Terminal"
python function_inspection.py
```

You should see:

```text title="Output"
Method: add
Parameters: 3

Class method: create
Parameters: 2
```

Note that `self` and `cls` parameters appear in the signature when inspecting unbound methods.

## Step 12: Use inspect_signature() directly

For callable objects where you only need the signature, use [`inspect_signature()`][typing_graph.inspect_signature]:

```python title="function_inspection.py"
from dataclasses import dataclass
from typing import Annotated

from typing_graph import inspect_signature


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


sig = inspect_signature(calculate_total)
print(f"Signature type: {type(sig).__name__}")
print(f"Parameters: {[p.name for p in sig.parameters]}")
```

Run the script:

```bash title="Terminal"
python function_inspection.py
```

You should see:

```text title="Output"
Signature type: SignatureNode
Parameters: ['items', 'tax_rate', 'discount']
```

## Step 13: Inspect a callable object

The `inspect_signature()` function also works with callable objects by inspecting their `__call__` method:

```python title="function_inspection.py"
from typing_graph import inspect_signature


class Greeter:
    def __call__(self, name: str) -> str:
        return f"Hello, {name}!"


# Inspect the __call__ method directly for the signature
sig = inspect_signature(Greeter.__call__)

print(f"Parameters: {[p.name for p in sig.parameters]}")
print(f"Return type: {sig.returns.cls}")
```

Run the script:

```bash title="Terminal"
python function_inspection.py
```

You should see:

```text title="Output"
Parameters: ['self', 'name']
Return type: <class 'str'>
```

!!! success "Checkpoint"
    You've completed this tutorial. You can now:

    - Inspect functions with `inspect_function()`
    - Access parameters with their kinds, defaults, and types
    - Retrieve return type information
    - Inspect methods and callable objects
    - Use `inspect_signature()` for direct signature access

## Summary

You've learned how to inspect function signatures and extract parameter information. The key functions are:

- [`inspect_function()`][typing_graph.inspect_function] returns a `FunctionNode` with name and signature
- [`inspect_signature()`][typing_graph.inspect_signature] returns a `SignatureNode` directly
- `signature.parameters` contains `Parameter` objects with name, kind, type, and default
- `signature.returns` contains the return type node

!!! tip "Next steps"
    Now that you can inspect functions, explore:

    - [Metadata queries](../guides/metadata-queries.md) - Process parameter metadata for validation
    - [Configuration options](../guides/configuration.md) - Control forward reference handling
    - [Walking the type graph](../guides/walking-type-graph.md) - Traverse complex parameter types

    For understanding how forward references affect function inspection, see [Forward references](../explanation/forward-references.md).
