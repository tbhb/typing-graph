# Configuration options

This guide explains the [`InspectConfig`][typing_graph.InspectConfig] options and how to customize typing-graph's behavior.

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

## Forward reference evaluation modes

The `eval_mode` option controls how typing-graph handles forward references (string annotations or references to not-yet-defined types). See [`EvalMode`][typing_graph.EvalMode] for all available modes.

```python
from typing_graph import inspect_type, InspectConfig, EvalMode
```

### Eager mode

`EvalMode.EAGER` fully resolves all annotations immediately. If resolution fails, inspection raises an error.

```python
config = InspectConfig(eval_mode=EvalMode.EAGER)

# This works because int is defined
node = inspect_type(list[int], config=config)

# This would fail if "UndefinedType" doesn't exist
# node = inspect_type("UndefinedType", config=config)  # Error!
```

Use eager mode when you need all types fully resolved and want immediate feedback on resolution failures.

### Deferred mode (default)

`EvalMode.DEFERRED` resolves what it can and represents unresolvable references as [`ForwardRef`][typing_graph.ForwardRef] nodes.

```python
config = InspectConfig(eval_mode=EvalMode.DEFERRED)

# Forward references become ForwardRef nodes
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from mymodule import SomeType  # Not available at runtime

# Won't fail; creates a ForwardRef node
node = inspect_type("SomeType", config=config)
```

This is the default mode and works well for most use cases.

### `STRINGIFIED` mode

`EvalMode.STRINGIFIED` keeps annotations as strings and resolves them lazily.

```python
config = InspectConfig(eval_mode=EvalMode.STRINGIFIED)
```

Use this when working with code that uses `from __future__ import annotations` or when you want full control over resolution timing.

## Depth limiting

The `max_depth` option limits how deeply typing-graph recurses into nested types:

```python
# snippet - conceptual example
config = InspectConfig(max_depth=10)
node = inspect_type(deeply_nested_type, config=config)
```

This prevents issues with:

- Recursive type definitions
- Deeply nested generics
- Complex type hierarchies

The default value (50) handles most real-world types.

## Metadata hoisting

The `hoist_metadata` option controls whether metadata from `Annotated` wrappers gets attached to the base type node:

```python
from typing import Annotated

from typing_graph import InspectConfig, inspect_type

# With hoisting (default)
config = InspectConfig(hoist_metadata=True)
node = inspect_type(Annotated[int, "metadata"], config=config)
print(type(node).__name__)  # ConcreteType
print(node.metadata)        # ('metadata',)

# Without hoisting - metadata is still accessible on the node
config = InspectConfig(hoist_metadata=False)
node = inspect_type(Annotated[int, "metadata"], config=config)
print(type(node).__name__)  # ConcreteType
print(node.metadata)        # ('metadata',)
```

Hoisting (enabled by default) attaches metadata directly to the underlying type node for convenient access.

## Source locations

The `include_source_locations` option adds source file information to nodes:

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

## Cache management

typing-graph caches inspection results for performance. Use [`cache_info()`][typing_graph.cache_info] and [`cache_clear()`][typing_graph.cache_clear] to control this behavior.

### Viewing cache statistics

```python
from typing_graph import cache_info

info = cache_info()
print(f"Hits: {info.hits}")
print(f"Misses: {info.misses}")
print(f"Size: {info.currsize}")
print(f"Max size: {info.maxsize}")
```

### Clearing the cache

```python
from typing_graph import cache_clear

# Clear all cached results
cache_clear()
```

Clear the cache when:

- You've modified class definitions and need fresh inspection results
- You want to measure inspection performance without cache effects
- You're done with a batch of inspections and want to free memory

### Cache behavior

The cache uses the type object and configuration as keys. Different configurations produce different cache entries:

```python
from typing_graph import inspect_type, InspectConfig

# These create separate cache entries
node1 = inspect_type(list[int])
node2 = inspect_type(list[int], config=InspectConfig(max_depth=5))
```

## Configuration patterns

### Strict validation context

For contexts where you need fully resolved types:

```python
strict_config = InspectConfig(
    eval_mode=EvalMode.EAGER,
    max_depth=100,
)
```

### Performance-sensitive context

For high-volume inspection where you can tolerate forward references:

```python
fast_config = InspectConfig(
    eval_mode=EvalMode.DEFERRED,
    include_source_locations=False,
)
```

### Debugging context

For understanding type structures during development:

```python
debug_config = InspectConfig(
    include_source_locations=True,
    hoist_metadata=True,
)
```

## See also

- [Your first type inspection](../tutorials/first-inspection.md) - Basic inspection usage
- [API reference][typing_graph.InspectConfig] - Complete InspectConfig documentation
