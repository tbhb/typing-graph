# typing-graph

[![CI](https://github.com/tbhb/typing-graph/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/tbhb/typing-graph/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/typing-graph.svg)](https://pypi.org/project/typing-graph/)
[![codecov](https://codecov.io/gh/tbhb/typing-graph/branch/main/graph/badge.svg)](https://codecov.io/gh/tbhb/typing-graph)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)

typing-graph is a building block for Python libraries and frameworks that derive runtime behavior from type annotations. If you're building validation frameworks, CLI tools, serializers, ORMs, or similar tools that inspect types to generate code or configure behavior, typing-graph provides the structured type introspection layer so you can focus on your domain logic.

> [!WARNING]
> This project is in early development. APIs may change without notice. Not yet recommended for production use.

Pass any type (generics, `Annotated`, dataclasses, `TypedDict`, [PEP 695][pep-695] aliases) and get back a graph of nodes representing the type structure and its metadata. The library handles metadata hoisting (extracting annotations from `Annotated` wrappers), qualifier detection (`ClassVar`, `Final`, `Required`), forward reference resolution, and caching. Each node exposes a `children()` method for recursive traversal.

Built on [Pydantic's typing-inspection][typing-inspection] library and designed for compatibility with [annotated-types][annotated-types].

## Why I built this

After studying how projects like Pydantic, SQLAlchemy, and Typer derive behavior from type annotations, I became fascinated with the pattern and started experimenting with it in my own projects, and after writing similar introspection code across many of them, I decided to extract the common plumbing into a reusable library.

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

See the [roadmap](https://typing-graph.tbhb.dev/roadmap/) for details on planned features.

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

```pycon
>>> from typing import Annotated
>>> from dataclasses import dataclass
>>> from typing_graph import inspect_type

>>> # Define constraint metadata (like you might in a validation framework)
>>> @dataclass
... class Pattern:
...     regex: str

>>> @dataclass
... class MinLen:
...     value: int

>>> # Define a reusable annotated type alias
>>> URL = Annotated[str, Pattern(r"^https?://")]

>>> # Build a complex nested type
>>> Urls = Annotated[list[URL], MinLen(1)]

>>> # Inspect the type graph
>>> node = inspect_type(Urls)
>>> node  # doctest: +SKIP
SubscriptedGenericNode(metadata=(MinLen(value=1),), origin=GenericTypeNode(cls=list), args=(ConcreteNode(metadata=(Pattern(regex='^https?://'),), cls=str),))

>>> # The outer node is a SubscriptedGenericNode (list) with container-level metadata
>>> node.origin.cls
<class 'list'>
>>> node.metadata
(MinLen(value=1),)

>>> # Traverse to the element type - it carries its own metadata
>>> element = node.args[0]
>>> element.cls
<class 'str'>
>>> element.metadata
(Pattern(regex='^https?://'),)

```

Each node in the graph carries its own metadata, enabling frameworks to apply different validation or transformation logic at each level of the type structure.

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
from typing_graph import inspect_class, DataclassNode

@dataclass(frozen=True, slots=True)
class User:
    name: str
    age: int

node = inspect_class(User)
assert isinstance(node, DataclassNode)
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

- `source`: Optional source location where the code defines the type
- `metadata`: Tuple of metadata from `Annotated` wrappers (when hoisted)
- `qualifiers`: Set of type qualifiers (`ClassVar`, `Final`, etc.)
- `children()`: Method returning child nodes for graph traversal

### Core type nodes

| Node                    | Represents                                               |
|-------------------------|----------------------------------------------------------|
| `ConcreteNode`          | Non-generic nominal types (`int`, `str`, custom classes) |
| `GenericTypeNode`       | Unsubscripted generics (`list`, `Dict`)                  |
| `SubscriptedGenericNode`| Applied type arguments (`list[int]`, `Dict[str, T]`)     |
| `UnionNode`             | Union types (`Union[A, B]`, `A \| B`)                    |
| `TupleNode`             | Tuple types (heterogeneous and homogeneous)              |
| `CallableNode`          | Callable types with parameter and return type info       |
| `AnnotatedNode`         | `Annotated[T, ...]` when metadata is not hoisted         |

### Special forms

| Node                  | Represents                          |
|-----------------------|-------------------------------------|
| `AnyNode`             | `typing.Any`                        |
| `NeverNode`           | `typing.Never` / `typing.NoReturn`  |
| `SelfNode`            | `typing.Self`                       |
| `LiteralNode`         | `Literal[...]` with specific values |
| `LiteralStringNode`   | `typing.LiteralString`              |

### Type variables

| Node               | Represents                                            |
|--------------------|-------------------------------------------------------|
| `TypeVarNode`      | Type variables with bounds, constraints, and variance |
| `ParamSpecNode`    | Parameter specification variables (PEP 612)           |
| `TypeVarTupleNode` | Variadic type variables (PEP 646)                     |

### Structured types

| Node                  | Represents                           |
|-----------------------|--------------------------------------|
| `DataclassNode`       | Dataclasses with field metadata      |
| `TypedDictNode`       | TypedDict with field definitions     |
| `NamedTupleNode`      | NamedTuple with named fields         |
| `ProtocolNode`        | Protocol with methods and attributes |
| `EnumNode`            | Enum with typed members              |
| `AttrsNode`           | attrs classes                        |
| `PydanticModelNode`   | Pydantic models                      |

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
- `EvalMode.DEFERRED`: Use `ForwardRefNode` for unresolvable annotations (default)
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
| `to_runtime_type()`         | Convert a node back to runtime type hints   |
| `cache_clear()`             | Clear the global inspection cache           |
| `cache_info()`              | Get cache statistics                        |

## Documentation

Full documentation is available at [typing-graph.tbhb.dev](https://typing-graph.tbhb.dev).

## Acknowledgments

[Pydantic][pydantic]'s approach to type introspection and metadata extraction inspired this library. typing-graph builds on Pydantic's [typing-inspection][typing-inspection] library for low-level type introspection.

## AI help

This project uses [Claude Code][claude-code] as a development tool for:

- Rubber ducking and exploring design alternatives
- Drafting documentation and docstrings
- Generating test scaffolding and boilerplate
- Code cleanup and refactoring suggestions
- Researching Python typing edge cases

All contributions undergo review and testing before inclusion, regardless of origin.

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
