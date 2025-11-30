<!-- vale Google.Headings = NO -->
<!-- vale Google.Colons = NO -->
<!-- Headlines use API method names (filter(), first(), etc.) which are proper nouns -->
<!-- Code blocks contain type annotations with colons (: P, : A) -->

# How to filter metadata by conditions

This guide shows you how to filter [`MetadataCollection`][typing_graph.MetadataCollection] contents using predicate functions, type constraints, and runtime-checkable protocols. You'll learn to select items matching custom conditions, combine type-safe filtering with predicates, and use structural typing with protocols.

## Quick reference

| Goal | Method | Returns |
| ---- | ------ | ------- |
| Filter by custom condition | [`filter()`](#filter-with-lambda-functions) | `MetadataCollection` |
| Type-safe filtering with predicate | [`filter_by_type()`](#filter_by_type-for-typed-predicates) | `MetadataCollection` |
| Find first matching condition | [`first()`](#first-vs-find) | `T \| None` |
| Find first of type matching condition | [`first_of_type()`](#first_of_type-with-predicate) | `T \| None` |
| Check if any matches | [`any()`](#any-for-boolean-checks) | `bool` |
| Find by structural interface | [`find_protocol()`](#find_protocol-usage) | `MetadataCollection` |
| Check protocol existence | [`has_protocol()`](#has_protocol-and-count_protocol) | `bool` |
| Count protocol matches | [`count_protocol()`](#has_protocol-and-count_protocol) | `int` |

## Method comparison

When filtering metadata, choose the method that best fits your need:

| Method | Input | Returns | Stops early? | Use when |
| ------ | ----- | ------- | ------------ | -------- |
| `find(type_)` | Type | Single item or None | Yes | Finding by exact type |
| `first(predicate)` | Callable | Single item or None | Yes | Finding by condition |
| `filter(predicate)` | Callable | Collection | No | Getting all matches |
| `filter_by_type(type_, predicate)` | Type + Callable | Collection | No | Type-safe filtering |
| `find_protocol(protocol)` | Protocol | Collection | No | Structural matching |

## Filtering by custom conditions

### filter() with lambda functions

Use [`filter()`][typing_graph.MetadataCollection.filter] to filter items by a predicate function:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=(1, 2, 3, 4, 5))
evens = coll.filter(lambda x: x % 2 == 0)
print(list(evens))  # [2, 4]
```

### filter() with named functions

For complex predicates, use named functions for clarity:

```python
from dataclasses import dataclass
from typing_graph import MetadataCollection

@dataclass(frozen=True)
class Constraint:
    value: int
    strict: bool = False

def is_strict_constraint(item):
    """Check if item is a strict constraint."""
    return isinstance(item, Constraint) and item.strict

coll = MetadataCollection(_items=(
    Constraint(0, strict=True),
    Constraint(10, strict=False),
    Constraint(5, strict=True),
    "doc"
))
strict = coll.filter(is_strict_constraint)
print(list(strict))  # [Constraint(value=0, strict=True), Constraint(value=5, strict=True)]
```

!!! tip "Performance"

    Prefer `first()` over `filter()` when you only need one result. `first()` stops at the first match, while `filter()` processes all items.

## Combining type and predicate filters

### filter_by_type() for typed predicates

Use [`filter_by_type()`][typing_graph.MetadataCollection.filter_by_type] for type-safe filtering with a typed predicate:

```python
from dataclasses import dataclass
from typing_graph import MetadataCollection

@dataclass(frozen=True)
class Gt:
    value: int

coll = MetadataCollection(_items=(Gt(0), Gt(10), Gt(5), "doc"))

# Filter Gt items where value > 5
large = coll.filter_by_type(Gt, lambda x: x.value > 5)  # (1)!
print(list(large))  # [Gt(value=10)]
```

1. First filters to `Gt` instances, then applies predicate. The predicate receives typed `Gt` objects.

### Combining type and predicate

`filter_by_type()` first filters by type, then applies the predicate only to matching items:

```python
from dataclasses import dataclass
from typing_graph import MetadataCollection

@dataclass(frozen=True)
class Range:
    min: int
    max: int

coll = MetadataCollection(_items=(
    Range(0, 10),
    Range(5, 100),
    Range(-10, 10),
    "doc"
))

# Find ranges that include zero
includes_zero = coll.filter_by_type(Range, lambda r: r.min <= 0 <= r.max)
print(list(includes_zero))  # [Range(min=0, max=10), Range(min=-10, max=10)]
```

## Getting the first item matching a condition

### first() vs find()

[`first()`][typing_graph.MetadataCollection.first] finds the first item matching a predicate, while [`find()`][typing_graph.MetadataCollection.find] finds by type:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=(1, 2, 3, 4, 5))

# first() uses a predicate
result = coll.first(lambda x: x > 3)
print(result)  # 4

# find() uses a type
result = coll.find(int)
print(result)  # 1
```

### first_of_type() with predicate

Use [`first_of_type()`][typing_graph.MetadataCollection.first_of_type] to combine type filtering with a predicate:

```python
from dataclasses import dataclass
from typing_graph import MetadataCollection

@dataclass(frozen=True)
class Gt:
    value: int

coll = MetadataCollection(_items=(Gt(0), Gt(10), Gt(5), "doc"))

# Find first Gt where value > 3
result = coll.first_of_type(Gt, lambda x: x.value > 3)
print(result)  # Gt(value=10)

# Returns None if no match
result = coll.first_of_type(Gt, lambda x: x.value > 100)
print(result)  # None
```

### any() for boolean checks

Use [`any()`][typing_graph.MetadataCollection.any] to check if any item matches a predicate:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=(1, 2, 3, 4, 5))

# Check if any item is greater than 3
print(coll.any(lambda x: x > 3))  # True

# Check if any item is negative
print(coll.any(lambda x: x < 0))  # False
```

!!! tip "Performance"

    Prefer `any()` over `filter()` + `bool()` for existence checks. `any()` stops at the first match.

## Filtering by structural interface

### Creating `@runtime_checkable` protocols

Define protocols with the `@runtime_checkable` decorator to use them for filtering:

!!! note "Why `@runtime_checkable` is required"

    Python's `isinstance()` only works with protocols decorated with `@runtime_checkable`. Without it, the protocol is only usable for static type checking. The decorator enables structural subtyping at runtime by adding `__subclasshook__` support.

```python
from typing import Protocol, runtime_checkable
from dataclasses import dataclass

@runtime_checkable
class HasValue(Protocol):  # (1)!
    value: int

@dataclass(frozen=True)
class Constraint:
    value: int  # (2)!

@dataclass(frozen=True)
class Description:
    text: str  # (3)!

# Constraint matches HasValue, Description does not
c = Constraint(42)
d = Description("doc")
print(isinstance(c, HasValue))  # True
print(isinstance(d, HasValue))  # False
```

1. Protocol requires a `value: int` attribute for structural matching.
2. `Constraint` has `value`, so it matches `HasValue` protocol.
3. `Description` has `text`, not `value`, so it does not match.

### find_protocol() usage

Use [`find_protocol()`][typing_graph.MetadataCollection.find_protocol] to find items matching a protocol:

```python
from typing import Protocol, runtime_checkable
from dataclasses import dataclass
from typing_graph import MetadataCollection

@runtime_checkable
class HasValue(Protocol):
    value: int

@dataclass(frozen=True)
class Constraint:
    value: int

coll = MetadataCollection(_items=(Constraint(0), "doc", Constraint(10)))
matches = coll.find_protocol(HasValue)
print(list(matches))  # [Constraint(value=0), Constraint(value=10)]
```

!!! warning "Performance"

    Avoid `find_protocol()` in hot paths. Protocol `isinstance` checks have significant overhead (~4us per item). Use `find()` with concrete types when possible.

### has_protocol() and count_protocol()

Use [`has_protocol()`][typing_graph.MetadataCollection.has_protocol] to check existence and [`count_protocol()`][typing_graph.MetadataCollection.count_protocol] to count matches:

```python
from typing import Protocol, runtime_checkable
from dataclasses import dataclass
from typing_graph import MetadataCollection

@runtime_checkable
class HasValue(Protocol):
    value: int

@dataclass(frozen=True)
class Constraint:
    value: int

coll = MetadataCollection(_items=(Constraint(0), "doc", Constraint(10)))

# Check if any item matches
print(coll.has_protocol(HasValue))  # True

# Count matching items
print(coll.count_protocol(HasValue))  # 2
```

### ProtocolNotRuntimeCheckableError handling

Using a non-runtime-checkable protocol raises [`ProtocolNotRuntimeCheckableError`][typing_graph.ProtocolNotRuntimeCheckableError]:

```python
from typing import Protocol
from typing_graph import MetadataCollection, ProtocolNotRuntimeCheckableError

class NotRuntime(Protocol):
    value: int

coll = MetadataCollection(_items=(1, 2, 3))

try:
    coll.find_protocol(NotRuntime)
except ProtocolNotRuntimeCheckableError as e:
    print(e.protocol)  # <class 'NotRuntime'>
    print(str(e))
    # NotRuntime is not @runtime_checkable. Add @runtime_checkable decorator...
```

??? failure "Troubleshooting: ProtocolNotRuntimeCheckableError"

    **Problem**: You get `ProtocolNotRuntimeCheckableError` when using a protocol with `find_protocol()`, `has_protocol()`, or `count_protocol()`.

    **Cause**: The protocol is missing the `@runtime_checkable` decorator.

    **Solution**: Add the decorator to your protocol definition:

    ```python
    from typing import Protocol, runtime_checkable

    @runtime_checkable  # Add this decorator
    class HasValue(Protocol):
        value: int
    ```

    **Note**: If you don't control the protocol definition (for example, if it's from a third-party library), you cannot use it with protocol-based filtering. Use `filter()` with a custom predicate instead:

    ```python
    # Alternative: use filter() with duck typing
    matches = coll.filter(lambda x: hasattr(x, "value"))
    ```

## Result

You can now filter metadata with predicate functions using `filter()` and `first()`, combine type safety with predicates using `filter_by_type()` and `first_of_type()`, and use structural typing with `find_protocol()`, `has_protocol()`, and `count_protocol()`.

## See also

- [Working with metadata](../tutorials/working-with-metadata.md) - Tutorial introduction
- [Querying metadata](metadata-queries.md) - Finding metadata by type
- [Transforming metadata](metadata-transformations.md) - Combining, sorting, and mapping
- [Metadata recipes](metadata-recipes.md) - Real-world patterns and troubleshooting
- [Metadata and Annotated](../explanation/metadata.md) - Design rationale and concepts
- [MetadataCollection](../reference/glossary.md#metadata-collection) - Glossary definition
