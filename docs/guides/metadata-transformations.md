<!-- vale Google.Headings = NO -->
<!-- Headlines use API method names (exclude(), flatten(), sorted(), etc.) which are proper nouns -->

# How to combine and transform metadata

This guide shows you how to transform [`MetadataCollection`][typing_graph.MetadataCollection] instances through combining, sorting, deduplicating, and mapping operations. You'll learn to merge collections, remove duplicates, sort by custom criteria, and extract values.

## Quick reference

| Goal | Method | Returns |
| ---- | ------ | ------- |
| Merge two collections | [`+`](#merging-metadata-from-multiple-sources) / [`\|`](#merging-metadata-from-multiple-sources) | `MetadataCollection` |
| Exclude specific types | [`exclude()`](#exclude-by-type) | `MetadataCollection` |
| Expand grouped constraints | [`flatten()`](#flatten-single-level) | `MetadataCollection` |
| Recursively expand all groups | [`flatten_deep()`](#flatten_deep-recursive) | `MetadataCollection` |
| Remove duplicates | [`unique()`](#unique-for-duplicates) | `MetadataCollection` |
| Sort items | [`sorted()`](#sorted-with-default-key) | `MetadataCollection` |
| Reverse order | [`reversed()`](#reversed-ordering) | `MetadataCollection` |
| Extract values | [`map()`](#map-returns-tuple) | `tuple` |
| Split by condition | [`partition()`](#partition-for-splitting) | `tuple[MetadataCollection, MetadataCollection]` |
| Get unique types | [`types()`](#types-for-unique-types) | `frozenset[type]` |
| Group by type | [`by_type()`](#by_type-for-grouping) | `Mapping[type, MetadataCollection]` |

## Merging metadata from multiple sources

### __add__ (+) operator

Use `+` to combine two collections:

```python
from typing_graph import MetadataCollection

a = MetadataCollection(_items=(1, 2))
b = MetadataCollection(_items=(3, 4))

combined = a + b
print(list(combined))  # [1, 2, 3, 4]
```

### __or__ (|) operator

The `|` operator works identically to `+`:

```python
from typing_graph import MetadataCollection

a = MetadataCollection(_items=(1, 2))
b = MetadataCollection(_items=(3, 4))

combined = a | b
print(list(combined))  # [1, 2, 3, 4]
```

!!! note "Operator equivalence"

    The `+` and `|` operators are completely equivalent, so use whichever reads better in your context. The `|` operator is often more intuitive when thinking of collections as sets being combined.

### Preserving order

Both operators preserve the order of items from left to right:

```python
from typing_graph import MetadataCollection

first = MetadataCollection(_items=("a", "b"))
second = MetadataCollection(_items=("c", "d"))
third = MetadataCollection(_items=("e", "f"))

# Chain multiple combinations
result = first + second + third
print(list(result))  # ['a', 'b', 'c', 'd', 'e', 'f']
```

## Excluding specific metadata types

### exclude() by type

Use [`exclude()`][typing_graph.MetadataCollection.exclude] to remove items of specific types:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=("a", 1, "b", 2))
no_strings = coll.exclude(str)
print(list(no_strings))  # [1, 2]
```

### Chaining exclusions

Exclude multiple types by chaining calls or passing multiple types:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=("a", 1, True, 2.5, "b"))

# Chain exclusions
result = coll.exclude(str).exclude(bool)
print(list(result))  # [1, 2.5]

# Or exclude multiple types at once
result = coll.exclude(str, bool)
print(list(result))  # [1, 2.5]
```

## Expanding grouped constraints

`GroupedMetadata` is a protocol from the [annotated-types](https://github.com/annotated-types/annotated-types) library for metadata that contains other metadata. For example, `Interval(ge=0, le=100)` groups `Ge(0)` and `Le(100)` into a single constraint. See [GroupedMetadata automatic flattening](../explanation/metadata.md#groupedmetadata-automatic-flattening) for more background.

### flatten() single level

Use [`flatten()`][typing_graph.MetadataCollection.flatten] to expand `GroupedMetadata` items one level:

```python
from annotated_types import Ge, Interval, Le
from typing_graph import MetadataCollection

interval = Interval(ge=5, le=15)
coll = MetadataCollection.of([interval], auto_flatten=False)
flattened = coll.flatten()
print(list(flattened))  # [Ge(ge=5), Le(le=15)]
```

### flatten_deep() recursive

Use [`flatten_deep()`][typing_graph.MetadataCollection.flatten_deep] to recursively expand nested `GroupedMetadata`:

```python
from typing_graph import MetadataCollection

# For deeply nested GroupedMetadata structures
coll = MetadataCollection(_items=(1, 2, 3))
deep_flat = coll.flatten_deep()
print(list(deep_flat))  # [1, 2, 3]
```

??? info "When to use flatten() vs flatten_deep()"

    | Method | Behavior | Use when |
    |--------|----------|----------|
    | `flatten()` | Expands one level | You only want immediate children expanded |
    | `flatten_deep()` | Recursively expands all levels | You want all nested `GroupedMetadata` fully unwrapped |

    In practice, `flatten()` is sufficient for most cases since `annotated-types` constraints don't nest `GroupedMetadata` deeply. Use `flatten_deep()` only if you have custom `GroupedMetadata` implementations that might be nested.

### auto_flatten parameter

Both flatten methods return `self` if no `GroupedMetadata` items exist, avoiding unnecessary allocations.

When creating collections, `auto_flatten=True` (the default) automatically flattens:

```python
from annotated_types import Interval
from typing_graph import MetadataCollection

interval = Interval(ge=0, le=100)

# Default: auto_flatten=True
coll = MetadataCollection.of([interval])
print(len(coll))  # 2 (Ge and Le)

# Disable flattening
coll = MetadataCollection.of([interval], auto_flatten=False)
print(len(coll))  # 1 (the Interval itself)
```

## Removing duplicates and sorting

### unique() for duplicates

Use [`unique()`][typing_graph.MetadataCollection.unique] to remove duplicate items:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=(1, 2, 1, 3, 2))
unique = coll.unique()
print(list(unique))  # [1, 2, 3]
```

The method preserves first occurrence order and handles unhashable items:

```python
from typing_graph import MetadataCollection

# Works with unhashable items too
coll = MetadataCollection(_items=([1, 2], [3, 4], [1, 2]))
unique = coll.unique()
print(list(unique))  # [[1, 2], [3, 4]]
```

!!! warning "Performance with unhashable items"

    `unique()` is O(n) for hashable items but O(n^2) for unhashable items. For collections with unhashable items and many duplicates, consider filtering before calling `unique()`.

### sorted() with default key

Use [`sorted()`][typing_graph.MetadataCollection.sorted] to sort items:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=(3, 1, 2))
sorted_coll = coll.sorted()
print(list(sorted_coll))  # [1, 2, 3]
```

The default sort key groups items by type name first, then by value:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=("b", 2, "a", 1))
sorted_coll = coll.sorted()
# Integers before strings (alphabetically by type name)
print(list(sorted_coll))  # [1, 2, 'a', 'b']
```

### sorted() with custom key

Provide a custom key function for specific ordering:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=("bb", "a", "ccc"))
by_len = coll.sorted(key=len)
print(list(by_len))  # ['a', 'bb', 'ccc']
```

```python
from dataclasses import dataclass
from typing_graph import MetadataCollection

@dataclass(frozen=True)
class Constraint:
    value: int

coll = MetadataCollection(_items=(
    Constraint(10),
    Constraint(5),
    Constraint(20)
))
by_value = coll.sorted(key=lambda c: c.value)
print(list(by_value))  # [Constraint(value=5), Constraint(value=10), Constraint(value=20)]
```

### reversed() ordering

Use [`reversed()`][typing_graph.MetadataCollection.reversed] to reverse the order:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=(1, 2, 3))
rev = coll.reversed()
print(list(rev))  # [3, 2, 1]
```

Combine with `sorted()` for descending order:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=(3, 1, 2))
descending = coll.sorted().reversed()
print(list(descending))  # [3, 2, 1]
```

## Extracting values from metadata

### map() returns tuple

Use [`map()`][typing_graph.MetadataCollection.map] to transform items. This is a terminal operation that returns a tuple, not a new collection:

!!! tip "Terminal operation"

    `map()` returns a `tuple`, not a `MetadataCollection`. This is intentional because the transformed values may not be valid metadata items. If you need to chain operations, apply `map()` last.

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=(1, 2, 3))
doubled = coll.map(lambda x: x * 2)
print(doubled)       # (2, 4, 6)
print(type(doubled)) # <class 'tuple'>
```

Extract specific attributes:

```python
from dataclasses import dataclass
from typing_graph import MetadataCollection

@dataclass(frozen=True)
class Constraint:
    value: int

coll = MetadataCollection(_items=(Constraint(10), Constraint(5), Constraint(20)))
values = coll.map(lambda c: c.value)
print(values)  # (10, 5, 20)
```

### partition() for splitting

Use [`partition()`][typing_graph.MetadataCollection.partition] to split a collection by a predicate:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=(1, 2, 3, 4, 5))
evens, odds = coll.partition(lambda x: x % 2 == 0)
print(list(evens))  # [2, 4]
print(list(odds))   # [1, 3, 5]
```

The first collection contains items where the predicate is `True`, the second where it's `False`:

```python
from dataclasses import dataclass
from typing_graph import MetadataCollection

@dataclass(frozen=True)
class Constraint:
    value: int
    strict: bool = False

coll = MetadataCollection(_items=(
    Constraint(0, strict=True),
    Constraint(10, strict=False),
    Constraint(5, strict=True)
))
strict, lenient = coll.partition(lambda c: c.strict)
print(list(strict))   # [Constraint(value=0, strict=True), Constraint(value=5, strict=True)]
print(list(lenient))  # [Constraint(value=10, strict=False)]
```

## Analyzing metadata composition

### types() for unique types

Use [`types()`][typing_graph.MetadataCollection.types] to get the unique types in a collection:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=("a", 1, "b", 2.0))
types = coll.types()
print(sorted(t.__name__ for t in types))  # ['float', 'int', 'str']
```

Returns a `frozenset` of types:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=(1, 2, 3))
types = coll.types()
print(type(types))  # <class 'frozenset'>
print(int in types)  # True
```

### by_type() for grouping

Use [`by_type()`][typing_graph.MetadataCollection.by_type] to group items by their type:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=("a", 1, "b", 2))
grouped = coll.by_type()
print(list(grouped[str]))  # ['a', 'b']
print(list(grouped[int]))  # [1, 2]
```

The returned mapping is immutable:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=(1, 2, "a"))
grouped = coll.by_type()

# Access groups
for type_, items in grouped.items():
    print(f"{type_.__name__}: {list(items)}")
# int: [1, 2]
# str: ['a']
```

## Result

You can now merge collections with `+` or `|`, exclude types with `exclude()`, expand grouped constraints with `flatten()` and `flatten_deep()`, remove duplicates with `unique()`, sort with `sorted()`, extract values with `map()`, split with `partition()`, and analyze composition with `types()` and `by_type()`.

## See also

- [Working with metadata](../tutorials/working-with-metadata.md) - Tutorial introduction
- [Querying metadata](metadata-queries.md) - Finding metadata by type
- [Filtering metadata](metadata-filtering.md) - Predicate and protocol-based filtering
- [Metadata recipes](metadata-recipes.md) - Real-world patterns and troubleshooting
- [Metadata and Annotated](../explanation/metadata.md) - Design rationale and concepts
- [GroupedMetadata](../reference/glossary.md#grouped-metadata) - Glossary definition
