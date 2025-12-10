# Traversing type graphs

In this tutorial, you'll build a constraint collector that finds all validation constraints in nested type annotations. By the end, you'll have a reusable function that traverses type graphs using [`walk()`][typing_graph.walk] and collects metadata from any depth.

??? info "Prerequisites"
    Before starting, ensure you have:

    - Completed the [Your first type inspection](first-inspection.md) tutorial
    - Completed the [Working with metadata](working-with-metadata.md) tutorial
    - Basic familiarity with Python dataclasses

    You don't need prior experience with graph traversal.

## Step 1: Create the script file

Create a new file called `collect_constraints.py`:

```python title="collect_constraints.py"
from typing_graph import inspect_type

print("Ready to collect constraints")
```

Run the script:

```bash title="Terminal"
python collect_constraints.py
```

You should see:

```text title="Output"
Ready to collect constraints
```

## Step 2: Define constraint classes

Add dataclass definitions for the constraints you'll collect:

```python title="collect_constraints.py"
from dataclasses import dataclass

from typing_graph import inspect_type


@dataclass(frozen=True)
class Gt:
    """Value must be greater than this threshold."""

    value: int


@dataclass(frozen=True)
class Lt:
    """Value must be less than this threshold."""

    value: int


@dataclass(frozen=True)
class MaxLen:
    """String or collection must not exceed this length."""

    value: int


print("Constraint classes defined")
```

Run the script:

```bash title="Terminal"
python collect_constraints.py
```

You should see:

```text title="Output"
Constraint classes defined
```

## Step 3: Create a nested annotated type

Add a type with constraints at multiple levels:

```python title="collect_constraints.py"
from dataclasses import dataclass
from typing import Annotated

from typing_graph import inspect_type


@dataclass(frozen=True)
class Gt:
    """Value must be greater than this threshold."""

    value: int


@dataclass(frozen=True)
class Lt:
    """Value must be less than this threshold."""

    value: int


@dataclass(frozen=True)
class MaxLen:
    """String or collection must not exceed this length."""

    value: int


# Nested type with constraints at different levels
Score = Annotated[int, Gt(0), Lt(100)]
Username = Annotated[str, MaxLen(50)]
Scores = Annotated[list[Score], MaxLen(10)]

# Complex nested type combining them
UserScores = dict[Username, Scores]

print(f"Type: {UserScores}")
```

Run the script:

```bash title="Terminal"
python collect_constraints.py
```

You should see output showing the nested type structure:

```text title="Output"
Type: dict[typing.Annotated[str, MaxLen(value=50)], typing.Annotated[list[typing.Annotated[int, Gt(value=0), Lt(value=100)]], MaxLen(value=10)]]
```

## Step 4: Inspect the root node

Add code to get the root type node:

```python title="collect_constraints.py"
from dataclasses import dataclass
from typing import Annotated

from typing_graph import inspect_type


@dataclass(frozen=True)
class Gt:
    """Value must be greater than this threshold."""

    value: int


@dataclass(frozen=True)
class Lt:
    """Value must be less than this threshold."""

    value: int


@dataclass(frozen=True)
class MaxLen:
    """String or collection must not exceed this length."""

    value: int


# Nested type with constraints at different levels
Score = Annotated[int, Gt(0), Lt(100)]
Username = Annotated[str, MaxLen(50)]
Scores = Annotated[list[Score], MaxLen(10)]

# Complex nested type combining them
UserScores = dict[Username, Scores]

# Inspect the type
node = inspect_type(UserScores)
print(f"Root node type: {type(node).__name__}")
print(f"Root class: {node.origin.cls.__name__}")
```

Run the script:

```bash title="Terminal"
python collect_constraints.py
```

You should see:

```text title="Output"
Root node type: SubscriptedGenericNode
Root class: dict
```

!!! success "Checkpoint"
    At this point, you have:

    - Created constraint dataclasses (`Gt`, `Lt`, `MaxLen`)
    - Built a nested type with constraints at multiple levels
    - Inspected the root node of the type graph

## Step 5: Traverse with walk()

Import `walk` and iterate over all nodes in the type graph:

```python title="collect_constraints.py"
from dataclasses import dataclass
from typing import Annotated

from typing_graph import inspect_type, walk


@dataclass(frozen=True)
class Gt:
    """Value must be greater than this threshold."""

    value: int


@dataclass(frozen=True)
class Lt:
    """Value must be less than this threshold."""

    value: int


@dataclass(frozen=True)
class MaxLen:
    """String or collection must not exceed this length."""

    value: int


# Nested type with constraints at different levels
Score = Annotated[int, Gt(0), Lt(100)]
Username = Annotated[str, MaxLen(50)]
Scores = Annotated[list[Score], MaxLen(10)]

# Complex nested type combining them
UserScores = dict[Username, Scores]

# Inspect and traverse
node = inspect_type(UserScores)

print("Traversing all nodes:")
for visited in walk(node):
    print(f"  {type(visited).__name__}")
```

