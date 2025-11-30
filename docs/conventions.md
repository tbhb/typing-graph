# Conventions

This page explains patterns used throughout the typing-graph documentation to help you navigate and understand the examples.

## Code examples

### Running examples

Most code examples are complete and runnable. You can copy them directly into a Python file or interactive session.

```python
from typing import Annotated
from typing_graph import inspect_type

node = inspect_type(Annotated[int, "positive"])
print(node.metadata)  # MetadataCollection(['positive'])
```

### Illustrative snippets

Examples marked with `# snippet` show partial code that demonstrates a concept but will not run standalone:

```python
# snippet
def process(item: T) -> Result[T]:
    ...  # implementation details omitted
```

### Error demonstrations

Examples marked with `# Error!` show code that produces an error condition:

```python
# Error!
coll.get_required(MissingType)  # Raises MetadataNotFoundError
```

## Admonitions

The documentation uses colored boxes to highlight different types of information.

!!! note "Notes highlight key information"

    Notes draw attention to important concepts or behaviors you should be aware of.

!!! tip "Tips suggest best practices"

    Tips provide performance advice or recommend preferred approaches.

!!! warning "Warnings flag potential issues"

    Warnings alert you to common pitfalls or behaviors that might be surprising.

??? info "Collapsible boxes contain optional details"

    Click to expand sections that provide additional context you can skip if you're in a hurry.

## Method signatures

Method signatures use Python's type annotation syntax. For example:

```python
def find(self, type_: type[T]) -> T | None: ...
```

This signature tells you:

- `type_` accepts a type (like `str` or a custom class)
- The return value is either an instance of that type or `None`

## Terminology

Key terms appear throughout the documentation. The [glossary](reference/glossary.md) defines all terminology, including:

- **Type node**: An object representing an inspected type annotation
- **Metadata**: Values attached to types via `Annotated[T, meta1, meta2]`
- **Type graph**: The tree structure produced when inspecting nested types

## Documentation sections

The documentation is organized into four sections based on your goals:

[Tutorials](tutorials/index.md)
:   Step-by-step lessons for learning typing-graph from scratch.

[Guides](guides/index.md)
:   Task-oriented recipes for accomplishing specific goals.

[Explanation](explanation/index.md)
:   Background information and conceptual discussions.

[Reference](reference/index.md)
:   Technical specifications and API documentation.

## See also

- [Glossary](reference/glossary.md) - Complete list of term definitions
- [API reference](reference/api.md) - Full API documentation
