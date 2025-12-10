# typing-graph

[![CI](https://github.com/tbhb/typing-graph/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/tbhb/typing-graph/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/typing-graph.svg)](https://pypi.org/project/typing-graph/)
[![codecov](https://codecov.io/gh/tbhb/typing-graph/branch/main/graph/badge.svg)](https://codecov.io/gh/tbhb/typing-graph)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)

A building block for Python libraries that derive runtime behavior from type annotations. Pass any type (generics, `Annotated`, dataclasses, `TypedDict`, [PEP 695][pep-695] aliases) and get back a graph of nodes with metadata hoisting, qualifier detection, and semantic edge information.

> [!WARNING]
> Early development. APIs may change. Not yet recommended for production use.

Built on [Pydantic's typing-inspection][typing-inspection] and designed for compatibility with [annotated-types][annotated-types].

## Features

- [x] **Type introspection**: Inspect any type annotation (generics, `Annotated`, `TypedDict`, PEP 695 aliases) into structured nodes
- [x] **Metadata hoisting**: Extract `Annotated` metadata and attach to base types
- [x] **Metadata querying**: `MetadataCollection` with `find()`, `filter()`, `get()`, and protocol matching
- [x] **Qualifier extraction**: Detect `ClassVar`, `Final`, `Required`, `NotRequired`, `ReadOnly`, `InitVar`
- [x] **Graph traversal**: `walk()` for depth-first iteration, `edges()` for semantic relationships with `TypeEdgeKind`
- [x] **Structured types**: `dataclass`, `TypedDict`, `NamedTuple`, `Protocol`, `Enum`
- [x] **Modern Python**: PEP 695 type parameters, PEP 696 defaults, `TypeGuard`, `TypeIs`

**Planned:** annotated-types integration, visitor pattern, attrs/Pydantic support. See the [roadmap](https://typing-graph.tbhb.dev/roadmap/).

## Use cases

typing-graph provides the foundation for frameworks that derive behavior from type annotations:

| Use case                    | Description                                                                                                               |
|-----------------------------|---------------------------------------------------------------------------------------------------------------------------|
| **Validation frameworks**   | Extract constraints from `Annotated` metadata and generate validation logic based on type structure                       |
| **Type conversion**         | Convert values between types by inspecting source and target type structures, handling nested generics and union types    |
| **Command-line interfaces** | Parse command-line arguments by inspecting function signatures and generating appropriate parsers for each parameter type |
| **ORM mapping**             | Map Python classes to database schemas by analyzing field types, extracting column metadata from annotations              |
| **Feature flags**           | Extract feature flag definitions from type metadata to configure runtime behavior based on annotated types                |
| **Code generation**         | Generate serializers, API clients, or documentation by traversing the type graph and emitting code for each node type     |

## Installation

```bash
pip install typing-graph  # or: uv add typing-graph
```

Requires Python 3.10+.

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

>>> # The outer node is a SubscriptedGenericNode (list) with container-level metadata
>>> node.origin.cls
<class 'list'>
>>> node.metadata.find(MinLen)
MinLen(value=1)

>>> # Traverse to the element type - it carries its own metadata
>>> element = node.args[0]
>>> element.cls
<class 'str'>
>>> element.metadata.find(Pattern)
Pattern(regex='^https?://')

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

## Graph traversal

Use `walk()` for depth-first traversal with optional filtering and depth limits:

```python
from typing_graph import inspect_type, is_concrete_node, walk, ConcreteNode
from typing_extensions import TypeIs

node = inspect_type(dict[str, list[int]])

# Iterate all nodes
for n in walk(node):
    print(n)

for n in walk(node, predicate=is_concrete_node):
    print(n.cls)  # str, int
```

Use `edges()` on any node for semantic relationship information:

```python
for conn in node.edges():
    print(conn.edge.kind, conn.target)
# TypeEdgeKind.ORIGIN SubscriptedGenericNode(...)
# TypeEdgeKind.TYPE_ARG ConcreteNode(cls=str)
# TypeEdgeKind.TYPE_ARG SubscriptedGenericNode(...)
```

`TypeEdgeKind` describes relationships: `ORIGIN`, `TYPE_ARG`, `ELEMENT`, `FIELD`, `PARAM`, `RETURN`, `UNION_MEMBER`, and more.

## Configuration

```python
from typing_graph import inspect_type, InspectConfig, EvalMode

config = InspectConfig(
    eval_mode=EvalMode.DEFERRED,  # EAGER, DEFERRED (default), or STRINGIFIED
    max_depth=50,
    hoist_metadata=True,
)
node = inspect_type(SomeType, config=config)
```

## Documentation

Full documentation is available at [typing-graph.tbhb.dev](https://typing-graph.tbhb.dev).

## Acknowledgments

[Pydantic][pydantic]'s approach to type introspection and metadata extraction inspired this library. typing-graph builds on Pydantic's [typing-inspection][typing-inspection] library for low-level type introspection.

## AI help

This project uses [Claude Code][claude-code] as a development tool for:

- Rubber ducking and exploring architecture and design alternatives
- Drafting documentation and docstrings
- Generating test scaffolding and boilerplate
- Code cleanup and refactoring suggestions
- Researching Python typing edge cases
- Running benchmarks and mutation testing
- Release automation

All contributions undergo review and testing before inclusion, regardless of origin.

## License

MIT License. See [LICENSE](LICENSE) for details.

[annotated-types]: https://github.com/annotated-types/annotated-types
[claude-code]: https://docs.anthropic.com/en/docs/claude-code
[pep-695]: https://peps.python.org/pep-0695/
[pydantic]: https://pydantic.dev
[typing-inspection]: https://typing-inspection.pydantic.dev/latest/
