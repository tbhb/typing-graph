# Qualifiers

This page explains type qualifiers, which are special typing constructs that change how the type system interprets an annotation. Understanding qualifiers is essential for accurately inspecting classes with special field behaviors.

## Why qualifiers exist

Type annotations typically describe what values a name can hold. But sometimes you need to express extra constraints about how a value is used: "this field belongs to the class, not instances," "this value can't be reassigned," or "this TypedDict key is optional."

Python's type system handles these through qualifiers, which are special wrappers that change the meaning of the underlying type. A `ClassVar[int]` is still an `int`, but it has different semantics than a plain `int` field.

Qualifiers are distinct from metadata (attached via `Annotated`) in an important way: qualifiers have meanings defined by the language and type checkers, while metadata can be anything. A type checker knows what `Final` means; it has no idea what your custom `MaxLen(100)` constraint means.

typing-graph extracts qualifiers during inspection, making them available on each node so your tools can handle qualified types correctly.

## What are qualifiers?

Qualifiers are type-system constructs that wrap another type to signal special semantics. Unlike metadata (which adds arbitrary information), qualifiers have specific meanings defined by Python's type system:

| Qualifier | Meaning |
| --------- | ------- |
| `ClassVar` | Attribute belongs to the class, not instances |
| `Final` | Code cannot reassign the value after initialization |
| `Required` | TypedDict key must be present |
| `NotRequired` | Callers may omit this TypedDict key |
| `ReadOnly` | Code cannot mutate this TypedDict value |
| `InitVar` | Dataclass field used only during `__init__` |

## Where qualifiers are valid

Each qualifier is only valid in certain contexts:

| Context | Valid qualifiers |
| ------- | ---------------- |
| Class attributes | `ClassVar`, `Final` |
| Dataclass fields | `ClassVar`, `Final`, `InitVar` |
| TypedDict fields | `Required`, `NotRequired`, `ReadOnly` |
| NamedTuple fields | None |
| Function parameters | None (though `Final` is sometimes used) |

Using a qualifier in the wrong context typically produces a type error that static analyzers flag.

## How typing-graph handles qualifiers

