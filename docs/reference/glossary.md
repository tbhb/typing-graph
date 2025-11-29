# Glossary

This glossary defines key terms used throughout the typing-graph documentation. Terms appear in alphabetical order.

Annotated type { #annotated-type }
:   A type constructed with `typing.Annotated` that attaches metadata to a base type. For example, `Annotated[int, Gt(0)]` attaches a "greater than zero" constraint to an integer type. typing-graph extracts and processes this metadata through the inspection API. See [`AnnotatedNode`][typing_graph.AnnotatedNode].

Forward reference { #forward-reference }
:   A type annotation that references a class not yet defined at the point of annotation. Python represents forward references as strings (for example, `"Node"` or `Optional["Node"]`). typing-graph provides configurable strategies for evaluating forward references during inspection. See [`ForwardRefNode`][typing_graph.ForwardRefNode] and [`EvalMode`][typing_graph.EvalMode]. See also: [inspection](#inspection).

Inspection { #inspection }
:   The process of analyzing a type annotation and producing a structured [type node](#type-node) representation. The [`inspect_type()`][typing_graph.inspect_type] function performs inspection, returning an appropriate node subclass based on the input type.

Metadata hoisting { #metadata-hoisting }
:   The process of propagating metadata from an [annotated type](#annotated-type) wrapper to its base [type node](#type-node). When typing-graph inspects `Annotated[list[int], SomeMetadata]`, it hoists `SomeMetadata` to the resulting node, making the metadata accessible on the node that represents the actual type. Configure this behavior with [`InspectConfig`][typing_graph.InspectConfig].

Structured type { #structured-type }
:   A type that defines named fields with associated types. Structured types include dataclasses, TypedDict, NamedTuple, and Protocol. typing-graph provides specialized node classes for each: [`DataclassNode`][typing_graph.DataclassNode], [`TypedDictNode`][typing_graph.TypedDictNode], [`NamedTupleNode`][typing_graph.NamedTupleNode], and [`ProtocolNode`][typing_graph.ProtocolNode].

Type alias { #type-alias }
:   A named reference to another type, either using the `TypeAlias` annotation or PEP 695 `type` statement syntax. typing-graph unwraps type aliases during [inspection](#inspection) to analyze the underlying type structure. See [`TypeAliasNode`][typing_graph.TypeAliasNode] and [`inspect_type_alias()`][typing_graph.inspect_type_alias].

Type graph { #type-graph }
:   The tree structure produced when inspecting a type annotation. The root node represents the top-level type, and child nodes represent nested types (like a list's element type or a dataclass's field types). Navigate the graph using each node's [`children()`][typing_graph.TypeNode.children] method. See also: [type node](#type-node).

Type node { #type-node }
:   An immutable object representing an inspected type annotation. Each node class corresponds to a category of Python types: [`ConcreteNode`][typing_graph.ConcreteNode] for simple types, [`SubscriptedGenericNode`][typing_graph.SubscriptedGenericNode] for parameterized generics, [`UnionNode`][typing_graph.UnionNode] for unions, and so on. All nodes inherit from [`TypeNode`][typing_graph.TypeNode], which defines the common interface.

Type qualifier { #type-qualifier }
:   A wrapper type that modifies how another type behaves in a specific context. Qualifiers include `ClassVar` (class-level attribute), `Final` (immutable binding), `Required`/`NotRequired` (TypedDict field optionality), `ReadOnly` (immutable field), and `InitVar` (dataclass init-only field). typing-graph extracts qualifiers and exposes them through the `Qualifier` enumeration (re-exported from typing-inspection).

Type variable { #type-variable }
:   A placeholder for a type that gets filled in when a generic type gets parameterized. For example, in `list[T]`, `T` is a type variable. typing-graph represents type variables with [`TypeVarNode`][typing_graph.TypeVarNode], [`ParamSpecNode`][typing_graph.ParamSpecNode], and [`TypeVarTupleNode`][typing_graph.TypeVarTupleNode]. See also: [type node](#type-node).
