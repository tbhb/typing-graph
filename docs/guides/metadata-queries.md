<!-- vale Google.Headings = NO -->
<!-- Headlines use API method names (find(), get(), count(), etc.) which are proper nouns -->

# How to find specific metadata

This guide shows you how to find metadata items by type within a [`MetadataCollection`][typing_graph.MetadataCollection]. You'll learn to locate single items, collect all matches, check for existence, and handle missing metadata gracefully.

## Quick reference

| Goal | Method | Returns |
| ---- | ------ | ------- |
| Find first item of a type | [`find()`](#find-for-exact-type-match) | `T \| None` |
| Find first of several types | [`find_first()`](#find_first-for-multiple-candidate-types) | `object \| None` |
| Get all items matching types | [`find_all()`](#find_all-with-single-type) | `MetadataCollection` |
| Check if type exists | [`has()`](#has-vs-count) | `bool` |
| Count matching items | [`count()`](#count-for-single-type) | `int` |
| Get with fallback | [`get()`](#get-with-default-values) | `T` |
| Get or raise error | [`get_required()`](#get_required-for-mandatory-metadata) | `T` |
| Check if empty | [`is_empty`](#is_empty-property) | `bool` |

!!! note "Prerequisites"

    This guide assumes you know how to create `MetadataCollection` instances.
    See [Working with metadata](../tutorials/working-with-metadata.md) for construction basics.

## Finding the first matching item

### find() for exact type match

Use [`find()`][typing_graph.MetadataCollection.find] to get the first item matching a specific type:

```python
from dataclasses import dataclass
from typing_graph import MetadataCollection

@dataclass(frozen=True)
class Gt:
    value: int

@dataclass(frozen=True)
class Lt:
    value: int

coll = MetadataCollection(_items=(Gt(0), Lt(100), Gt(10), "doc"))  # (1)!

# Find first item of type
constraint = coll.find(Gt)  # (2)!
print(constraint)  # Gt(value=0)

# Returns None if not found
missing = coll.find(float)
print(missing)  # None
```

1. Creates an immutable collection with two `Gt` instances, one `Lt`, and a string.
2. Returns the **first** `Gt` found (`Gt(0)`), not `Gt(10)`. Stops searching at first match.

The `find()` method uses `isinstance` semantics, so subclasses also match:

```python
from typing_graph import MetadataCollection

class Animal:
    pass

class Dog(Animal):
    pass

coll = MetadataCollection(_items=(Dog(), "doc"))
result = coll.find(Animal)  # Returns the Dog instance
```

!!! tip "Performance"

    Prefer `find()` over `find_all()` when you only need the first match. `find()` stops at the first match, while `find_all()` scans the entire collection.

### find_first() for multiple candidate types

Use [`find_first()`][typing_graph.MetadataCollection.find_first] to find the first item matching any of several types:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=("doc", 42, True))

# Find first item matching any type
result = coll.find_first(int, float)
print(result)  # 42

# Returns None if no types match
result = coll.find_first(list, dict)
print(result)  # None
```

### Handling None results

Both `find()` and `find_first()` return `None` when no match is found. Use conditional checks or the `get()` method with defaults:

```python
from dataclasses import dataclass
from typing_graph import MetadataCollection

@dataclass(frozen=True)
class Description:
    text: str

coll = MetadataCollection(_items=(42, "doc"))

# Conditional check
desc = coll.find(Description)
if desc is not None:
    print(desc.text)
else:
    print("No description")
```

!!! tip "Safe None handling with walrus operator"

    Use Python's walrus operator (`:=`) for concise None-safe patterns:

    ```python
    if (desc := coll.find(Description)) is not None:
        print(desc.text)
    ```

## Collecting all items of a type

### find_all() with single type

Use [`find_all()`][typing_graph.MetadataCollection.find_all] to get all items matching a type:

```python
from dataclasses import dataclass
from typing_graph import MetadataCollection

@dataclass(frozen=True)
class Gt:
    value: int

coll = MetadataCollection(_items=(Gt(0), "doc", Gt(10), Gt(5)))

# Find all items of a type
all_gt = coll.find_all(Gt)
print(list(all_gt))  # [Gt(value=0), Gt(value=10), Gt(value=5)]
```

### find_all() with multiple types

Pass multiple types to find items matching any of them:

```python
from dataclasses import dataclass
from typing_graph import MetadataCollection

@dataclass(frozen=True)
class Gt:
    value: int

@dataclass(frozen=True)
class Lt:
    value: int

coll = MetadataCollection(_items=(Gt(0), Lt(100), Gt(10), "doc"))

# Find all items matching any of multiple types
constraints = coll.find_all(Gt, Lt)
print(list(constraints))  # [Gt(value=0), Lt(value=100), Gt(value=10)]
```

### Empty results

When no items match, `find_all()` returns an empty collection:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=("a", "b", "c"))
floats = coll.find_all(float)
print(len(floats))  # 0
print(floats is MetadataCollection.EMPTY)  # True
```

With no arguments, `find_all()` returns a copy of all items:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=(1, 2, 3))
all_items = coll.find_all()
print(list(all_items))  # [1, 2, 3]
```

## Checking existence

### has() vs count()

Use [`has()`][typing_graph.MetadataCollection.has] to check if any item matches given types:

```python
from dataclasses import dataclass
from typing_graph import MetadataCollection

@dataclass(frozen=True)
class Gt:
    value: int

coll = MetadataCollection(_items=(Gt(0), "doc", 42))

# Check for a single type
print(coll.has(Gt))     # True
print(coll.has(float))  # False

# Check for any of multiple types
print(coll.has(float, list))  # False
print(coll.has(str, int))     # True
```

!!! tip "Performance"

    Prefer `has()` over `count()` when you only need to know if something exists. `has()` stops at the first match, while `count()` scans the entire collection.

### is_empty property

Use the [`is_empty`][typing_graph.MetadataCollection.is_empty] property for readable empty checks:

```python
from typing_graph import MetadataCollection

empty = MetadataCollection.EMPTY
non_empty = MetadataCollection(_items=(1, 2))

print(empty.is_empty)      # True
print(non_empty.is_empty)  # False

# More readable than len() == 0
coll = MetadataCollection(_items=("a",))
if coll.is_empty:
    print("No metadata")
```

## Providing fallback values for missing metadata

### get() with default values

Use [`get()`][typing_graph.MetadataCollection.get] to retrieve an item with a default value if not found:

```python
from dataclasses import dataclass
from typing_graph import MetadataCollection

@dataclass(frozen=True)
class Gt:
    value: int

@dataclass(frozen=True)
class Lt:
    value: int

coll = MetadataCollection(_items=(Gt(0), "doc"))

# Get with no default returns None if not found
result = coll.get(Lt)
print(result)  # None

# Get with default value
result = coll.get(Lt, Lt(100))
print(result)  # Lt(value=100)

# Get returns the matched item, not the default
result = coll.get(Gt, Gt(999))
print(result)  # Gt(value=0)
```

### get() falsy value handling

The `get()` method correctly handles falsy values like `0`, `False`, and empty strings:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=(0, False, ""))

# Falsy values are returned correctly
print(coll.get(int, -1))   # 0 (not -1)
print(coll.get(str, "x"))  # '' (not 'x')
```

### get_required() for mandatory metadata

Use [`get_required()`][typing_graph.MetadataCollection.get_required] when metadata must exist:

!!! warning "Use sparingly"

    `get_required()` raises an exception when metadata is missing. Prefer `get()` with a sensible default unless the absence of metadata is truly exceptional and indicates a programming error.

=== "get() with default"

    ```python
    from dataclasses import dataclass
    from typing_graph import MetadataCollection

    @dataclass(frozen=True)
    class MaxLen:
        value: int

    coll = MetadataCollection(_items=("doc",))

    # Safe: returns default if not found
    max_len = coll.get(MaxLen, MaxLen(255))  # (1)!
    print(max_len.value)  # 255
    ```

    1. `MaxLen` not in collection, so returns the default `MaxLen(255)`.

=== "get_required()"

    ```python
    from dataclasses import dataclass
    from typing_graph import MetadataCollection, MetadataNotFoundError

    @dataclass(frozen=True)
    class MaxLen:
        value: int

    coll = MetadataCollection(_items=("doc",))

    # Raises MetadataNotFoundError if not found
    try:
        max_len = coll.get_required(MaxLen)  # (1)!
    except MetadataNotFoundError as e:
        print(f"Missing: {e.requested_type.__name__}")
    ```

    1. Raises `MetadataNotFoundError` because `MaxLen` is not in the collection.

## Counting matches

### count() for single type

Use [`count()`][typing_graph.MetadataCollection.count] to count items matching a type:

```python
from dataclasses import dataclass
from typing_graph import MetadataCollection

@dataclass(frozen=True)
class Gt:
    value: int

coll = MetadataCollection(_items=(Gt(0), "doc", Gt(10), Gt(5)))
print(coll.count(Gt))  # 3
```

### count() for multiple types

Pass multiple types to count items matching any of them:

```python
from dataclasses import dataclass
from typing_graph import MetadataCollection

@dataclass(frozen=True)
class Gt:
    value: int

@dataclass(frozen=True)
class Lt:
    value: int

coll = MetadataCollection(_items=(Gt(0), Lt(100), Gt(10), "doc"))

# Count items matching any of multiple types
print(coll.count(Gt, Lt))  # 3
```

## Result

You can now find metadata by type using `find()` and `find_first()`, collect all matches with `find_all()`, check existence with `has()` and `is_empty`, and handle missing metadata gracefully with `get()` and `get_required()`.

## See also

- [Working with metadata](../tutorials/working-with-metadata.md) - Tutorial introduction
- [Filtering metadata](metadata-filtering.md) - Predicate and protocol-based filtering
- [Transforming metadata](metadata-transformations.md) - Combining, sorting, and mapping
- [Metadata recipes](metadata-recipes.md) - Real-world patterns
- [Metadata and Annotated](../explanation/metadata.md) - Design rationale and concepts
- [MetadataCollection](../reference/glossary.md#metadata-collection) - Glossary definition
