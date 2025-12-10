# Explanation

This section provides understanding-oriented discussions of concepts, architecture, and design decisions. These pages answer "why" questions: why typing-graph exists, why it makes certain design choices, and why Python's type system works the way it does.

Unlike tutorials (which guide you through tasks) or reference documentation (which lists every API detail), explanations help you build mental models. Reading these pages will deepen your understanding of both typing-graph and Python's type system, making you more effective when building type introspection tools.

## How to use this section

Each page explores a concept in depth. You don't need to read them in order, though the architecture overview provides useful context for the others. If you're trying to do something specific, start with the [tutorials](../tutorials/index.md) or [how-to guides](../guides/index.md) instead.

## Available topics

[Architecture overview](architecture.md)
:   Why typing-graph exists, how its components work together, and the reasoning behind key design decisions. Start here to understand the library's structure.

[Graph edges](graph-edges.md)
:   Edge semantics in the type graph: what `TypeEdgeKind` values represent, when to use `children()` versus `edges()`, and how edges enable schema generation and serialization.

[Forward references](forward-references.md)
:   The evolution of forward reference handling in Python, from string annotations to PEP 649's lazy evaluation. Explains typing-graph's evaluation modes and why they exist.

[Metadata and Annotated types](metadata.md)
:   How `Annotated` metadata enables declarative programming, how typing-graph extracts and organizes it, and the design rationale behind `MetadataCollection`.

[Qualifiers](qualifiers.md)
:   Type qualifiers like `ClassVar`, `Final`, and `Required`: what they mean, how they evolved, and how typing-graph distinguishes them from metadata.

[Type aliases](type-aliases.md)
:   The difference between traditional and PEP 695 type aliases, why Python needed new syntax, and how typing-graph represents both forms.

[Generics and variance](generics.md)
:   Type parameters, variance rules, and why they matter. Explains how typing-graph models generic types and what automatic variance inference means.

[Union types](union-types.md)
:   Why Python has two different union types, the surprising behavior of the `|` operator, and how typing-graph handles the distinction.

## Related resources

- **Want hands-on practice?** Start with the [tutorials](../tutorials/index.md)
- **Need to do specific tasks?** Use the [how-to guides](../guides/index.md)
- **Looking up API details?** See the [API reference](../reference/api.md)