Run the script:

```bash title="Terminal"
python collect_constraints.py
```

You should see all nodes in the type graph:

```text title="Output"
Traversing all nodes:
  SubscriptedGenericNode
  GenericTypeNode
  ConcreteNode
  SubscriptedGenericNode
  GenericTypeNode
  ConcreteNode
```

The `walk()` function performs depth-first traversal, visiting each unique node exactly once.

## Step 6: Filter nodes with metadata

Use a predicate to filter to only concrete nodes that have metadata. Constraints are attached to the underlying concrete types (like `int` or `str`), not to container types, so we filter to `ConcreteNode` using the `is_concrete_node` type guard:

```python title="collect_constraints.py"
from dataclasses import dataclass
from typing import Annotated

from typing_extensions import TypeIs

from typing_graph import ConcreteNode, TypeNode, inspect_type, is_concrete_node, walk


@dataclass(frozen=True)
class Gt:
    """Value must be greater than this threshold."""

    value: int


@dataclass(frozen=True)
class Lt:
    """Value must be less than this threshold."""

    value: int


@dataclass(frozen=True)
class MaxLen:
    """String or collection must not exceed this length."""

    value: int


def is_concrete_with_metadata(n: TypeNode) -> TypeIs[ConcreteNode]:
    """Check if a node is concrete and has metadata."""
    return is_concrete_node(n) and len(n.metadata) > 0


# Nested type with constraints at different levels
Score = Annotated[int, Gt(0), Lt(100)]
Username = Annotated[str, MaxLen(50)]
Scores = Annotated[list[Score], MaxLen(10)]

# Complex nested type combining them
UserScores = dict[Username, Scores]

# Inspect and filter
node = inspect_type(UserScores)

print("Nodes with metadata:")
for visited in walk(node, predicate=is_concrete_with_metadata):
    print(f"  {visited.cls.__name__}: {list(visited.metadata)}")
```

Run the script:

```bash title="Terminal"
python collect_constraints.py
```

You should see only the concrete nodes that have constraints:

```text title="Output"
Nodes with metadata:
  str: [MaxLen(value=50)]
  int: [Gt(value=0), Lt(value=100)]
```

!!! note "Why filter to concrete nodes?"
    Only `ConcreteNode` has a direct `cls` attribute. Other node types like `SubscriptedGenericNode` access the class through `origin.cls`. By filtering to concrete nodes, we get clean access to `visited.cls` and find the types where constraints are actually attached.

## Step 7: Collect specific constraint types

Extract only the constraint types you care about, filtering to concrete nodes:

```python title="collect_constraints.py"
from dataclasses import dataclass
from typing import Annotated

from typing_extensions import TypeIs

from typing_graph import ConcreteNode, TypeNode, inspect_type, is_concrete_node, walk


@dataclass(frozen=True)
class Gt:
    """Value must be greater than this threshold."""

    value: int


@dataclass(frozen=True)
class Lt:
    """Value must be less than this threshold."""

    value: int


@dataclass(frozen=True)
class MaxLen:
    """String or collection must not exceed this length."""

    value: int


def is_concrete_with_metadata(n: TypeNode) -> TypeIs[ConcreteNode]:
    """Check if a node is concrete and has metadata."""
    return is_concrete_node(n) and len(n.metadata) > 0


# Nested type with constraints at different levels
Score = Annotated[int, Gt(0), Lt(100)]
Username = Annotated[str, MaxLen(50)]
Scores = Annotated[list[Score], MaxLen(10)]

# Complex nested type combining them
UserScores = dict[Username, Scores]

# Inspect and collect
node = inspect_type(UserScores)

print("Collecting constraints:")
for visited in walk(node, predicate=is_concrete_with_metadata):
    for meta in visited.metadata:
        if isinstance(meta, Gt):
            print(f"  {visited.cls.__name__} > {meta.value}")
        elif isinstance(meta, Lt):
            print(f"  {visited.cls.__name__} < {meta.value}")
        elif isinstance(meta, MaxLen):
            print(f"  {visited.cls.__name__} max length: {meta.value}")
```

Run the script:

```bash title="Terminal"
python collect_constraints.py
```

You should see the constraints formatted:

```text title="Output"
Collecting constraints:
  str max length: 50
  int > 0
  int < 100
```

!!! success "Checkpoint"
    At this point, you have:

    - Used `walk()` to traverse all nodes in a type graph
    - Filtered nodes using a predicate function
    - Extracted specific constraint types from metadata

## Step 8: Build a reusable collector function

