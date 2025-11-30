# Working with metadata

In this tutorial, you'll create, query, and traverse [metadata collections](../reference/glossary.md#metadata-collection) attached to [type nodes](../reference/glossary.md#type-node). By the end, you'll have working code that constructs collections, searches for specific metadata types, and integrates with typing-graph's type inspection.

??? info "Prerequisites"
    Before starting, ensure you have:

    - Completed the [Your first type inspection](first-inspection.md) tutorial
    - Basic familiarity with `typing.Annotated`

    For background on how metadata hoisting works, see [Metadata and annotated types](../explanation/metadata.md).

## Step 1: Create the script file

Create a new file called `metadata_demo.py`:

```python title="metadata_demo.py"
from typing_graph import MetadataCollection

print("Ready to work with metadata")
```

Run the script:

```bash title="Terminal"
python metadata_demo.py
```

You should see:

```text title="Output"
Ready to work with metadata
```

## Step 2: Create a collection from a list

Use [`MetadataCollection.of()`][typing_graph.MetadataCollection.of] to create a collection from any iterable:

```python title="metadata_demo.py"
from typing_graph import MetadataCollection

# Create from a list
coll = MetadataCollection.of(["doc", 42, True])
print(f"Items: {list(coll)}")
print(f"Length: {len(coll)}")
```

Run the script:

```bash title="Terminal"
python metadata_demo.py
```

You should see:

```text title="Output"
Items: ['doc', 42, True]
Length: 3
```

## Step 3: Create a collection from different iterables

The `of()` method accepts any iterable:

```python title="metadata_demo.py"
from typing_graph import MetadataCollection

# Create from a tuple
coll1 = MetadataCollection.of(("a", "b", "c"))
print(f"From tuple: {list(coll1)}")

# Create from a generator
coll2 = MetadataCollection.of(x for x in range(3))
print(f"From generator: {list(coll2)}")
```

Run the script:

```bash title="Terminal"
python metadata_demo.py
```

You should see:

```text title="Output"
From tuple: ['a', 'b', 'c']
From generator: [0, 1, 2]
```

## Step 4: Use the EMPTY singleton

For efficiency, use the `EMPTY` singleton instead of creating new empty collections:

```python title="metadata_demo.py"
from typing_graph import MetadataCollection

# Use the singleton for empty collections
empty = MetadataCollection.EMPTY
print(f"Empty length: {len(empty)}")

# Empty iterables return the EMPTY singleton
also_empty = MetadataCollection.of([])
print(f"Same object: {also_empty is MetadataCollection.EMPTY}")
```

Run the script:

```bash title="Terminal"
python metadata_demo.py
```

You should see:

```text title="Output"
Empty length: 0
Same object: True
```

## Step 5: Extract metadata from an annotated type

Use [`MetadataCollection.from_annotated()`][typing_graph.MetadataCollection.from_annotated] to extract metadata directly from `Annotated` types:

```python title="metadata_demo.py"
from typing import Annotated

from typing_graph import MetadataCollection

# Extract metadata from Annotated
MyType = Annotated[int, "description", 42]
coll = MetadataCollection.from_annotated(MyType)
print(f"Metadata: {list(coll)}")

# Non-Annotated types return EMPTY
plain_coll = MetadataCollection.from_annotated(int)
print(f"Plain type returns EMPTY: {plain_coll is MetadataCollection.EMPTY}")
```

Run the script:

```bash title="Terminal"
python metadata_demo.py
```

You should see:

```text title="Output"
Metadata: ['description', 42]
Plain type returns EMPTY: True
```

!!! success "Checkpoint"
    At this point, you have:

    - Created metadata collections from lists, tuples, and generators
    - Used the `EMPTY` singleton for efficiency
    - Extracted metadata directly from `Annotated` types

## Step 6: Define metadata constraint classes

Create typed metadata classes that you'll use for querying:

```python title="metadata_demo.py"
from dataclasses import dataclass


@dataclass(frozen=True)
class Gt:
    value: int


@dataclass(frozen=True)
class Lt:
    value: int


print("Constraint classes defined")
```

Run the script:

```bash title="Terminal"
python metadata_demo.py
```

You should see:

```text title="Output"
Constraint classes defined
```

## Step 7: Create a collection with typed metadata

Build a collection containing your constraint instances:

```python title="metadata_demo.py"
from dataclasses import dataclass

from typing_graph import MetadataCollection


@dataclass(frozen=True)
class Gt:
    value: int


@dataclass(frozen=True)
class Lt:
    value: int


coll = MetadataCollection.of([Gt(0), Lt(100), Gt(10), "doc"])
print(f"Collection: {list(coll)}")
print(f"Length: {len(coll)}")
```

Run the script:

```bash title="Terminal"
python metadata_demo.py
```

You should see:

```text title="Output"
Collection: [Gt(value=0), Lt(value=100), Gt(value=10), 'doc']
Length: 4
```

## Step 8: Find the first item by type

Use [`find()`][typing_graph.MetadataCollection.find] to get the first item matching a specific type:

```python title="metadata_demo.py"
from dataclasses import dataclass

from typing_graph import MetadataCollection


@dataclass(frozen=True)
class Gt:
    value: int


@dataclass(frozen=True)
class Lt:
    value: int


coll = MetadataCollection.of([Gt(0), Lt(100), Gt(10), "doc"])

# Find first item of type
constraint = coll.find(Gt)
print(f"First Gt: {constraint}")

# Returns None if not found
missing = coll.find(float)
print(f"Missing type: {missing}")
```

Run the script:

```bash title="Terminal"
python metadata_demo.py
```

