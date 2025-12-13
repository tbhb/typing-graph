# Forward references

Forward references are a fundamental aspect of Python's type system that has driven significant design evolution. This page explains what they are, why they exist, how Python's approach has evolved, and how typing-graph handles forward reference evaluation across Python versions.

## Why forward references matter

Python evaluates type annotations at definition time by default. This creates a fundamental tension: type annotations often need to reference types that don't exist yet.

This tension has driven major design changes in Python's typing system, from [PEP 484](https://peps.python.org/pep-0484/)'s string annotations through [PEP 563](https://peps.python.org/pep-0563/)'s deferred evaluation to [PEP 649](https://peps.python.org/pep-0649/) and [PEP 749](https://peps.python.org/pep-0749/)'s lazy evaluation. typing-graph works correctly across all these approaches, abstracting away the version-specific complexity.

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

## The `from __future__ import annotations` approach

PEP 563 introduced a more sweeping solution to forward references: make *all* annotations strings by default. With the future import, Python stores every annotation as its literal string form without evaluating it:

```python
from __future__ import annotations

class Order:
    customer: Customer  # Stored as the string "Customer", not evaluated
    items: list[Item]   # Stored as "list[Item]"

class Customer:
    name: str
    orders: list[Order]  # No quotes needed - it's already a string internally
```

This eliminates the forward reference problem entirely. You never need to think about definition order or add quotes around type names. The annotations exist as strings until something explicitly evaluates them.

### Why this matters for runtime inspection

The trade-off is that runtime type inspection becomes more complex. When you access `Order.__annotations__`, you get strings instead of type objects. Any tool that wants to work with the actual types must resolve those strings, which requires access to the right namespace.

This is precisely where typing-graph's auto-namespace detection becomes valuable. When you call `inspect_dataclass(Order)`, typing-graph:

1. Detects that annotations are stringified
2. Extracts the module's global namespace from `Order.__module__`
3. Adds `Order` itself to the local namespace for self-references
4. Evaluates the string annotations in that namespace

The result is that PEP 563 code works without configuration:

```python
from __future__ import annotations
from dataclasses import dataclass
from typing_graph import inspect_dataclass

@dataclass
class Order:
    customer: Customer
    total: float

@dataclass
class Customer:
    name: str

# Auto-namespace detection handles the stringified annotations
node = inspect_dataclass(Order)
customer_field = node.fields[0]
print(customer_field.type)  # ConcreteNode for Customer
```

### The deprecation path

PEP 563's future import will continue working with its current behavior until Python 3.13 reaches end-of-life (expected October 2029). After that point, the import will be deprecated and eventually removed.

The reason for this phaseout is PEP 649 and PEP 749, which introduce a better solution in Python 3.14: lazy annotation evaluation. Rather than storing strings that must be explicitly resolved, Python 3.14 stores annotations as lazily evaluated code objects. They look and behave like regular type objects when accessed, but aren't evaluated until first use.

This approach gives you the best of both worlds: forward references work naturally (no definition order issues), and runtime inspection gets real type objects (no string evaluation needed).

### Recommendations

For new code targeting Python 3.14+, the future import is unnecessary. Lazy evaluation handles forward references automatically, and your annotations remain as actual type expressions rather than strings.

For code that must support Python 3.10-3.13, `from __future__ import annotations` remains a reasonable choice. typing-graph handles both approaches transparently through auto-namespace detection.

For codebases transitioning from older Python versions, consider whether the future import is worth keeping. If your tooling (ORMs, serialization libraries, validation frameworks) works correctly with stringified annotations, there's no urgency to remove it. The import will continue working for years.

!!! info "Historical context: the evolution of forward references"

    Python's approach to forward references has evolved significantly:

    - **PEP 484 (2014)**: Introduced string annotations as the solution
    - **PEP 563 (2017)**: Proposed making all annotations strings via `__future__` import
    - **PEP 649 (2021)**: Proposed lazy evaluation as an alternative, avoiding string-related issues
    - **PEP 749 (2024)**: Supplements PEP 649 with implementation details and the `annotationlib` module
    - **Python 3.14**: PEP 649/749 becomes the default behavior

    This evolution reflects the community's ongoing effort to balance three competing concerns: runtime introspectability, performance, and developer ergonomics. typing-graph is designed to work correctly regardless of which approach a codebase uses.

    Note that `from __future__ import annotations` (PEP 563) will continue to work with its current behavior at least until Python 3.13 reaches end-of-life. After that, it will be deprecated and eventually removed in favor of PEP 649/749's lazy evaluation.

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

| State           | Meaning                                                 |
|-----------------|---------------------------------------------------------|
| `RefUnresolved` | Resolution not yet attempted                            |
| `RefResolved`   | Successfully resolved; contains the resolved node       |
| `RefFailed`     | Resolution attempted but failed; contains error message |

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

## Why namespace context matters

Forward reference resolution requires access to the namespace where the type is defined. A string like `"Customer"` is meaningless without knowing which `Customer` class it refers to. This is why any runtime type inspection library must solve the namespace problem.

typing-graph addresses this through automatic namespace detection: when you inspect a class or function, the library extracts namespace context from the object itself. This design decision eliminates boilerplate for the common case while still allowing explicit control when needed.

For practical guidance on configuring namespaces, see [Namespace configuration](../guides/namespace-configuration.md).

## Automatic namespace detection

The key design insight behind typing-graph's namespace handling is that objects in Python carry namespace information with them. A class knows its defining module via `__module__`. A function carries its globals via `__globals__`. This information is enough to resolve most forward references without manual configuration.

### The design rationale

Manual namespace configuration works, but it creates friction for the common case. Consider how often you write code like this:

```python
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Order:
    customer: Customer  # Forward reference

@dataclass
class Customer:
    name: str
```

With PEP 563, both `Customer` in the `Order` class and `Order` in any self-referential patterns become strings. A runtime inspection library must resolve these strings, which requires access to the module's namespace.

typing-graph's approach: extract this namespace automatically from the object being inspected. When you call `inspect_dataclass(Order)`, the library:

1. Retrieves the module from `Order.__module__`
2. Gets the module's namespace from `sys.modules`
3. Adds `Order` itself to enable self-references
4. Includes any PEP 695 type parameters from `__type_params__`

This happens transparently. The common case requires zero configuration.

### Design trade-offs

Automatic detection introduces complexity:

**Caching considerations.** When namespaces are auto-detected, the cache key must account for the source object. typing-graph handles this by bypassing the cache when namespace context varies, ensuring correctness at the cost of some repeated work.

**Precedence rules.** When users provide explicit namespaces alongside auto-detection, the library must define clear precedence. typing-graph chose user-provided values taking precedence, allowing targeted overrides without turning off auto-detection entirely.

**Limitations.** Auto-detection can only extract what Python makes available at runtime. `TYPE_CHECKING` imports, cross-module references without actual imports, and dynamically created types all fall outside what auto-detection can resolve.

These trade-offs reflect a deliberate design choice: optimize for the common case (PEP 563 code with standard module structure) while providing escape hatches for edge cases.

For practical guidance on configuring namespaces in various scenarios, see [Namespace configuration](../guides/namespace-configuration.md).

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

| Version   | API                                                            |
|-----------|----------------------------------------------------------------|
| 3.14+     | `typing.evaluate_forward_ref()`                                |
| 3.13      | `ForwardRefNode._evaluate()` with `type_params`                |
| 3.12      | `ForwardRefNode._evaluate()` with `recursive_guard` keyword    |
| 3.10-3.11 | `ForwardRefNode._evaluate()` with positional `recursive_guard` |

typing-graph handles these differences internally, providing a consistent API regardless of Python version.

??? abstract "Why Python's forward reference API keeps changing"

    The instability of Python's forward reference API reflects genuine complexity in the problem space. Each version has attempted to address limitations discovered in practice:

    - **3.10-3.11**: Basic evaluation with manual cycle detection via `recursive_guard`
    - **3.12**: Keyword-only `recursive_guard` for clearer API
    - **3.13**: Added `type_params` to support PEP 695 scoped type parameters
    - **3.14**: New `evaluate_forward_ref()` function designed for PEP 649's lazy evaluation

    This evolution shows Python's type system maturing from an optional annotation layer into a core language feature. Libraries like typing-graph absorb this complexity so your code doesn't have to.

## Working with forward references

Understanding forward references conceptually shapes how you approach them in practice:

**Default to auto-detection.** typing-graph's design assumes auto-namespace detection handles most cases. The common pattern (PEP 563 code with standard module structure) requires zero configuration. Only reach for explicit namespaces when auto-detection falls short.

**Embrace deferred evaluation.** The default `DEFERRED` mode reflects a pragmatic stance: resolve what you can, preserve what you can't. This approach suits most tools better than failing fast on unresolvable references.

**Think about resolution state.** Forward references aren't binary (resolved vs unresolved). They exist in three states: unresolved (not yet attempted), resolved (successfully evaluated), and failed (attempted but couldn't resolve). Code that handles forward references should account for all three.

