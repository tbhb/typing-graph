# typing-graph

[![CI](https://github.com/tbhb/typing-graph/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/tbhb/typing-graph/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/typing-graph.svg)](https://pypi.org/project/typing-graph/)
[![codecov](https://codecov.io/gh/tbhb/typing-graph/branch/main/graph/badge.svg)](https://codecov.io/gh/tbhb/typing-graph)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)

A Python library for inspecting type annotations and building graph representations of type metadata.

> [!WARNING]
> This project is in early development. APIs may change without notice. Not yet recommended for production use.

typing-graph recursively unwraps `Annotated` types and [PEP 695][pep-695] type aliases, building a lazy, cached graph of metadata nodes. The library separates container-level metadata from element-level metadata and provides type-safe introspection of complex type hierarchies.

Built on [Pydantic's typing-inspection][typing-inspection] library and designed for compatibility with [annotated-types][annotated-types], typing-graph powers use cases like type conversion, validation, and feature flag extraction frameworks that derive behavior from type hints.

Inspired by the machinery behind Pydantic's model field metadata extraction, typing-graph generalizes this approach for arbitrary type annotations in classes (including dataclasses), `TypedDict`s, `NamedTuple`s, functions, and type aliases.

## Why I built this

After studying how projects like Pydantic, SQLAlchemy, and Typer derive behavior from type annotations, I became fascinated with the pattern and started experimenting with it in my own projects, and after writing similar introspection code across several of them, I decided to extract the common plumbing into a reusable library.

typing-graph provides a consistent graph representation that handles the edge cases of Python's typing system, so projects can focus on their domain logic instead of reinventing type introspection and metadata extraction.

## Features

- [x] **Comprehensive type introspection**: Inspect any Python type annotation and receive a structured, type-safe node representation
- [x] **Graph-based representation**: Every type node exposes a `children()` method for recursive traversal
- [x] **Metadata hoisting**: Automatically extract `Annotated` metadata and attach it to base types
- [x] **Qualifier extraction**: Detect `ClassVar`, `Final`, `Required`, `NotRequired`, `ReadOnly`, and `InitVar` qualifiers
- [x] **Caching**: Global cache for efficient repeated introspection
- [x] **Forward reference handling**: Configurable evaluation modes for forward references (eager, deferred, or stringified)
- [x] **Modern Python support**: [PEP 695][pep-695] type parameters, [PEP 696][pep-696] defaults, [PEP 647][pep-647] `TypeGuard`, [PEP 742][pep-742] `TypeIs`
- [x] **Structured type support**: `dataclass`, `TypedDict`, `NamedTuple`, `Protocol`, `Enum`
- [ ] **Metadata querying API**: Predicate-based filtering, type-based extraction, scoped queries
- [ ] **annotated-types integration**: `GroupedMetadata` flattening and convenience methods for constraint extraction
- [ ] **Type inspection controls**: Allowlists/blocklists, configurable depth boundaries
- [ ] **Graph traversal API**: Walk function, visitor pattern, path tracking
- [ ] **[attrs] support**: Field metadata, validators, converters
- [ ] **[Pydantic][pydantic] support**: Field metadata, validators, serializers

See the [roadmap](ROADMAP.md) for details on planned features.

## Installation

Requires Python 3.10 or later.

### pip

```bash
pip install typing-graph
```

### uv

```bash
uv add typing-graph
```

### Poetry

```bash
poetry add typing-graph
```

## Quick start

```python
from typing import Annotated
from typing_graph import inspect_type, ConcreteType, SubscriptedGeneric

# Inspect a simple type
node = inspect_type(int)
assert isinstance(node, ConcreteType)
assert node.cls is int

# Inspect a generic type with arguments
node = inspect_type(list[str])
assert isinstance(node, SubscriptedGeneric)
assert node.origin.cls is list
assert node.args[0].cls is str

# Inspect an Annotated type with metadata
node = inspect_type(Annotated[int, "positive"])
assert isinstance(node, ConcreteType)
assert node.cls is int
assert node.metadata == ("positive",)  # Metadata is hoisted to the base type
```

### Inspecting functions

```python
from typing_graph import inspect_function

def greet(name: str, times: int = 1) -> str:
    return name * times

func = inspect_function(greet)
print(func.name)  # "greet"
print(func.signature.parameters[0].name)  # "name"
print(func.signature.returns.cls)  # str
```

### Inspecting classes

```python
from dataclasses import dataclass
from typing_graph import inspect_class, DataclassType

@dataclass(frozen=True, slots=True)
class User:
    name: str
    age: int

node = inspect_class(User)
assert isinstance(node, DataclassType)
assert node.frozen is True
assert node.slots is True
assert len(node.fields) == 2
```

### Inspecting modules

```python
from typing_graph import inspect_module
import mymodule

types = inspect_module(mymodule)
print(types.classes)      # Dict of class names to inspection results
print(types.functions)    # Dict of function names to FunctionNodes
print(types.type_aliases) # Dict of type alias names to alias nodes
```

## Type node hierarchy

All type representations inherit from `TypeNode`, which provides:

- `source`: Optional source location where the type was defined
- `metadata`: Tuple of metadata from `Annotated` wrappers (when hoisted)
- `qualifiers`: Set of type qualifiers (`ClassVar`, `Final`, etc.)
- `children()`: Method returning child nodes for graph traversal

### Core type nodes

| Node                 | Represents                                               |
|----------------------|----------------------------------------------------------|
| `ConcreteType`       | Non-generic nominal types (`int`, `str`, custom classes) |
| `GenericTypeNode`    | Unsubscripted generics (`list`, `Dict`)                  |
| `SubscriptedGeneric` | Applied type arguments (`list[int]`, `Dict[str, T]`)     |
| `UnionType`          | Union types (`Union[A, B]`, `A \| B`)                    |
| `TupleType`          | Tuple types (heterogeneous and homogeneous)              |
| `CallableType`       | Callable types with parameter and return type info       |
| `AnnotatedType`      | `Annotated[T, ...]` when metadata is not hoisted         |

### Special forms

| Node                | Represents                          |
|---------------------|-------------------------------------|
| `AnyType`           | `typing.Any`                        |
| `NeverType`         | `typing.Never` / `typing.NoReturn`  |
| `SelfType`          | `typing.Self`                       |
| `LiteralNode`       | `Literal[...]` with specific values |
| `LiteralStringType` | `typing.LiteralString`              |

### Type variables

| Node               | Represents                                            |
|--------------------|-------------------------------------------------------|
| `TypeVarNode`      | Type variables with bounds, constraints, and variance |
| `ParamSpecNode`    | Parameter specification variables (PEP 612)           |
| `TypeVarTupleNode` | Variadic type variables (PEP 646)                     |

### Structured types

| Node                | Represents                           |
|---------------------|--------------------------------------|
| `DataclassType`     | Dataclasses with field metadata      |
| `TypedDictType`     | TypedDict with field definitions     |
| `NamedTupleType`    | NamedTuple with named fields         |
| `ProtocolType`      | Protocol with methods and attributes |
| `EnumType`          | Enum with typed members              |
| `AttrsType`         | attrs classes                        |
| `PydanticModelType` | Pydantic models                      |

## Configuration

Control inspection behavior with `InspectConfig`:

```python
from typing_graph import inspect_type, InspectConfig, EvalMode

config = InspectConfig(
    eval_mode=EvalMode.DEFERRED,  # How to handle forward references
    max_depth=50,                  # Maximum recursion depth
    hoist_metadata=True,           # Move Annotated metadata to base type
    include_source_locations=False, # Track where types are defined
)

node = inspect_type(SomeType, config=config)
```

### Forward reference evaluation modes

- `EvalMode.EAGER`: Fully resolve annotations; fail on errors
- `EvalMode.DEFERRED`: Use `ForwardRef` for unresolvable annotations (default)
- `EvalMode.STRINGIFIED`: Keep annotations as strings, resolve lazily

## Inspection functions

| Function                    | Purpose                                     |
|-----------------------------|---------------------------------------------|
| `inspect_type()`            | Inspect any type annotation                 |
| `inspect_function()`        | Inspect a function's signature and metadata |
| `inspect_signature()`       | Inspect a callable's signature              |
| `inspect_class()`           | Auto-detect and inspect a class             |
| `inspect_dataclass()`       | Inspect a dataclass specifically            |
| `inspect_enum()`            | Inspect an Enum specifically                |
| `inspect_module()`          | Discover all public types in a module       |
| `inspect_type_alias()`      | Inspect a type alias                        |
| `get_type_hints_for_node()` | Convert a node back to runtime type hints   |
| `cache_clear()`             | Clear the global inspection cache           |
| `cache_info()`              | Get cache statistics                        |

## Documentation

Full documentation is available at [typing-graph.tbhb.dev](https://typing-graph.tbhb.dev).

## Acknowledgments

This library is inspired by [Pydantic][pydantic]'s approach to type introspection and metadata extraction. typing-graph builds on Pydantic's [typing-inspection][typing-inspection] library for low-level type introspection.

## AI assistance

This project uses [Claude Code][claude-code] as a development tool. The core architecture, API design, and implementation are authored by the maintainer. All AI-generated contributions are reviewed, tested, and revised to meet project standards before being committed.

Claude Code has been used for:

- Rubber ducking and exploring design alternatives
- Drafting documentation and docstrings
- Generating test scaffolding and boilerplate
- Code cleanup and refactoring suggestions
- Researching Python typing edge cases

All contributions, regardless of origin, are reviewed and tested before inclusion.

## License

MIT License. See [LICENSE](LICENSE) for details.

[annotated-types]: https://github.com/annotated-types/annotated-types
[attrs]: https://www.attrs.org/
[claude-code]: https://code.claude.com/docs
[pep-647]: https://peps.python.org/pep-0647/
[pep-695]: https://peps.python.org/pep-0695/
[pep-696]: https://peps.python.org/pep-0696/
[pep-742]: https://peps.python.org/pep-0742/
[pydantic]: https://pydantic.dev
[typing-inspection]: https://typing-inspection.pydantic.dev/latest/