You should see:

```text title="Output"
First Gt: Gt(value=0)
Missing type: None
```

## Step 9: Find all items matching types

Use [`find_all()`][typing_graph.MetadataCollection.find_all] to get all items matching specific types:

```python title="metadata_demo.py"
from dataclasses import dataclass

from typing_graph import MetadataCollection


@dataclass(frozen=True)
class Gt:
    value: int


@dataclass(frozen=True)
class Lt:
    value: int


coll = MetadataCollection.of([Gt(0), Lt(100), Gt(10), "doc"])

# Find all items of a type
all_gt = coll.find_all(Gt)
print(f"All Gt: {list(all_gt)}")

# Find all items matching any of multiple types
constraints = coll.find_all(Gt, Lt)
print(f"All constraints: {list(constraints)}")
```

Run the script:

```bash title="Terminal"
python metadata_demo.py
```

You should see:

```text title="Output"
All Gt: [Gt(value=0), Gt(value=10)]
All constraints: [Gt(value=0), Lt(value=100), Gt(value=10)]
```

## Step 10: Check for presence with has()

Use [`has()`][typing_graph.MetadataCollection.has] to check if any item matches given types:

```python title="metadata_demo.py"
from dataclasses import dataclass

from typing_graph import MetadataCollection


@dataclass(frozen=True)
class Gt:
    value: int


coll = MetadataCollection.of([Gt(0), "doc", 42])

# Check for a single type
print(f"Has Gt: {coll.has(Gt)}")
print(f"Has float: {coll.has(float)}")

# Check for any of multiple types
print(f"Has float or list: {coll.has(float, list)}")
print(f"Has str or int: {coll.has(str, int)}")
```

Run the script:

```bash title="Terminal"
python metadata_demo.py
```

You should see:

```text title="Output"
Has Gt: True
Has float: False
Has float or list: False
Has str or int: True
```

!!! success "Checkpoint"
    At this point, you have:

    - Created typed metadata constraint classes
    - Found items by type using `find()` and `find_all()`
    - Checked for presence using `has()`

## Step 11: Inspect a type with metadata

Combine metadata collections with type inspection:

```python title="metadata_demo.py"
from dataclasses import dataclass
from typing import Annotated

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
meta = node.metadata

# Work with metadata using familiar Python patterns
print(f"Length: {len(meta)}")
print(f"Items: {list(meta)}")
print(f"Contains Gt(0): {Gt(0) in meta}")
```

Run the script:

```bash title="Terminal"
python metadata_demo.py
```

You should see:

```text title="Output"
Length: 3
Items: [Gt(value=0), Lt(value=100), 'A positive integer less than 100']
Contains Gt(0): True
```

## Step 12: Query metadata from a type node

Use the collection methods on the node's metadata:

```python title="metadata_demo.py"
from dataclasses import dataclass
from typing import Annotated

from typing_graph import inspect_type


@dataclass(frozen=True)
class Gt:
    value: int


@dataclass(frozen=True)
class Lt:
    value: int


BoundedInt = Annotated[int, Gt(0), Lt(100), "A positive integer less than 100"]

node = inspect_type(BoundedInt)
meta = node.metadata

# Query specific types
constraint = meta.find(Gt)
print(f"First Gt constraint: {constraint}")

# Check what types exist
print(f"Has string: {meta.has(str)}")
```

Run the script:

```bash title="Terminal"
python metadata_demo.py
```

You should see:

```text title="Output"
First Gt constraint: Gt(value=0)
Has string: True
```

## Step 13: Inspect nested types with layered metadata

Metadata can exist at different levels in nested types. typing-graph preserves this distinction:

```python title="metadata_demo.py"
from dataclasses import dataclass
from typing import Annotated

from typing_graph import inspect_type


@dataclass(frozen=True)
class MinValue:
    value: int


@dataclass(frozen=True)
class MaxItems:
    limit: int


# Container-level metadata on list, element-level on int
scores_type = Annotated[list[Annotated[int, MinValue(0)]], MaxItems(100)]
node = inspect_type(scores_type)

# The outer list carries container-level metadata
print(f"List metadata: {list(node.metadata)}")

# The inner int carries element-level metadata
int_node = node.args[0]
print(f"Element metadata: {list(int_node.metadata)}")
```

Run the script:

```bash title="Terminal"
python metadata_demo.py
```

You should see:

```text title="Output"
List metadata: [MaxItems(limit=100)]
Element metadata: [MinValue(value=0)]
```

!!! success "Checkpoint"
    You've completed this tutorial. You can now:

    - Create metadata collections from iterables and `Annotated` types
    - Query metadata by type using `find()`, `find_all()`, and `has()`
    - Access metadata from inspected type nodes
    - Traverse nested types with layered metadata

## Summary

You've learned how to work with [`MetadataCollection`][typing_graph.MetadataCollection], the immutable container that holds metadata on every type node. The key methods are:

- `MetadataCollection.of()` creates a collection from any iterable
- `MetadataCollection.from_annotated()` extracts metadata from `Annotated` types
- `find()` returns the first item of a type
- `find_all()` returns all items matching types
- `has()` checks for the presence of types

!!! tip "Next steps"
    Now that you understand metadata basics, explore:

    - [Querying metadata](../guides/metadata-queries.md) - Advanced query patterns
    - [Filtering metadata](../guides/metadata-filtering.md) - Predicate and protocol-based filtering
    - [Transforming metadata](../guides/metadata-transformations.md) - Combining, sorting, and mapping collections
    - [Metadata and annotated types](../explanation/metadata.md) - Deep dive into metadata hoisting
