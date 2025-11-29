# MetadataCollection

`MetadataCollection` is an immutable, type-safe container for metadata extracted from `Annotated` type annotations. It replaces raw tuples with a rich API for querying, filtering, and transforming metadata.

## Overview

When you inspect a type with typing-graph, each [`TypeNode`][typing_graph.TypeNode] carries a `metadata` attribute containing any metadata attached via `Annotated`. The `MetadataCollection` class provides a structured way to work with this metadata:

```python
from typing import Annotated
from dataclasses import dataclass
from typing_graph import inspect_type

@dataclass(frozen=True)
class Gt:
    value: int

@dataclass(frozen=True)
class Lt:
    value: int

# A type with multiple metadata items
BoundedInt = Annotated[int, Gt(0), Lt(100), "A positive integer less than 100"]

node = inspect_type(BoundedInt)
meta = node.metadata  # MetadataCollection

# Work with metadata using familiar Python patterns
print(len(meta))        # 3
print(list(meta))       # [Gt(value=0), Lt(value=100), 'A positive integer less than 100']
print(Gt(0) in meta)    # True
```

The collection is immutable---all transformation methods return new collections rather than modifying the existing one. This design enables safe sharing and caching across your application.

## Empty collections

An empty `MetadataCollection` represents a type with no metadata:

```python
from typing_graph import MetadataCollection

# Create an empty collection
empty = MetadataCollection()
print(len(empty))   # 0
print(bool(empty))  # False
print(list(empty))  # []
```

### The EMPTY singleton

For efficiency, use the `EMPTY` singleton instead of creating new empty collections:

```python
from typing_graph import MetadataCollection

# Use the singleton for empty collections
empty = MetadataCollection.EMPTY

# The singleton is always the same object
assert MetadataCollection.EMPTY is MetadataCollection.EMPTY

# Verify it's truly empty
assert len(MetadataCollection.EMPTY) == 0
assert not MetadataCollection.EMPTY
```

This pattern avoids repeated allocations when many types have no metadata.

## Sequence protocol

`MetadataCollection` implements Python's sequence protocol, making it work naturally with standard Python patterns.

### Length and iteration

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=("doc", 42, True))

# Get the item count
print(len(coll))  # 3

# Iterate over items in order
for item in coll:
    print(item)
# Output:
# doc
# 42
# True

# Convert to list
items = list(coll)
print(items)  # ['doc', 42, True]
```

### Membership testing

Use `in` to check if an item exists in the collection:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=("doc", 42, True))

print("doc" in coll)     # True
print("missing" in coll) # False
print(42 in coll)        # True
```

Membership testing uses equality comparison (`==`), not identity (`is`).

### Indexing and slicing

Access items by index or slice:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=("a", "b", "c", "d"))

# Integer indexing returns individual items
print(coll[0])   # 'a'
print(coll[-1])  # 'd'
print(coll[2])   # 'c'

# Slicing returns a new MetadataCollection
subset = coll[1:3]
print(list(subset))  # ['b', 'c']

# Step slicing also works
evens = coll[::2]
print(list(evens))   # ['a', 'c']
```

Integer indexing returns the item at that position. Slice indexing returns a new `MetadataCollection` containing the sliced items.

### Truthiness

Empty collections are falsy, non-empty collections are truthy:

```python
from typing_graph import MetadataCollection

empty = MetadataCollection.EMPTY
non_empty = MetadataCollection(_items=(1,))

if non_empty:
    print("Has metadata")  # This prints

if not empty:
    print("No metadata")   # This prints
```

## Equality and hashing

### Equality comparison

Two collections are equal if they contain the same items in the same order:

```python
from typing_graph import MetadataCollection

a = MetadataCollection(_items=(1, 2, 3))
b = MetadataCollection(_items=(1, 2, 3))
c = MetadataCollection(_items=(3, 2, 1))

print(a == b)  # True - same items, same order
print(a == c)  # False - same items, different order
```

Comparing with non-`MetadataCollection` objects returns `NotImplemented`, allowing Python to try the reverse comparison:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=(1, 2, 3))
print(coll == [1, 2, 3])  # False - different types
print(coll == (1, 2, 3))  # False - different types
```

### Hashing

Collections with all hashable items can be used as dict keys or set members:

```python
from typing_graph import MetadataCollection

# Hashable items work
coll = MetadataCollection(_items=(1, "doc", (2, 3)))
my_dict = {coll: "some value"}
my_set = {coll}

# Same items produce same hash
other = MetadataCollection(_items=(1, "doc", (2, 3)))
print(hash(coll) == hash(other))  # True
```

If any item is unhashable, attempting to hash the collection raises `TypeError`:

```python
from typing_graph import MetadataCollection

# Contains an unhashable dict
coll = MetadataCollection(_items=([1, 2],))

try:
    hash(coll)
except TypeError as e:
    print(e)  # MetadataCollection contains unhashable items: ...
```

### Checking hashability

Use the `is_hashable` property to check before attempting hash operations:

```python
from typing_graph import MetadataCollection

hashable = MetadataCollection(_items=(1, "doc"))
unhashable = MetadataCollection(_items=([1, 2],))

print(hashable.is_hashable)    # True
print(unhashable.is_hashable)  # False

# Safe pattern for conditional hashing
cache = {}
if hashable.is_hashable:
    cache[hashable] = "cached value"
```

This property never raises an exception---it returns `False` for unhashable collections.

## Debug representation

The `repr()` of a collection shows its contents:

```python
from typing_graph import MetadataCollection

# Empty collection
print(repr(MetadataCollection.EMPTY))
# MetadataCollection([])

# Small collection (5 items or fewer)
small = MetadataCollection(_items=(1, 2, 3))
print(repr(small))
# MetadataCollection([1, 2, 3])

# Large collection (more than 5 items)
large = MetadataCollection(_items=(1, 2, 3, 4, 5, 6, 7))
print(repr(large))
# MetadataCollection([1, 2, 3, 4, 5, ...<2 more>])
```

For collections with more than 5 items, the representation truncates to show the first 5 items plus a count of remaining items. This prevents overwhelming output when debugging large collections.

## Exception types

`MetadataCollection` defines two exception types for clear error handling.

### MetadataNotFoundError

Raised when a required metadata type is not found in a collection:

```python
from typing_graph import MetadataCollection, MetadataNotFoundError

coll = MetadataCollection()

try:
    raise MetadataNotFoundError(int, coll)
except MetadataNotFoundError as e:
    print(e.requested_type)  # <class 'int'>
    print(e.collection)      # MetadataCollection([])
    print(str(e))
    # No metadata of type 'int' found. Use find() instead of get_required() if the type may not exist.
```

The exception provides:

- `requested_type`: The type that was searched for but not found
- `collection`: The collection that was searched

This exception will be raised by query methods like `get_required()` in later stages.

### ProtocolNotRuntimeCheckableError

Raised when a non-runtime-checkable protocol is used with protocol-based methods:

```python
from typing import Protocol
from typing_graph import ProtocolNotRuntimeCheckableError

class NotRuntime(Protocol):
    value: int

try:
    raise ProtocolNotRuntimeCheckableError(NotRuntime)
except ProtocolNotRuntimeCheckableError as e:
    print(e.protocol)  # <class 'NotRuntime'>
    print(str(e))
    # NotRuntime is not @runtime_checkable. Add @runtime_checkable decorator to use with find_protocol() or has_protocol().
```

The exception provides:

- `protocol`: The protocol type that is not runtime checkable

This exception will be raised by protocol-based methods like `find_protocol()` and `has_protocol()` in later stages.

## Factory methods

### Creating from iterables

Use `MetadataCollection.of()` to create a collection from any iterable:

```python
from typing_graph import MetadataCollection

# Create from a list
coll = MetadataCollection.of(["doc", 42, True])
print(list(coll))  # ['doc', 42, True]

# Create from a tuple
coll = MetadataCollection.of(("a", "b", "c"))

# Create from a generator
coll = MetadataCollection.of(x for x in range(3))
print(list(coll))  # [0, 1, 2]

# Empty iterables return the EMPTY singleton
empty = MetadataCollection.of([])
assert empty is MetadataCollection.EMPTY
```

### Extracting from Annotated types

Use `MetadataCollection.from_annotated()` to extract metadata from `Annotated` types:

```python
from typing import Annotated
from typing_graph import MetadataCollection

# Extract metadata from Annotated
MyType = Annotated[int, "description", 42]
coll = MetadataCollection.from_annotated(MyType)
print(list(coll))  # ['description', 42]

# Non-Annotated types return EMPTY
coll = MetadataCollection.from_annotated(int)
assert coll is MetadataCollection.EMPTY
```

### GroupedMetadata handling

The factory methods automatically flatten `GroupedMetadata` from `annotated-types`:

```python
from typing import Annotated
from annotated_types import Ge, Interval, Le
from typing_graph import MetadataCollection

# Interval is a GroupedMetadata containing Ge and Le
interval = Interval(ge=0, le=100)
coll = MetadataCollection.of([interval])
print(list(coll))  # [Ge(ge=0), Le(le=100)]

# Also works with from_annotated
MyType = Annotated[int, Interval(ge=0, le=100)]
coll = MetadataCollection.from_annotated(MyType)
print(list(coll))  # [Ge(ge=0), Le(le=100)]
```

To preserve `GroupedMetadata` without flattening, use `auto_flatten=False`:

```python
from annotated_types import Interval
from typing_graph import MetadataCollection

interval = Interval(ge=0, le=100)
coll = MetadataCollection.of([interval], auto_flatten=False)
print(len(coll))  # 1 - the Interval itself
```

## Flatten methods

### Single-level flattening

Use `flatten()` to expand `GroupedMetadata` items one level:

```python
from annotated_types import Ge, Interval, Le
from typing_graph import MetadataCollection

interval = Interval(ge=5, le=15)
coll = MetadataCollection.of([interval], auto_flatten=False)
flattened = coll.flatten()
print(list(flattened))  # [Ge(ge=5), Le(le=15)]
```

### Deep flattening

Use `flatten_deep()` to recursively expand nested `GroupedMetadata`:

```python
from typing_graph import MetadataCollection

# For deeply nested GroupedMetadata structures
coll = MetadataCollection(_items=(1, 2, 3))
deep_flat = coll.flatten_deep()
print(list(deep_flat))  # [1, 2, 3]
```

Both flatten methods return `self` if no `GroupedMetadata` items exist, avoiding unnecessary allocations.

## Query methods

### Finding by type

Use `find()` to get the first item matching a specific type:

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

# Find first item of type
constraint = coll.find(Gt)
print(constraint)  # Gt(value=0)

# Returns None if not found
missing = coll.find(float)
print(missing)  # None
```

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

### Finding first of multiple types

Use `find_first()` to find the first item matching any of several types:

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

### Finding all matching items

Use `find_all()` to get all items matching specific types:

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

# Find all items of a type
all_gt = coll.find_all(Gt)
print(list(all_gt))  # [Gt(value=0), Gt(value=10)]

# Find all items matching any of multiple types
constraints = coll.find_all(Gt, Lt)
print(list(constraints))  # [Gt(value=0), Lt(value=100), Gt(value=10)]

# With no arguments, returns a copy of all items
all_items = coll.find_all()
print(list(all_items))  # [Gt(value=0), Lt(value=100), Gt(value=10), 'doc']
```

### Checking for presence

Use `has()` to check if any item matches given types:

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

### Counting matches

Use `count()` to count items matching given types:

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

# Count items of a type
print(coll.count(Gt))  # 2

# Count items matching any of multiple types
print(coll.count(Gt, Lt))  # 3
```

### Getting with defaults

Use `get()` to retrieve an item with a default value if not found:

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

The `get()` method correctly handles falsy values like `0`, `False`, and empty strings:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=(0, False, ""))

# Falsy values are returned correctly
print(coll.get(int, -1))   # 0 (not -1)
print(coll.get(str, "x"))  # '' (not 'x')
```

### Requiring metadata

Use `get_required()` when metadata must exist:

```python
from dataclasses import dataclass
from typing_graph import MetadataCollection, MetadataNotFoundError

@dataclass(frozen=True)
class Gt:
    value: int

@dataclass(frozen=True)
class Lt:
    value: int

coll = MetadataCollection(_items=(Gt(0), "doc"))

# Returns the item if found
constraint = coll.get_required(Gt)
print(constraint)  # Gt(value=0)

# Raises MetadataNotFoundError if not found
try:
    coll.get_required(Lt)
except MetadataNotFoundError as e:
    print(e.requested_type)  # <class 'Lt'>
    print(e.collection)      # MetadataCollection([...])
```