Combine the logic into a reusable function that filters to concrete nodes:

```python title="collect_constraints.py"
from dataclasses import dataclass
from typing import Annotated

from typing_graph import TypeNode, inspect_type, is_concrete_node, walk


@dataclass(frozen=True)
class Gt:
    """Value must be greater than this threshold."""

    value: int


@dataclass(frozen=True)
class Lt:
    """Value must be less than this threshold."""

    value: int


@dataclass(frozen=True)
class MaxLen:
    """String or collection must not exceed this length."""

    value: int


def collect_constraints(
    node: TypeNode,
) -> list[tuple[type, Gt | Lt | MaxLen]]:
    """Collect all Gt, Lt, and MaxLen constraints from a type graph.

    Returns a list of (type, constraint) tuples for concrete types only.
    """
    constraints: list[tuple[type, Gt | Lt | MaxLen]] = []
    for visited in walk(node):
        if is_concrete_node(visited):
            for meta in visited.metadata:
                if isinstance(meta, (Gt, Lt, MaxLen)):
                    constraints.append((visited.cls, meta))
    return constraints


# Test the collector
Score = Annotated[int, Gt(0), Lt(100)]
Username = Annotated[str, MaxLen(50)]
Scores = Annotated[list[Score], MaxLen(10)]
UserScores = dict[Username, Scores]

node = inspect_type(UserScores)
results = collect_constraints(node)

print("Collected constraints:")
for cls, constraint in results:
    print(f"  {cls.__name__}: {constraint}")
```

Run the script:

```bash title="Terminal"
python collect_constraints.py
```

You should see:

```text title="Output"
Collected constraints:
  str: MaxLen(value=50)
  int: Gt(value=0)
  int: Lt(value=100)
```

## Step 9: Limit traversal depth

Use `max_depth` to control how deep the traversal goes:

```python title="collect_constraints.py"
from dataclasses import dataclass
from typing import Annotated

from typing_graph import TypeNode, inspect_type, is_concrete_node, walk


@dataclass(frozen=True)
class Gt:
    """Value must be greater than this threshold."""

    value: int


@dataclass(frozen=True)
class Lt:
    """Value must be less than this threshold."""

    value: int


@dataclass(frozen=True)
class MaxLen:
    """String or collection must not exceed this length."""

    value: int


def collect_constraints(
    node: TypeNode,
    max_depth: int | None = None,
) -> list[tuple[type, Gt | Lt | MaxLen]]:
    """Collect all Gt, Lt, and MaxLen constraints from a type graph.

    Args:
        node: The root node to start traversal from.
        max_depth: Maximum depth to traverse. None means no limit.

    Returns a list of (type, constraint) tuples for concrete types only.
    """
    constraints: list[tuple[type, Gt | Lt | MaxLen]] = []
    for visited in walk(node, max_depth=max_depth):
        if is_concrete_node(visited):
            for meta in visited.metadata:
                if isinstance(meta, (Gt, Lt, MaxLen)):
                    constraints.append((visited.cls, meta))
    return constraints


# Test depth limiting
Score = Annotated[int, Gt(0), Lt(100)]
Username = Annotated[str, MaxLen(50)]
Scores = Annotated[list[Score], MaxLen(10)]
UserScores = dict[Username, Scores]

node = inspect_type(UserScores)

print("Depth 1 (immediate children only):")
for cls, constraint in collect_constraints(node, max_depth=1):
    print(f"  {cls.__name__}: {constraint}")

print("\nFull depth (all constraints):")
for cls, constraint in collect_constraints(node):
    print(f"  {cls.__name__}: {constraint}")
```

Run the script:

```bash title="Terminal"
python collect_constraints.py
```

You should see fewer constraints at limited depth:

```text title="Output"
Depth 1 (immediate children only):
  str: MaxLen(value=50)

Full depth (all constraints):
  str: MaxLen(value=50)
  int: Gt(value=0)
  int: Lt(value=100)
```

With `max_depth=1`, only the `Username` (str) constraint is found at depth 1. The `Score` (int) constraints are deeper in the graph and are skipped.

!!! success "Checkpoint"
    At this point, you have:

    - Built a reusable `collect_constraints()` function
    - Added depth limiting with the `max_depth` parameter
    - Understood how depth affects traversal results

## Step 10: Apply to complex types

Test your collector with different complex types:

