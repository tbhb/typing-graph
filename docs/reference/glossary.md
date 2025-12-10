# Glossary

Definitions of key terms used throughout the typing-graph documentation. Terms appear in alphabetical order. Each term links to its primary explanation page and relevant API reference.

Annotated type { #annotated-type }
:   A type constructed with `typing.Annotated` that attaches metadata to a base type. Example: `Annotated[int, Gt(0)]` attaches a "greater than zero" constraint to an integer type.

    **Learn more:** [Metadata and Annotated types](../explanation/metadata.md) | **API:** [`AnnotatedNode`][typing_graph.AnnotatedNode]

Depth-first traversal { #depth-first-traversal }
:   A graph traversal strategy that visits each node before its children, exploring as deep as possible along each branch before backtracking. The [`walk()`][typing_graph.walk] function uses this approach.

    **Guide:** [Walking the type graph](../guides/walking-type-graph.md) | **API:** [`walk()`][typing_graph.walk]

Edge { #edge }
:   A semantic relationship between a parent [type node](#type-node) and a child node in a [type graph](#type-graph). Edges describe how nodes relate (for example, `KEY` for dict key types, `FIELD` for class fields, `ELEMENT` for tuple elements).

    **API:** [`TypeEdge`][typing_graph.TypeEdge], [`TypeEdgeKind`][typing_graph.TypeEdgeKind], [`TypeEdgeConnection`][typing_graph.TypeEdgeConnection]

EvalMode { #eval-mode }
:   An enumeration controlling forward reference evaluation during [inspection](#inspection). Values: `EAGER` (resolve immediately, fail on error), `DEFERRED` (wrap in ForwardRef for lazy resolution), `STRINGIFIED` (keep as string).

    **Learn more:** [Forward references](../explanation/forward-references.md) | **API:** [`EvalMode`][typing_graph.EvalMode]

Forward reference { #forward-reference }
:   A type annotation referencing a class not yet defined at the point of annotation. Python represents forward references as strings (for example, `"Node"` or `Optional["Node"]`).

    **Learn more:** [Forward references](../explanation/forward-references.md) | **API:** [`ForwardRefNode`][typing_graph.ForwardRefNode], [`EvalMode`][typing_graph.EvalMode]

GroupedMetadata { #grouped-metadata }
:   A protocol from the annotated-types library for metadata containing other metadata items. Example: `Interval(ge=0, le=100)` groups `Ge(0)` and `Le(100)`.

    **Learn more:** [GroupedMetadata flattening](../explanation/metadata.md#groupedmetadata-automatic-flattening) | **API:** [`MetadataCollection`][typing_graph.MetadataCollection]

InspectConfig { #inspect-config }
:   A frozen dataclass containing configuration options for type inspection. Controls forward reference evaluation mode, recursion depth, member inclusion, metadata hoisting, and source location tracking.

    **Learn more:** [Configuration options](../guides/configuration.md) | **API:** [`InspectConfig`][typing_graph.InspectConfig]

Inspection { #inspection }
:   The process of analyzing a type annotation to produce a [type node](#type-node) representation. The [`inspect_type()`][typing_graph.inspect_type] function performs inspection, returning an appropriate node subclass based on the input type.

    **Learn more:** [Architecture overview](../explanation/architecture.md) | **Tutorial:** [Your first type inspection](../tutorials/first-inspection.md)

Metadata hoisting { #metadata-hoisting }
:   The process of propagating metadata from an [annotated type](#annotated-type) wrapper to its base [type node](#type-node). Example: inspecting `Annotated[list[int], SomeMetadata]` hoists `SomeMetadata` to the resulting node.

    **Learn more:** [Metadata and Annotated types](../explanation/metadata.md#metadata-hoisting) | **API:** [`InspectConfig.hoist_metadata`][typing_graph.InspectConfig]

MetadataCollection { #metadata-collection }
:   An immutable, type-safe container for metadata extracted from `Annotated` type annotations. Every [type node](#type-node) has a `metadata` attribute containing a `MetadataCollection`.

    **Learn more:** [Metadata and Annotated types](../explanation/metadata.md) | **Tutorial:** [Working with metadata](../tutorials/working-with-metadata.md) | **API:** [`MetadataCollection`][typing_graph.MetadataCollection]

Structured type { #structured-type }
:   A type defining named fields with associated types. Includes dataclasses, TypedDict, NamedTuple, and Protocol.

    **Tutorial:** [Inspecting structured types](../tutorials/structured-types.md) | **API:** [`DataclassNode`][typing_graph.DataclassNode], [`TypedDictNode`][typing_graph.TypedDictNode], [`NamedTupleNode`][typing_graph.NamedTupleNode], [`ProtocolNode`][typing_graph.ProtocolNode]

Type alias { #type-alias }
:   A named reference to another type, using either `TypeAlias` annotation or PEP 695 `type` statement syntax.

    **Learn more:** [Type aliases](../explanation/type-aliases.md) | **API:** [`TypeAliasNode`][typing_graph.TypeAliasNode], [`inspect_type_alias()`][typing_graph.inspect_type_alias]

Type graph { #type-graph }
:   The tree structure produced when inspecting a type annotation. The root node represents the top-level type; child nodes represent nested types (element types, field types).

    **Learn more:** [Architecture overview](../explanation/architecture.md) | **Guide:** [Walking the type graph](../guides/walking-type-graph.md) | **API:** [`TypeNode.children()`][typing_graph.TypeNode.children]

Type node { #type-node }
:   An immutable object representing an inspected type annotation. Node classes correspond to type categories: [`ConcreteNode`][typing_graph.ConcreteNode] for simple types, [`SubscriptedGenericNode`][typing_graph.SubscriptedGenericNode] for parameterized generics, [`UnionNode`][typing_graph.UnionNode] for unions. All inherit from [`TypeNode`][typing_graph.TypeNode].

    **Learn more:** [Architecture overview](../explanation/architecture.md) | **Tutorial:** [Your first type inspection](../tutorials/first-inspection.md)

Type qualifier { #type-qualifier }
:   A wrapper type modifying how another type behaves in a specific context. Includes `ClassVar`, `Final`, `Required`, `NotRequired`, `ReadOnly`, and `InitVar`.

    **Learn more:** [Qualifiers](../explanation/qualifiers.md)

Type variable { #type-variable }
:   A placeholder for a type filled in when a generic type is parameterized. Example: in `list[T]`, `T` is a type variable.

    **Learn more:** [Generics and variance](../explanation/generics.md) | **API:** [`TypeVarNode`][typing_graph.TypeVarNode], [`ParamSpecNode`][typing_graph.ParamSpecNode], [`TypeVarTupleNode`][typing_graph.TypeVarTupleNode]

Walk { #walk }
:   An iterator-based traversal of a [type graph](#type-graph) using [depth-first traversal](#depth-first-traversal). The [`walk()`][typing_graph.walk] function yields unique nodes, supports predicate filtering with type narrowing, and allows depth limiting.

    **Guide:** [Walking the type graph](../guides/walking-type-graph.md) | **API:** [`walk()`][typing_graph.walk]