**Let traversal handle cycles.** Self-referential types create cycles in the type graph. Rather than implementing cycle detection yourself, use [`walk()`][typing_graph.walk], which handles cycles automatically.

For step-by-step guidance on namespace configuration, see [Namespace configuration](../guides/namespace-configuration.md). For traversal patterns, see [Walking the type graph](../guides/walking-type-graph.md).

## The broader context

Forward references connect to larger themes in Python's evolution. The tension between runtime evaluation and static analysis has shaped much of the typing module's design. PEP 649's lazy evaluation in Python 3.14 represents a potential resolution to this tension: annotations will be available at runtime without the performance cost of eager evaluation or the complexity of string-based deferred evaluation.

For library authors, this evolution means designing APIs that work regardless of how annotations are evaluated. typing-graph's `EvalMode` abstraction provides this flexibility: the same inspection code works whether annotations come from string evaluation, lazy evaluation, or direct expression evaluation.

## Applying this understanding

The conceptual foundation covered here informs practical decisions:

- When choosing an evaluation mode, consider whether your use case needs immediate validation (eager), graceful degradation (deferred), or string preservation (stringified)
- When encountering resolution failures, trace back to namespace context: is the type available at runtime? Is it in scope?
- When designing APIs that consume type graphs, account for the three-state nature of forward references rather than assuming resolution always succeeds

## See also

- [Namespace configuration](../guides/namespace-configuration.md) - How-to guide for namespace scenarios
- [Configuration options](../guides/configuration.md) - Full details on `EvalMode` and namespaces
- [`InspectConfig`][typing_graph.InspectConfig] - Configuration class with `auto_namespace` field
- [`inspect_type()`][typing_graph.inspect_type] - Type inspection with `source` parameter
- [`walk()`][typing_graph.walk] - Cycle-safe graph traversal
- [Architecture overview](architecture.md) - How forward references fit into the inspection process
- [Forward reference](../reference/glossary.md#forward-reference) - Glossary definition
- [EvalMode](../reference/glossary.md#eval-mode) - Glossary definition
- [PEP 563](https://peps.python.org/pep-0563/) - Postponed evaluation of annotations
- [PEP 649](https://peps.python.org/pep-0649/) - Deferred evaluation of annotations using descriptors
- [PEP 749](https://peps.python.org/pep-0749/) - Implementing PEP 649
