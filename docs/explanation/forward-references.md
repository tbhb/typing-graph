# Forward references

Forward references are a notable aspect of Python's type system. This page explains what they are, why they exist, and how typing-graph handles forward reference evaluation across Python versions.

## Why forward references matter

Python evaluates type annotations at definition time by default. This creates a practical problem: type annotations often need to reference types that don't exist yet.

This problem has driven design changes in Python's typing system, from PEP 484's string annotations through PEP 563's deferred evaluation to PEP 649's lazy evaluation. typing-graph works correctly across all these approaches.

## Quick start: common self-referential pattern

If you just need to handle a common self-referential type like a tree node:

```python
from dataclasses import dataclass
from typing_graph import inspect_dataclass, InspectConfig

@dataclass
class TreeNode:
    value: int
    children: list["TreeNode"]

# Provide the namespace containing the class
config = InspectConfig(globalns={"TreeNode": TreeNode})
node = inspect_dataclass(TreeNode, config=config)

# Forward references are now resolved
children_field = node.fields[1]
print(children_field.type)  # SubscriptedGenericNode for list[TreeNode]
```

For more complex scenarios involving multiple modules or deferred evaluation modes, read on.

## What are forward references?

In Python, the interpreter evaluates type annotations at definition time by default. This creates a problem when you need to reference a class before defining it:

```python
class Node:
    # Error! Parent isn't defined yet
    parent: Parent

class Parent:
    children: list[Node]
```

Python solves this with **forward references**, which are string annotations that defer evaluation:

```python
class Node:
    parent: "Parent"  # String annotation - evaluated later

class Parent:
    children: list[Node]
```

Forward references also appear when using `from __future__ import annotations` (PEP 563), which makes all annotations strings by default.

!!! info "Historical context: the evolution of forward references"

    Python's approach to forward references has evolved significantly:

    - **PEP 484 (2014)**: Introduced string annotations as the solution
    - **PEP 563 (2017)**: Proposed making all annotations strings via `__future__` import
    - **PEP 649 (2021)**: Proposed lazy evaluation as an alternative, avoiding string-related issues
    - **Python 3.14**: PEP 649 becomes the default behavior

    This evolution reflects the community's ongoing effort to balance three competing concerns: runtime introspectability, performance, and developer ergonomics. typing-graph is designed to work correctly regardless of which approach a codebase uses.

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

[`EvalMode.DEFERRED`][typing_graph.EvalMode] resolves what it can and creates [`ForwardRefNode`][typing_graph.ForwardRefNode] nodes for anything unresolvable.

```python
from typing_graph import inspect_type, ForwardRefNode

# Resolves to ConcreteNode because int exists
node = inspect_type("int")
print(type(node))  # ConcreteNode

# Creates ForwardRefNode because UndefinedClass doesn't exist
node = inspect_type("UndefinedClass")
print(type(node))  # ForwardRefNode
print(node.ref)    # "UndefinedClass"
```

Use deferred mode when:

- Some types might not be available at inspection time
- You want graceful handling of unresolvable references
- You're building tools that analyze incomplete code

### `STRINGIFIED` mode

`EvalMode.STRINGIFIED` keeps all string annotations as unresolved `ForwardRefNode` nodes without attempting resolution.

```python
from typing_graph import inspect_type, InspectConfig, EvalMode, ForwardRefNode

config = InspectConfig(eval_mode=EvalMode.STRINGIFIED)

# Even "int" becomes an unresolved ForwardRefNode
node = inspect_type("int", config=config)
print(type(node))  # ForwardRefNode
print(node.ref)    # "int"
```

Use stringified mode when:

- You want to preserve the original string form
- Resolution should happen at a different time
- You're analyzing code with `from __future__ import annotations`

!!! note "Design trade-off: three modes vs automatic detection"

    You might wonder why typing-graph requires explicit mode selection rather than automatically detecting the best approach. The reason is that the "right" choice depends on your use case, not just the input:

    - **Eager mode** is right when you need immediate validation and can guarantee all types exist
    - **Deferred mode** balances convenience and robustness, making it the right default for most tools
    - **Stringified mode** is essential when you need to preserve the exact annotation form

    Automatic detection would need to guess your intent, which inevitably leads to surprising behavior in edge cases. Explicit modes make the behavior predictable and testable.

## The forward ref node