### Checking emptiness

Use the `is_empty` property for readable empty checks:

```python
from typing_graph import MetadataCollection

empty = MetadataCollection.EMPTY
non_empty = MetadataCollection(_items=(1, 2))

print(empty.is_empty)      # True
print(non_empty.is_empty)  # False

# More readable than len() == 0
if coll.is_empty:
    print("No metadata")
```

## Filtering methods

### Predicate-based filtering

Use `filter()` to filter items by a predicate function:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=(1, 2, 3, 4, 5))
evens = coll.filter(lambda x: x % 2 == 0)
print(list(evens))  # [2, 4]
```

Use `filter_by_type()` for type-safe filtering with a typed predicate:

```python
from dataclasses import dataclass
from typing_graph import MetadataCollection

@dataclass(frozen=True)
class Gt:
    value: int

coll = MetadataCollection(_items=(Gt(0), Gt(10), Gt(5), "doc"))
large = coll.filter_by_type(Gt, lambda x: x.value > 5)
print(list(large))  # [Gt(value=10)]
```

### Protocol-based filtering

Use `find_protocol()` to find items matching a `@runtime_checkable` protocol:

```python
from typing import Protocol, runtime_checkable
from typing_graph import MetadataCollection

@runtime_checkable
class HasValue(Protocol):
    value: int

@dataclass(frozen=True)
class Constraint:
    value: int

coll = MetadataCollection(_items=(Constraint(0), "doc"))
matches = coll.find_protocol(HasValue)
print(list(matches))  # [Constraint(value=0)]
```

## Transformation methods

### Combining collections

Use `+` or `|` to combine collections:

```python
from typing_graph import MetadataCollection

a = MetadataCollection(_items=(1, 2))
b = MetadataCollection(_items=(3, 4))

combined = a + b
print(list(combined))  # [1, 2, 3, 4]

# | operator works the same way
combined = a | b
print(list(combined))  # [1, 2, 3, 4]
```

### Excluding types

Use `exclude()` to remove items of specific types:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=("a", 1, "b", 2))
no_strings = coll.exclude(str)
print(list(no_strings))  # [1, 2]
```

### Removing duplicates

Use `unique()` to remove duplicate items:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=(1, 2, 1, 3, 2))
unique = coll.unique()
print(list(unique))  # [1, 2, 3]
```

The method preserves first occurrence order and handles unhashable items.

### Sorting

Use `sorted()` to sort items:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=(3, 1, 2))
sorted_coll = coll.sorted()
print(list(sorted_coll))  # [1, 2, 3]

# With custom key function
coll = MetadataCollection(_items=("bb", "a", "ccc"))
by_len = coll.sorted(key=len)
print(list(by_len))  # ['a', 'bb', 'ccc']
```

### Reversing

Use `reversed()` to reverse the order:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=(1, 2, 3))
rev = coll.reversed()
print(list(rev))  # [3, 2, 1]
```

### Mapping

Use `map()` to transform items. This is a terminal operation that returns a tuple:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=(1, 2, 3))
doubled = coll.map(lambda x: x * 2)
print(doubled)  # (2, 4, 6)
```

### Partitioning

Use `partition()` to split a collection by a predicate:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=(1, 2, 3, 4, 5))
evens, odds = coll.partition(lambda x: x % 2 == 0)
print(list(evens))  # [2, 4]
print(list(odds))   # [1, 3, 5]
```

## Introspection methods

### Getting unique types

Use `types()` to get the unique types in a collection:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=("a", 1, "b", 2.0))
types = coll.types()
print(sorted(t.__name__ for t in types))  # ['float', 'int', 'str']
```

### Grouping by type

Use `by_type()` to group items by their type:

```python
from typing_graph import MetadataCollection

coll = MetadataCollection(_items=("a", 1, "b", 2))
grouped = coll.by_type()
print(list(grouped[str]))  # ['a', 'b']
print(list(grouped[int]))  # [1, 2]
```

The returned mapping is immutable.

## See also

- [Metadata and annotated types](explanation/metadata.md) - Understanding how metadata flows through type graphs
- [Extracting metadata](guides/extracting-metadata.md) - Practical patterns for working with metadata
- [API reference](reference/api.md) - Complete API documentation
