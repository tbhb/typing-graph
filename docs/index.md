# typing-graph

[![CI](https://github.com/tbhb/typing-graph/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/tbhb/typing-graph/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/typing-graph.svg)](https://pypi.org/project/typing-graph/)
[![codecov](https://codecov.io/gh/tbhb/typing-graph/branch/main/graph/badge.svg)](https://codecov.io/gh/tbhb/typing-graph)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)

typing-graph is a building block for Python libraries and frameworks that derive runtime behavior from type annotations. If you're building validation frameworks, CLI tools, serializers, ORMs, or similar tools that inspect types to generate code or configure behavior, typing-graph provides the structured type introspection layer so you can focus on your domain logic.

Pass any type (generics, `Annotated`, dataclasses, `TypedDict`, PEP 695 aliases) and get back a graph of nodes representing the type structure and its metadata. The library handles metadata hoisting (extracting annotations from `Annotated` wrappers), qualifier detection (`ClassVar`, `Final`, `Required`), forward reference resolution, and caching. Each node exposes a [`children()`][typing_graph.TypeNode.children] method for recursive traversal.

!!! warning "Alpha software"

    This project is in early development. APIs may change without notice. Not yet recommended for production use.

## Installation

```bash
pip install typing-graph
```

Requires Python 3.10 or later. See [Installation](install.md) for package manager options and optional dependencies.

## Quick example

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

## Use cases

typing-graph provides the foundation for frameworks that derive behavior from type annotations:

<div class="grid" markdown>

:material-check-circle:{ .lg .middle } __Validation frameworks__

Build validators that extract constraints from `Annotated` metadata and generate validation logic based on type structure.

:material-swap-horizontal:{ .lg .middle } __Type conversion__

Convert values between types by inspecting source and target type structures, handling nested generics and union types.

:material-console:{ .lg .middle } __Command-line interfaces__

Parse command-line arguments by inspecting function signatures and generating appropriate parsers for each parameter type.

:material-database:{ .lg .middle } __ORM mapping__

Map Python classes to database schemas by analyzing field types, extracting column metadata from annotations.

:material-flag:{ .lg .middle } __Feature flags__

Extract feature flag definitions from type metadata to configure runtime behavior based on annotated types.

:material-code-braces:{ .lg .middle } __Code generation__

Generate serializers, API clients, or documentation by traversing the type graph and emitting code for each node type.

</div>

## Next steps

Ready to start using typing-graph? Choose your path based on how you learn best.

<div class="grid cards" markdown>

-   :material-school:{ .lg .middle } __Tutorials__

    ---

    Learn typing-graph step by step with hands-on lessons that teach the fundamentals.

    [:octicons-arrow-right-24: Get started](tutorials/index.md)

-   :material-directions:{ .lg .middle } __How-to guides__

    ---

    Follow practical recipes that show how to achieve specific goals with typing-graph.

    [:octicons-arrow-right-24: Find a guide](guides/index.md)

-   :material-book-open-variant:{ .lg .middle } __Reference__

    ---

    Look up technical details about the API, including classes, functions, and configuration.

    [:octicons-arrow-right-24: Browse the API](reference/index.md)

-   :material-lightbulb-on:{ .lg .middle } __Explanation__

    ---

    Understand the concepts, architecture, and design decisions behind typing-graph.

    [:octicons-arrow-right-24: Learn more](explanation/index.md)

</div>
