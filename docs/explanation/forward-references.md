# Forward references

This page explains how typing-graph handles forward references—type annotations that reference classes not yet defined at the point of annotation.

## What are forward references?

In Python, the interpreter evaluates type annotations at definition time by default. This creates a problem when you need to reference a class before defining it:

```python
class Node:
    # Error! Parent isn't defined yet
    parent: Parent

class Parent:
    children: list[Node]
```

Python solves this with **forward references**—string annotations that defer evaluation:

```python
class Node:
    parent: "Parent"  # String annotation - evaluated later

class Parent:
    children: list[Node]
```

Forward references also appear when using `from __future__ import annotations` (PEP 563), which makes all annotations strings by default.

## How typing-graph handles forward references

When typing-graph encounters a forward reference, it can handle it in three ways, controlled by [`EvalMode`][typing_graph.EvalMode]:

### Eager mode

`EvalMode.EAGER` attempts to resolve all forward references immediately. If resolution fails, inspection raises a `NameError`.

```python
from typing_graph import inspect_type, InspectConfig, EvalMode

config = InspectConfig(eval_mode=EvalMode.EAGER)

# This fails because "UndefinedClass" can't be resolved
inspect_type("UndefinedClass", config=config)  # Raises NameError
```

Use eager mode when:

- All types should be fully defined at inspection time
- You want immediate feedback on resolution failures
- You're inspecting types in a controlled environment

### Deferred mode (default)

[`EvalMode.DEFERRED`][typing_graph.EvalMode] resolves what it can and creates [`ForwardRef`][typing_graph.ForwardRef] nodes for anything unresolvable.

```python
from typing_graph import inspect_type, ForwardRef

# Resolves to ConcreteType because int exists
node = inspect_type("int")
print(type(node))  # ConcreteType

# Creates ForwardRef because UndefinedClass doesn't exist
node = inspect_type("UndefinedClass")
print(type(node))  # ForwardRef
print(node.ref)    # "UndefinedClass"
```

Use deferred mode when:

- Some types might not be available at inspection time
- You want graceful handling of unresolvable references
- You're building tools that analyze incomplete code

### `STRINGIFIED` mode

`EvalMode.STRINGIFIED` keeps all string annotations as unresolved `ForwardRef` nodes without attempting resolution.

```python
from typing_graph import inspect_type, InspectConfig, EvalMode, ForwardRef

config = InspectConfig(eval_mode=EvalMode.STRINGIFIED)

# Even "int" becomes an unresolved ForwardRef
node = inspect_type("int", config=config)
print(type(node))  # ForwardRef
print(node.ref)    # "int"
```

Use stringified mode when:

- You want to preserve the original string form
- Resolution should happen at a different time
- You're analyzing code with `from __future__ import annotations`

## The forward ref node

When a forward reference can't be immediately resolved, typing-graph creates a [`ForwardRef`][typing_graph.ForwardRef] node:

```python
# snippet - simplified internal implementation
@dataclass(slots=True, frozen=True)
class ForwardRef(TypeNode):
    ref: str  # The string reference
    state: RefState.Unresolved | RefState.Resolved | RefState.Failed
```

### Resolution states

The `state` attribute tracks the resolution status:

| State | Meaning |
| ----- | ------- |
| `RefState.Unresolved` | Resolution not yet attempted |
| `RefState.Resolved` | Successfully resolved; contains the resolved node |
| `RefState.Failed` | Resolution attempted but failed; contains error message |

```python
from typing_graph import inspect_type, ForwardRef, RefState

# Successfully resolved
node = inspect_type("int")
if isinstance(node, ForwardRef) and isinstance(node.state, RefState.Resolved):
    print(node.state.node)  # The resolved ConcreteType

# Failed resolution (in deferred mode)
node = inspect_type("NonexistentType")
if isinstance(node, ForwardRef) and isinstance(node.state, RefState.Failed):
    print(node.state.error)  # The error message
```

### Traversing resolved references

When a `ForwardRef` resolves successfully, its `children()` method returns the resolved node:

```python
node = inspect_type("int")  # Returns ForwardRef with resolved state
children = list(node.children())
# children[0] is the ConcreteType for int
```

Unresolved or failed references return no children.

## Providing namespaces for resolution

Forward reference resolution requires access to the namespace where the code defines the type. Use `globalns` and `localns` in [`InspectConfig`][typing_graph.InspectConfig]:

```python
from typing_graph import inspect_type, InspectConfig

class MyClass:
    pass

# Provide the namespace containing MyClass
config = InspectConfig(
    globalns={"MyClass": MyClass},
)

node = inspect_type("MyClass", config=config)
# Successfully resolves to ConcreteType for MyClass
```

For module-level types, you can pass the module's `__dict__`:

```python
# snippet - example with hypothetical mymodule
import mymodule

config = InspectConfig(globalns=vars(mymodule))
```

## Cycle detection

Forward references can create cycles in type definitions:

```python
class Node:
    children: list["Node"]  # Self-reference
```

typing-graph detects cycles during resolution to prevent infinite recursion. When the library detects a cycle, it returns an unresolved `ForwardRef` to break the cycle:

```python
from typing_graph import inspect_type, InspectConfig

class Node:
    children: list["Node"]

config = InspectConfig(globalns={"Node": Node})
node = inspect_type(Node, config=config)

# The type graph handles the self-reference gracefully
```

The `InspectContext` tracks which references the library currently resolves via its `resolving` set. If the library encounters a reference while already resolving it, the library detects a cycle.

## Python version differences

Forward reference evaluation has changed across Python versions:

| Version | API |
| ------- | --- |
| 3.14+ | `typing.evaluate_forward_ref()` |
| 3.13 | `ForwardRef._evaluate()` with `type_params` |
| 3.12 | `ForwardRef._evaluate()` with `recursive_guard` keyword |
| 3.10-3.11 | `ForwardRef._evaluate()` with positional `recursive_guard` |

typing-graph handles these differences internally, providing a consistent API regardless of Python version.

## Best practices

### Use deferred mode for flexibility

The default `DEFERRED` mode handles most scenarios gracefully. It resolves what it can while preserving information about unresolvable references.

### Provide complete namespaces

When resolution matters, provide comprehensive namespaces:

```python
# snippet - example with hypothetical mymodule
import typing
import mymodule

config = InspectConfig(
    globalns={
        **vars(typing),
        **vars(mymodule),
    }
)
```

### Check resolution state before use

When working with potentially unresolved references, check the state:

```python
from typing_graph import ForwardRef, RefState

def process_type(node):
    if isinstance(node, ForwardRef):
        if isinstance(node.state, RefState.Resolved):
            # Use node.state.node
            return process_type(node.state.node)
        elif isinstance(node.state, RefState.Failed):
            # Handle failure
            print(f"Could not resolve: {node.state.error}")
            return None
        else:
            # Unresolved - defer processing
            return None
    # Process other node types...
```

### Handle cycles in traversal

When traversing type graphs that may contain forward references, prepare for cycles:

```python
def traverse(node, visited=None):
    if visited is None:
        visited = set()

    node_id = id(node)
    if node_id in visited:
        return  # Cycle detected

    visited.add(node_id)

    # Process node...

    for child in node.children():
        traverse(child, visited)
```

## See also

- [Configuration options](../guides/configuration.md) - Full details on `EvalMode` and namespaces
- [Architecture overview](architecture.md) - How forward references fit into the inspection process
- [Glossary: Forward reference](../reference/glossary.md#forward-reference) - Quick definition