```python title="collect_constraints.py"
from dataclasses import dataclass
from typing import Annotated, Callable

from typing_graph import TypeNode, inspect_type, is_concrete_node, walk


@dataclass(frozen=True)
class Gt:
    """Value must be greater than this threshold."""

    value: int


@dataclass(frozen=True)
class Lt:
    """Value must be less than this threshold."""

    value: int


@dataclass(frozen=True)
class MaxLen:
    """String or collection must not exceed this length."""

    value: int


def collect_constraints(
    node: TypeNode,
    max_depth: int | None = None,
) -> list[tuple[type, Gt | Lt | MaxLen]]:
    """Collect all Gt, Lt, and MaxLen constraints from a type graph."""
    constraints: list[tuple[type, Gt | Lt | MaxLen]] = []
    for visited in walk(node, max_depth=max_depth):
        if is_concrete_node(visited):
            for meta in visited.metadata:
                if isinstance(meta, (Gt, Lt, MaxLen)):
                    constraints.append((visited.cls, meta))
    return constraints


# Test with a Callable type
PositiveInt = Annotated[int, Gt(0)]
BoundedStr = Annotated[str, MaxLen(100)]
ProcessorFunc = Callable[[PositiveInt, BoundedStr], PositiveInt]

node = inspect_type(ProcessorFunc)
print("Callable type constraints:")
for cls, constraint in collect_constraints(node):
    print(f"  {cls.__name__}: {constraint}")
```

Run the script:

```bash title="Terminal"
python collect_constraints.py
```

You should see constraints from parameters and return type:

```text title="Output"
Callable type constraints:
  int: Gt(value=0)
  str: MaxLen(value=100)
  int: Gt(value=0)
```

The `Gt(0)` constraint appears twice because `PositiveInt` is used for both a parameter and the return type.

## Step 11: Create a formatted report

Add a function to generate a readable constraint report:

```python title="collect_constraints.py"
from dataclasses import dataclass
from typing import Annotated

from typing_graph import TypeNode, inspect_type, is_concrete_node, walk


@dataclass(frozen=True)
class Gt:
    """Value must be greater than this threshold."""

    value: int


@dataclass(frozen=True)
class Lt:
    """Value must be less than this threshold."""

    value: int


@dataclass(frozen=True)
class MaxLen:
    """String or collection must not exceed this length."""

    value: int


def collect_constraints(
    node: TypeNode,
    max_depth: int | None = None,
) -> list[tuple[type, Gt | Lt | MaxLen]]:
    """Collect all Gt, Lt, and MaxLen constraints from a type graph."""
    constraints: list[tuple[type, Gt | Lt | MaxLen]] = []
    for visited in walk(node, max_depth=max_depth):
        if is_concrete_node(visited):
            for meta in visited.metadata:
                if isinstance(meta, (Gt, Lt, MaxLen)):
                    constraints.append((visited.cls, meta))
    return constraints


def format_constraint_report(constraints: list[tuple[type, Gt | Lt | MaxLen]]) -> str:
    """Format constraints as a readable report."""
    if not constraints:
        return "No constraints found."

    lines = ["Validation constraints:", ""]
    for cls, constraint in constraints:
        if isinstance(constraint, Gt):
            lines.append(f"  - {cls.__name__} must be > {constraint.value}")
        elif isinstance(constraint, Lt):
            lines.append(f"  - {cls.__name__} must be < {constraint.value}")
        elif isinstance(constraint, MaxLen):
            lines.append(f"  - {cls.__name__} max length: {constraint.value}")

    return "\n".join(lines)


# Generate a report
Score = Annotated[int, Gt(0), Lt(100)]
Username = Annotated[str, MaxLen(50)]
Scores = Annotated[list[Score], MaxLen(10)]
UserScores = dict[Username, Scores]

node = inspect_type(UserScores)
constraints = collect_constraints(node)
print(format_constraint_report(constraints))
```

Run the script:

```bash title="Terminal"
python collect_constraints.py
```

You should see a formatted report:

```text title="Output"
Validation constraints:

  - str max length: 50
  - int must be > 0
  - int must be < 100
```

!!! success "Checkpoint"
    You've completed this tutorial. You can now:

    - Traverse type graphs using `walk()`
    - Filter nodes with predicate functions
    - Collect metadata from nested types at any depth
    - Control traversal depth with `max_depth`
    - Build reusable functions for metadata collection

## Summary

You've built a constraint collector that traverses type graphs and extracts validation metadata. The key functions are:

- [`walk()`][typing_graph.walk] iterates over all nodes in a type graph
- The `predicate` parameter filters which nodes are yielded
- The `max_depth` parameter limits how deep traversal goes
- `node.metadata` provides access to `Annotated` metadata on any node

!!! tip "Next steps"
    Now that you can traverse type graphs, explore:

    - [How to filter type graphs with walk()](../guides/filtering-with-walk.md) - Advanced predicate patterns including TypeIs narrowing
    - [Walking the type graph](../guides/walking-type-graph.md) - Manual traversal with `children()`
    - [Metadata queries](../guides/metadata-queries.md) - Advanced metadata querying patterns
