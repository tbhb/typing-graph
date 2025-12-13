# How to configure type inspection

This guide shows you how to customize typing-graph's behavior using [`InspectConfig`][typing_graph.InspectConfig]. You'll learn to control forward reference resolution, limit recursion depth, manage metadata hoisting, enable source location tracking, and work with the inspection cache.

## Creating an InspectConfig

Pass an [`InspectConfig`][typing_graph.InspectConfig] instance to any inspection function:

```python
from typing_graph import inspect_type, InspectConfig

config = InspectConfig(
    max_depth=50,
    hoist_metadata=True,
)

node = inspect_type(list[int], config=config)
```

All configuration options have sensible defaults, so you only need to specify what you want to change.

## Controlling forward reference resolution

The `eval_mode` option controls how typing-graph handles forward references (string annotations or references to not-yet-defined types). See [`EvalMode`][typing_graph.EvalMode] for all available modes.

```python
from typing_graph import inspect_type, InspectConfig, EvalMode
```

### When you need all types fully resolved

Use `EvalMode.EAGER` to resolve all annotations immediately. If resolution fails, inspection raises an error:

```python
config = InspectConfig(eval_mode=EvalMode.EAGER)

# This works because int is defined
node = inspect_type(list[int], config=config)

# This would fail if "UndefinedType" doesn't exist
# node = inspect_type("UndefinedType", config=config)  # Error!
```

Choose eager mode when you want immediate feedback on resolution failures.

### When you want to tolerate unresolved references

Use `EvalMode.DEFERRED` (the default) to resolve what's possible and represent unresolvable references as [`ForwardRefNode`][typing_graph.ForwardRefNode] nodes:

```python
config = InspectConfig(eval_mode=EvalMode.DEFERRED)

# Forward references become ForwardRefNode nodes
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from mymodule import SomeType  # Not available at runtime

# Won't fail; creates a ForwardRefNode node
node = inspect_type("SomeType", config=config)
```

This mode works well for most use cases.

### When working with stringified annotations

Use `EvalMode.STRINGIFIED` to keep annotations as strings and resolve them lazily:

```python
config = InspectConfig(eval_mode=EvalMode.STRINGIFIED)
```

Choose this mode when working with code that uses `from __future__ import annotations` or when you want full control over resolution timing.

## Controlling automatic namespace detection

The `auto_namespace` option controls whether typing-graph automatically extracts namespaces from the objects you inspect. When enabled (the default), the library extracts module globals and adds class names for self-references.

```python
from typing_graph import InspectConfig

# Auto-detection enabled (default)
config = InspectConfig(auto_namespace=True)

# Auto-detection disabled - only explicit namespaces are used
config = InspectConfig(auto_namespace=False)
```

When `auto_namespace=False`, you must provide all namespace context explicitly through `globalns` and `localns`:

```python
# snippet - conceptual example
config = InspectConfig(
    auto_namespace=False,
    globalns={"MyType": MyType},
)
```

For detailed guidance on namespace configuration, see [How to configure namespaces](namespace-configuration.md).

## Limiting recursion depth

When you need to prevent issues with deeply nested or recursive types, use the `max_depth` option:

```python
# snippet - conceptual example
config = InspectConfig(max_depth=10)
node = inspect_type(deeply_nested_type, config=config)
```

This protects against:

- Recursive type definitions
- Deeply nested generics
- Complex type hierarchies

The default value (50) handles most real-world types.

## Managing metadata attachment

The `hoist_metadata` option controls whether metadata from `Annotated` wrappers gets attached to the base type node:

```python
from typing import Annotated

from typing_graph import InspectConfig, inspect_type

# With hoisting (default)
config = InspectConfig(hoist_metadata=True)
node = inspect_type(Annotated[int, "metadata"], config=config)
print(type(node).__name__)  # ConcreteNode
print(node.metadata)        # ('metadata',)

# Without hoisting - metadata is still accessible on the node
config = InspectConfig(hoist_metadata=False)
node = inspect_type(Annotated[int, "metadata"], config=config)
print(type(node).__name__)  # ConcreteNode
print(node.metadata)        # ('metadata',)
```

Hoisting (enabled by default) attaches metadata directly to the underlying type node for convenient access.

## Enabling source location tracking

When you need to track where types are defined (for error messages, IDE integration, or documentation), enable the `include_source_locations` option:

```python
from dataclasses import dataclass

from typing_graph import InspectConfig, inspect_dataclass


@dataclass
class Point:
    x: float
    y: float


config = InspectConfig(include_source_locations=True)
node = inspect_dataclass(Point, config=config)

if node.source:
    print(f"Defined in: {node.source.file}")
    print(f"Line: {node.source.lineno}")
```

This is useful for:

- Error messages that reference source locations
- IDE integrations
- Documentation generators

Source location tracking has a small performance cost, so it's off by default.

## Working with the inspection cache

typing-graph caches inspection results for performance. Use [`cache_info()`][typing_graph.cache_info] and [`cache_clear()`][typing_graph.cache_clear] to control this behavior.

### Viewing cache statistics

When you want to check cache effectiveness:

```python
from typing_graph import cache_info

info = cache_info()
print(f"Hits: {info.hits}")
print(f"Misses: {info.misses}")
print(f"Size: {info.currsize}")
print(f"Max size: {info.maxsize}")
```

### Clearing the cache

When you need fresh inspection results (after modifying class definitions, for performance testing, or to free memory):

```python
from typing_graph import cache_clear

# Clear all cached results
cache_clear()
```

### Understanding cache behavior

The cache uses the type object and configuration as keys. Different configurations produce different cache entries:

```python
from typing_graph import inspect_type, InspectConfig

# These create separate cache entries
node1 = inspect_type(list[int])
node2 = inspect_type(list[int], config=InspectConfig(max_depth=5))
```

## Common configuration patterns

### When validating types strictly

If you need fully resolved types with no forward references:

```python
strict_config = InspectConfig(
    eval_mode=EvalMode.EAGER,  # (1)!
    max_depth=100,
)
```

1. Fails immediately if any forward reference cannot be resolved.

### When optimizing for performance

If you're doing high-volume inspection and can tolerate forward references:

```python
fast_config = InspectConfig(
    eval_mode=EvalMode.DEFERRED,  # (1)!
    include_source_locations=False,  # (2)!
)
```

1. Creates `ForwardRefNode` for unresolvable references instead of failing.
2. Skips source location tracking to reduce overhead.

### When debugging type structures

If you're exploring types during development:

```python
debug_config = InspectConfig(
    include_source_locations=True,  # (1)!
    hoist_metadata=True,
)
```

1. Enables source file and line number tracking on nodes.

## Result

You can now configure type inspection with forward reference modes, depth limits, metadata hoisting, source location tracking, and cache management. Use these options to balance strict validation, performance, and debugging needs.

## See also

- [Your first type inspection](../tutorials/first-inspection.md) - Basic inspection usage
- [Forward references](../explanation/forward-references.md) - Deep dive into evaluation modes
- [Metadata hoisting](../reference/glossary.md#metadata-hoisting) - Glossary definition
- [API reference][typing_graph.InspectConfig] - Complete InspectConfig documentation
