<!-- vale Google.Headings = NO -->
<!-- vale Google.Colons = NO -->
<!-- Headlines use API class/method names (Doc, ProtocolNotRuntimeCheckableError) which are proper nouns -->
<!-- Code blocks contain type annotations with colons (: P, : A) -->

# How to solve common metadata tasks

This guide provides practical solutions to common real-world tasks involving [`MetadataCollection`][typing_graph.MetadataCollection]. You'll find patterns for extracting validation constraints, generating documentation from type annotations, traversing type graphs for metadata, and troubleshooting common issues.

## Quick reference

| Goal | Section | Key methods |
| ---- | ------- | ----------- |
| Extract validation constraints | [Building a constraint extractor](#building-a-constraint-extractor) | `find()`, `by_type()` |
| Work with annotated-types | [Working with annotated-types constraints](#working-with-annotated-types-constraints) | `find_all()` |
| Find documentation | [Finding documentation strings](#finding-documentation-strings) | `find()` |
| Process nested metadata | [Collecting metadata from type graph](#collecting-metadata-from-type-graph) | `find()`, `find_protocol()` |
| Create reusable extractors | [Type-safe extraction functions](#type-safe-extraction-functions) | `find()`, `get()` |
| Build metadata registries | [Building metadata registries](#building-metadata-registries) | `find_all()` |

## Extracting validation constraints

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
    constraints: dict[str, Any] = {}

    gt = node.metadata.find(Gt)
    if gt is not None:
        constraints["greater_than"] = gt.value

    lt = node.metadata.find(Lt)
    if lt is not None:
        constraints["less_than"] = lt.value

    min_len = node.metadata.find(MinLen)
    if min_len is not None:
        constraints["min_length"] = min_len.value

    max_len = node.metadata.find(MaxLen)
    if max_len is not None:
        constraints["max_length"] = max_len.value

    return constraints

# Usage
Price = Annotated[float, Gt(0), Lt(10000)]
node = inspect_type(Price)
print(extract_constraints(node))  # {'greater_than': 0, 'less_than': 10000}
```

### Working with annotated-types constraints

The [annotated-types](https://github.com/annotated-types/annotated-types) library provides standard constraint types that integrate naturally with typing-graph. Use `find_all()` to collect related constraints:

```python
from typing import Annotated
from annotated_types import Ge, Le, Gt, Lt
from typing_graph import inspect_type

BoundedInt = Annotated[int, Ge(0), Le(100)]
node = inspect_type(BoundedInt)

# Find all numeric bounds
lower_bounds = node.metadata.find_all(Ge, Gt)
upper_bounds = node.metadata.find_all(Le, Lt)

print(f"Lower: {list(lower_bounds)}")  # [Ge(ge=0)]
print(f"Upper: {list(upper_bounds)}")  # [Le(le=100)]
```

### Handling multiple constraint types

Use `by_type()` to organize constraints by category:

```python
from typing import Annotated
from dataclasses import dataclass
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

# Group by type
by_type = node.metadata.by_type()

# Access each constraint category
if MinLen in by_type:
    min_len = list(by_type[MinLen])[0]
    print(f"Minimum length: {min_len.value}")

if Pattern in by_type:
    pattern = list(by_type[Pattern])[0]
    print(f"Pattern: {pattern.regex}")
```

## Working with Doc metadata

!!! tip "Doc metadata pattern"

    The `typing_extensions.Doc` annotation is a standard way to attach documentation to types. It's widely supported by documentation generators and validation frameworks.

    While [PEP 727](https://peps.python.org/pep-0727/) (which proposed `Doc`) was withdrawn, `typing_extensions.Doc` remains available and is the recommended approach for attaching documentation to type annotations.

### Finding documentation strings

The `typing_extensions.Doc` annotation provides documentation strings for types:

```python
from typing import Annotated
from typing_extensions import Doc
from typing_graph import inspect_type

UserId = Annotated[str, Doc("Unique identifier for a user")]

node = inspect_type(UserId)

# Find the Doc metadata
doc = node.metadata.find(Doc)
if doc is not None:
    print(f"Documentation: {doc.documentation}")
```

### Generating help text

Build help text from multiple documentation sources:

```python
from typing import Annotated
from typing_extensions import Doc
from dataclasses import dataclass
from typing_graph import inspect_type

@dataclass(frozen=True)
class Example:
    value: str

@dataclass(frozen=True)
class Deprecated:
    reason: str

def generate_help(node) -> str:
    """Generate help text from metadata."""
    parts = []

    # Main documentation
    doc = node.metadata.find(Doc)
    if doc is not None:
        parts.append(doc.documentation)

    # Deprecation warning
    deprecated = node.metadata.find(Deprecated)
    if deprecated is not None:
        parts.append(f"DEPRECATED: {deprecated.reason}")

    # Examples
    examples = node.metadata.find_all(Example)
    if examples:
        parts.append("Examples:")
        for ex in examples:
            parts.append(f"  - {ex.value}")

    return "\n".join(parts)

# Usage
MyField = Annotated[
    str,
    Doc("A user's display name"),
    Example("John Doe"),
    Example("jane_doe")
]
node = inspect_type(MyField)
print(generate_help(node))
```

## Processing nested metadata

### Collecting metadata from type graph

When traversing a type graph, collect metadata from all levels:

```python
from typing import Annotated
from dataclasses import dataclass
from typing_graph import inspect_type, TypeNode

@dataclass(frozen=True)
class Description:
    text: str

def collect_all_descriptions(node: TypeNode) -> list[str]:
    """Recursively collect all Description metadata."""
    descriptions = []

    # Check this node
    desc = node.metadata.find(Description)  # (1)!
    if desc is not None:
        descriptions.append(desc.text)

    # Check children
    for child in node.children():  # (2)!
        descriptions.extend(collect_all_descriptions(child))

    return descriptions

# A type with metadata at multiple levels
URL = Annotated[str, Description("A URL string")]
URLs = Annotated[list[URL], Description("A list of URLs")]

node = inspect_type(URLs)
print(collect_all_descriptions(node))
# ['A list of URLs', 'A URL string']
```

1. Each node carries only its own metadata, not nested metadata.
2. Recurse through `children()` to collect metadata from all levels.

### Combining with node traversal

Use the metadata collection's methods during graph traversal:

```python
from typing import Annotated, Protocol, runtime_checkable
from dataclasses import dataclass
from typing_graph import inspect_type, TypeNode

@runtime_checkable
class Validatable(Protocol):
    def validate(self, value: object) -> bool: ...

@dataclass(frozen=True)
class Range:
    min: int
    max: int

    def validate(self, value: object) -> bool:
        if isinstance(value, int):
            return self.min <= value <= self.max
        return False

def find_all_validators(node: TypeNode) -> list[Validatable]:
    """Find all validators in the type graph."""
    validators: list[Validatable] = []

    # Find validators at this node
    node_validators = node.metadata.find_protocol(Validatable)
    validators.extend(node_validators)

    # Recurse into children
    for child in node.children():
        validators.extend(find_all_validators(child))

    return validators

# Usage
MyType = Annotated[list[Annotated[int, Range(0, 100)]], Range(1, 10)]
node = inspect_type(MyType)
validators = find_all_validators(node)
print(f"Found {len(validators)} validators")
```

## Common patterns

### Type-safe extraction functions

Create reusable extraction functions with proper typing:

```python
from typing import Annotated, TypeVar
from typing_graph import MetadataCollection, inspect_type

T = TypeVar("T")

def get_metadata_or_default(
    metadata: MetadataCollection,
    type_: type[T],
    default: T
) -> T:
    """Get metadata of a type, returning default if not found."""
    result = metadata.find(type_)
    return result if result is not None else default

# Usage
from dataclasses import dataclass

@dataclass(frozen=True)
class MaxLen:
    value: int

# When present
coll = MetadataCollection(_items=(MaxLen(50),))
max_len = get_metadata_or_default(coll, MaxLen, MaxLen(100))
print(max_len.value)  # 50

# When absent
coll = MetadataCollection.EMPTY
max_len = get_metadata_or_default(coll, MaxLen, MaxLen(100))
print(max_len.value)  # 100
```

### Building metadata registries

Create registries that map types to their metadata handlers:

```python
from typing import Annotated, Callable
from dataclasses import dataclass
from typing_graph import inspect_type, MetadataCollection

@dataclass(frozen=True)
class Validator:
    func: Callable[[object], bool]

@dataclass(frozen=True)
class Serializer:
    func: Callable[[object], str]

class MetadataRegistry:
    """Registry for processing different metadata types."""

    def __init__(self):
        self._handlers: dict[type, Callable] = {}

    def register(self, meta_type: type, handler: Callable) -> None:
        self._handlers[meta_type] = handler

    def process(self, metadata: MetadataCollection) -> dict[str, object]:
        results: dict[str, object] = {}
        for meta_type, handler in self._handlers.items():
            items = metadata.find_all(meta_type)
            if items:
                results[meta_type.__name__] = handler(list(items))
        return results

# Usage
registry = MetadataRegistry()
registry.register(Validator, lambda vs: [v.func for v in vs])
registry.register(Serializer, lambda ss: ss[0].func if ss else None)
```

## Troubleshooting

### Slow unique() with unhashable items

The `unique()` method is slow with many unhashable items because it falls back to O(n^2) comparison.

**Solution**: Partition hashable and unhashable items first:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=([1, 2], [3, 4], [1, 2], "a", "a"))

# Separate hashable and unhashable
hashable, unhashable = coll.partition(
    lambda x: isinstance(x, (str, int, float, tuple, frozenset))
)

# unique() is O(n) for hashable items
unique_hashable = hashable.unique()
unique_unhashable = unhashable.unique()  # O(n^2) but smaller n

result = unique_hashable + unique_unhashable
```

### ProtocolNotRuntimeCheckableError

The `find_protocol()` method raises `ProtocolNotRuntimeCheckableError` when the protocol is missing the `@runtime_checkable` decorator.

**Solution**: Add the decorator:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class HasValue(Protocol):
    value: int
```

### Empty results from queries

When query methods return `None` or empty collections unexpectedly, check these common causes:

**Type matching**: `find()` uses `isinstance`, so subclasses match:

```python
class Parent: pass
class Child(Parent): pass

coll = MetadataCollection(_items=(Child(),))
coll.find(Parent)  # Returns Child() - subclass matches
```

**Empty input**: Check if the collection is empty:

```python
coll = MetadataCollection.EMPTY
print(coll.is_empty)  # True
```

**Metadata hoisting**: Ensure metadata is on the node you're checking:

```python
MyType = Annotated[list[Annotated[int, "inner"]], "outer"]
node = inspect_type(MyType)

# "outer" is on list node, "inner" is on int node
print(list(node.metadata))  # ['outer']
print(list(node.args[0].metadata))  # ['inner']
```

**GroupedMetadata flattening**: By default, `GroupedMetadata` is expanded:

```python
from annotated_types import Ge, Interval
from typing_graph import MetadataCollection

interval = Interval(ge=0, le=100)
coll = MetadataCollection.of([interval])

# Interval was flattened into Ge and Le
coll.find(Interval)  # None
coll.find(Ge)        # Ge(ge=0)
```

## Result

You now have practical patterns for extracting constraints from types, working with annotated-types and Doc metadata, collecting metadata during type graph traversal, creating type-safe extraction utilities, and troubleshooting common issues with queries and protocols.

## See also

- [Working with metadata](../tutorials/working-with-metadata.md) - Tutorial introduction
- [Querying metadata](metadata-queries.md) - Finding metadata by type
- [Filtering metadata](metadata-filtering.md) - Predicate and protocol-based filtering
- [Transforming metadata](metadata-transformations.md) - Combining, sorting, and mapping
- [Walking the type graph](walking-type-graph.md) - Recursive traversal patterns
- [Metadata and Annotated](../explanation/metadata.md) - Design rationale and concepts
- [MetadataCollection](../reference/glossary.md#metadata-collection) - Glossary definition