typing-graph uses [typing-inspection](https://typing-inspection.pydantic.dev/) to extract qualifiers from type annotations. The library unwraps the qualifier and stores it in the node's [`qualifiers`][typing_graph.TypeNode] frozenset. Use [`inspect_dataclass()`][typing_graph.inspect_dataclass] to inspect dataclasses:

```python
from dataclasses import dataclass
from typing import ClassVar, Final
from typing_graph import inspect_dataclass

@dataclass
class Config:
    debug: ClassVar[bool] = False
    version: Final[str] = "1.0"
    name: str = "default"

result = inspect_dataclass(Config)

for field in result.fields:
    print(f"{field.name}: {field.type.qualifiers}")

# debug: frozenset({'class_var'})
# version: frozenset({'final'})
# name: frozenset()
```

### Qualifier values

The `qualifiers` frozenset contains string literals:

- `'class_var'` - from `ClassVar[T]`
- `'final'` - from `Final[T]`
- `'required'` - from `Required[T]`
- `'not_required'` - from `NotRequired[T]`
- `'read_only'` - from `ReadOnly[T]`
- `'init_var'` - from `InitVar[T]`

!!! note "Design trade-off: strings vs enums"

    You might wonder why qualifiers are stored as strings rather than a proper enum. The answer lies in compatibility and extensibility.

    Python's typing module continues to evolve, potentially adding new qualifiers in future versions. Using strings allows typing-graph to work with qualifiers that didn't exist when the library was written. The strings come directly from typing-inspection, which tracks Python's evolution.

    The trade-off is less type safety in user code. You can write `'class_var'` wrong and Python won't catch it until runtime. The `Qualifier` type alias (a `Literal` type) helps type checkers catch these errors, but only if you use it consistently.

### Importing the qualifier type

The `Qualifier` type alias for type checking comes from typing-inspection:

```python
from typing_inspection.introspection import Qualifier
```

`Qualifier` is a `Literal` type containing the valid qualifier strings. Use it when you need to type-annotate code that works with qualifiers:

```python
from typing_inspection.introspection import Qualifier

def has_qualifier(qualifiers: frozenset[Qualifier], name: Qualifier) -> bool:
    return name in qualifiers
```

## Comparing qualifiers and metadata

Qualifiers and metadata serve different purposes:

| Aspect | Qualifiers | Metadata |
| ------ | ---------- | -------- |
| Source | Python typing module | `Annotated[T, ...]` |
| Purpose | Type-system semantics | Arbitrary information |
| Extraction | Automatic unwrapping | Via `Annotated` |
| Storage | `qualifiers` frozenset | `metadata` tuple |
| Values | Fixed set of strings | Any Python objects |

You can have both on the same type:

```python
from typing import Annotated, Final
from typing_graph import inspect_type

# Final qualifier + metadata
node = inspect_type(Annotated[Final[str], "version string"])
print(node.qualifiers)  # frozenset({'final'})
print(node.metadata)    # ('version string',)
```

## Working with qualifiers

### Checking for specific qualifiers

```python
from typing import ClassVar
from typing_graph import inspect_type

node = inspect_type(ClassVar[int])

if 'class_var' in node.qualifiers:
    print("This is a class variable")
```

### Filtering fields by qualifier

```python
# snippet - illustrative pattern (MyClass from previous example)
from typing_graph import inspect_dataclass

result = inspect_dataclass(MyClass)

# Find all Final fields
final_fields = [
    f for f in result.fields
    if 'final' in f.type.qualifiers
]

# Find all instance variables (no ClassVar)
instance_fields = [
    f for f in result.fields
    if 'class_var' not in f.type.qualifiers
]
```

### Handling required and optional fields in TypedDict

Use [`inspect_typed_dict()`][typing_graph.inspect_typed_dict] to inspect TypedDict classes:

```python
from typing import TypedDict
from typing_extensions import Required, NotRequired
from typing_graph import inspect_typed_dict

class User(TypedDict, total=False):
    id: Required[int]
    name: str
    email: NotRequired[str]

result = inspect_typed_dict(User)

for field in result.fields:
    if 'required' in field.type.qualifiers:
        print(f"{field.name} is required")
    elif 'not_required' in field.type.qualifiers:
        print(f"{field.name} is explicitly optional")
    else:
        print(f"{field.name} follows total= default")
```

## Qualifier nesting

You can sometimes combine qualifiers on the same annotation, though this is rarely useful:

```python
from typing import ClassVar, Final
from typing_graph import inspect_type

# Multiple qualifiers on one annotation
node = inspect_type(Final[int])
print(node.qualifiers)  # frozenset({'final'})
```

typing-graph extracts all qualifiers from an annotation.

## The evolution of qualifiers

Python's qualifier vocabulary has grown over time as the type system matured:

??? info "Historical context"

    - **ClassVar** (PEP 526, Python 3.5.3): The first qualifier, distinguishing class attributes from instance attributes
    - **Final** (PEP 591, Python 3.8): Marked values as non-reassignable
    - **Required/NotRequired** (PEP 655, Python 3.11): Made TypedDict field optionality explicit
    - **ReadOnly** (PEP 705, Python 3.13): Added read-only TypedDict fields
    - **InitVar** (part of dataclasses, Python 3.7): Special handling for dataclass initialization

    This evolution shows Python's type system becoming more expressive over time. Each qualifier addresses a specific pattern that previous typing features couldn't express. typing-graph's integration with typing-inspection ensures it stays current with new qualifiers as Python evolves.

## Practical application

Now that you understand qualifiers, apply this knowledge:

- **Inspect classes with qualifiers** in [Inspecting structured types](../tutorials/structured-types.md)
- **Filter fields by qualifier** when [Walking the type graph](../guides/walking-type-graph.md)

## See also

- [typing-inspection documentation](https://typing-inspection.pydantic.dev/) - The library typing-graph uses for qualifier extraction
- [Metadata and Annotated types](metadata.md) - How metadata differs from qualifiers
- [Architecture overview](architecture.md) - How qualifier extraction fits into the inspection process
- [Type qualifier](../reference/glossary.md#type-qualifier) - Glossary definition
- [PEP 526](https://peps.python.org/pep-0526/) - Syntax for variable annotations (ClassVar)
- [PEP 591](https://peps.python.org/pep-0591/) - Adding a final qualifier to typing
- [PEP 655](https://peps.python.org/pep-0655/) - Marking individual TypedDict items as required or not-required
- [PEP 705](https://peps.python.org/pep-0705/) - TypedDict read-only items