When a forward reference can't be immediately resolved, typing-graph creates a [`ForwardRefNode`][typing_graph.ForwardRefNode] node:

```python
# snippet - simplified internal implementation
@dataclass(slots=True, frozen=True)
class ForwardRefNode(TypeNode):
    ref: str  # The string reference
    state: RefUnresolved | RefResolved | RefFailed
```

### Resolution states

The `state` attribute tracks the resolution status:

| State | Meaning |
| ----- | ------- |
| `RefUnresolved` | Resolution not yet attempted |
| `RefResolved` | Successfully resolved; contains the resolved node |
| `RefFailed` | Resolution attempted but failed; contains error message |

```python
from typing_graph import inspect_type, ForwardRefNode, RefResolved, RefFailed

# Successfully resolved
node = inspect_type("int")
if isinstance(node, ForwardRefNode) and isinstance(node.state, RefResolved):
    print(node.state.node)  # The resolved ConcreteNode

# Failed resolution (in deferred mode)
node = inspect_type("NonexistentType")
if isinstance(node, ForwardRefNode) and isinstance(node.state, RefFailed):
    print(node.state.error)  # The error message
```

### Traversing resolved references

When a `ForwardRefNode` resolves successfully, its `children()` method returns the resolved node:

```python
node = inspect_type("int")  # Returns ForwardRefNode with resolved state
children = list(node.children())
# children[0] is the ConcreteNode for int
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
# Successfully resolves to ConcreteNode for MyClass
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

typing-graph detects cycles during resolution to prevent infinite recursion. When the library detects a cycle, it returns an unresolved `ForwardRefNode` to break the cycle:

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
| 3.13 | `ForwardRefNode._evaluate()` with `type_params` |
| 3.12 | `ForwardRefNode._evaluate()` with `recursive_guard` keyword |
| 3.10-3.11 | `ForwardRefNode._evaluate()` with positional `recursive_guard` |

typing-graph handles these differences internally, providing a consistent API regardless of Python version.

??? abstract "Why Python's forward reference API keeps changing"

    The instability of Python's forward reference API reflects genuine complexity in the problem space. Each version has attempted to address limitations discovered in practice:

    - **3.10-3.11**: Basic evaluation with manual cycle detection via `recursive_guard`
    - **3.12**: Keyword-only `recursive_guard` for clearer API
    - **3.13**: Added `type_params` to support PEP 695 scoped type parameters
    - **3.14**: New `evaluate_forward_ref()` function designed for PEP 649's lazy evaluation

    This evolution shows Python's type system maturing from an optional annotation layer into a core language feature. Libraries like typing-graph absorb this complexity so your code doesn't have to.

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
from typing_graph import ForwardRefNode, RefResolved, RefFailed

def process_type(node):
    if isinstance(node, ForwardRefNode):
        if isinstance(node.state, RefResolved):
            # Use node.state.node
            return process_type(node.state.node)
        elif isinstance(node.state, RefFailed):
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

## The broader context

Forward references connect to larger themes in Python's evolution. The tension between runtime evaluation and static analysis has shaped much of the typing module's design. PEP 649's lazy evaluation in Python 3.14 represents a potential resolution to this tension: annotations will be available at runtime without the performance cost of eager evaluation or the complexity of string-based deferred evaluation.

For library authors, this evolution means designing APIs that work regardless of how annotations are evaluated. typing-graph's `EvalMode` abstraction provides this flexibility: the same inspection code works whether annotations come from string evaluation, lazy evaluation, or direct expression evaluation.

## Practical application

Now that you understand forward references, apply this knowledge:

- **Configure evaluation modes** with [Configuration options](../guides/configuration.md)
- **Handle forward refs during traversal** with [Walking the type graph](../guides/walking-type-graph.md)
- **Inspect functions with forward refs** in [Inspecting functions](../tutorials/functions.md)

## See also

- [Configuration options](../guides/configuration.md) - Full details on `EvalMode` and namespaces
- [Architecture overview](architecture.md) - How forward references fit into the inspection process
- [Forward reference](../reference/glossary.md#forward-reference) - Glossary definition
- [EvalMode](../reference/glossary.md#eval-mode) - Glossary definition
- [PEP 563](https://peps.python.org/pep-0563/) - Postponed evaluation of annotations
- [PEP 649](https://peps.python.org/pep-0649/) - Deferred evaluation of annotations using descriptors
