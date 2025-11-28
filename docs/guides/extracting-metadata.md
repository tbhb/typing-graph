# Extracting metadata

!!! note "Upcoming API improvements"

    A dedicated **metadata querying API** is coming soon with predicate-based filtering, type-safe extraction, and scoped queries. The patterns shown here use the current stable API. See the [roadmap](../roadmap.md#metadata-querying-apis) for details on planned features.

This guide shows how to access and filter metadata attached to types via `Annotated` wrappers.

## Understanding metadata hoisting

When you use `Annotated[T, meta1, meta2]`, the metadata (`meta1`, `meta2`) gets attached to type `T`. By default, typing-graph "hoists" this metadata from the `Annotated` wrapper to the resulting [`TypeNode`][typing_graph.TypeNode].

```python
from typing import Annotated
from dataclasses import dataclass
from typing_graph import inspect_type, ConcreteType

@dataclass(frozen=True)
class MaxLen:
    value: int

# The Annotated wrapper
Username = Annotated[str, MaxLen(50)]

# Inspect it
node = inspect_type(Username)

# You get a ConcreteType (for str), not an AnnotatedType
print(type(node))  # <class 'typing_graph.ConcreteType'>
print(node.cls)    # <class 'str'>

# The metadata is hoisted to this node
print(node.metadata)  # (MaxLen(value=50),)
```

This design means you get a [`ConcreteType`][typing_graph.ConcreteType] (or other appropriate node type) with metadata attached, allowing you to work with the actual type while still having access to its metadata.

## Accessing the metadata tuple

Every type node has a `metadata` attribute containing a tuple of metadata objects:

```python
from typing import Annotated
from typing_graph import inspect_type

@dataclass(frozen=True)
class Min:
    value: int

@dataclass(frozen=True)
class Max:
    value: int

@dataclass(frozen=True)
class Description:
    text: str

BoundedInt = Annotated[int, Min(0), Max(100), Description("A percentage")]

node = inspect_type(BoundedInt)

# Access all metadata
print(len(node.metadata))  # 3
for meta in node.metadata:
    print(meta)
```

Output:

```text
Min(value=0)
Max(value=100)
Description(text='A percentage')
```

If a type has no metadata, the tuple is empty:

```python
node = inspect_type(int)
print(node.metadata)  # ()
```

## Filtering by type

Use `isinstance()` to find specific metadata types:

```python
from typing import Annotated
from typing_graph import inspect_type

@dataclass(frozen=True)
class MinLen:
    value: int

@dataclass(frozen=True)
class MaxLen:
    value: int

@dataclass(frozen=True)
class Pattern:
    regex: str

Email = Annotated[str, MinLen(5), MaxLen(254), Pattern(r"^[\w.-]+@[\w.-]+\.\w+$")]
node = inspect_type(Email)

# Find the first matching metadata
def find_metadata(node, meta_type):
    """Find the first metadata of a given type."""
    for meta in node.metadata:
        if isinstance(meta, meta_type):
            return meta
    return None

pattern = find_metadata(node, Pattern)
if pattern:
    print(f"Regex: {pattern.regex}")
```

### Collecting all matches

To collect all metadata of a certain type:

```python
def collect_metadata(node, meta_type):
    """Collect all metadata of a given type."""
    return [m for m in node.metadata if isinstance(m, meta_type)]

# Find all length constraints
class LengthConstraint:
    """Base class for length constraints."""
    pass

@dataclass(frozen=True)
class MinLen(LengthConstraint):
    value: int

@dataclass(frozen=True)
class MaxLen(LengthConstraint):
    value: int

Text = Annotated[str, MinLen(1), MaxLen(1000)]
node = inspect_type(Text)

constraints = collect_metadata(node, LengthConstraint)
print(constraints)  # [MinLen(value=1), MaxLen(value=1000)]
```

## Working with doc metadata

The `typing_extensions.Doc` annotation provides documentation strings for types:

```python
from typing import Annotated
from typing_extensions import Doc
from typing_graph import inspect_type

UserId = Annotated[str, Doc("Unique identifier for a user")]

node = inspect_type(UserId)

# Find the Doc metadata
for meta in node.metadata:
    if isinstance(meta, Doc):
        print(f"Documentation: {meta.documentation}")
```

This is useful for generating documentation or help text from type annotations.

## Common patterns

### Building a constraint extractor

Here's a pattern for extracting validation constraints from a type:

```python
from typing import Annotated, Any
from dataclasses import dataclass
from typing_graph import inspect_type, TypeNode

@dataclass(frozen=True)
class Gt:
    value: int | float

@dataclass(frozen=True)
class Lt:
    value: int | float

@dataclass(frozen=True)
class MinLen:
    value: int

@dataclass(frozen=True)
class MaxLen:
    value: int

def extract_constraints(node: TypeNode) -> dict[str, Any]:
    """Extract all constraints from a type node's metadata."""
    constraints = {}

    for meta in node.metadata:
        if isinstance(meta, Gt):
            constraints["greater_than"] = meta.value
        elif isinstance(meta, Lt):
            constraints["less_than"] = meta.value
        elif isinstance(meta, MinLen):
            constraints["min_length"] = meta.value
        elif isinstance(meta, MaxLen):
            constraints["max_length"] = meta.value

    return constraints

# Usage
Price = Annotated[float, Gt(0), Lt(10000)]
node = inspect_type(Price)
print(extract_constraints(node))  # {'greater_than': 0, 'less_than': 10000}
```

### Processing nested metadata

When traversing a type graph, you often need to collect metadata from all levels:

```python
from typing import Annotated
from typing_graph import inspect_type, TypeNode

@dataclass(frozen=True)
class Description:
    text: str

def collect_all_descriptions(node: TypeNode) -> list[str]:
    """Recursively collect all Description metadata."""
    descriptions = []

    # Check this node
    for meta in node.metadata:
        if isinstance(meta, Description):
            descriptions.append(meta.text)

    # Check children
    for child in node.children():
        descriptions.extend(collect_all_descriptions(child))

    return descriptions

# A type with metadata at multiple levels
URL = Annotated[str, Description("A URL string")]
URLs = Annotated[list[URL], Description("A list of URLs")]

node = inspect_type(URLs)
print(collect_all_descriptions(node))
# ['A list of URLs', 'A URL string']
```

## See also

- [Your first type inspection](../tutorials/first-inspection.md) - Introduction to type inspection
- [Walking the type graph](walking-type-graph.md) - Traversal patterns
- [Configuration options](configuration.md) - Controlling metadata hoisting
