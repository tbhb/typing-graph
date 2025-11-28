# Explanation

This section provides understanding-oriented discussion of concepts, architecture, and design decisions. Read these to learn how typing-graph works and why.

## Available topics

[Architecture overview](architecture.md)
:   High-level architecture of typing-graph, including the inspection layer, node hierarchy, and design principles.

[Forward references](forward-references.md)
:   How typing-graph handles forward references, evaluation modes, resolution states, and cycle detection.

[Metadata and Annotated types](metadata.md)
:   How typing-graph extracts and represents metadata from `Annotated` types, including metadata hoisting and the distinction between container-level and element-level metadata.

[Qualifiers](qualifiers.md)
:   Type qualifiers like `ClassVar`, `Final`, `Required`, and `ReadOnly`—what they mean, where they're valid, and how typing-graph extracts them.

[Type aliases](type-aliases.md)
:   Traditional `TypeAlias` annotations and PEP 695 `type` statements—how typing-graph represents and inspects type aliases.

[Generics and variance](generics.md)
:   Type parameters (`TypeVar`, `ParamSpec`, `TypeVarTuple`), variance (covariant, contravariant, invariant), and how typing-graph represents generic types.

[Union types](union-types.md)
:   How Python represents union types (`types.UnionType` vs `typing.Union`), the `|` operator quirk with typing special forms, and how typing-graph normalizes them.
