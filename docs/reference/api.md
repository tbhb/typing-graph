<!-- vale off -->

# API reference

Complete reference for all public classes and functions in the typing-graph library. This reference is auto-generated from source docstrings using [mkdocstrings](https://mkdocstrings.github.io/).

## Contents

- [Core inspection functions](#core-inspection-functions) - Entry points for type inspection
- [Traversal](#traversal) - Graph traversal function
- [Configuration](#configuration) - Classes for controlling inspection behavior
- [Namespace extraction](#namespace-extraction) - Functions for extracting namespaces from objects
- [Type nodes](#type-nodes) - Base classes and node types for representing types
- [Structured type nodes](#structured-type-nodes) - Classes, dataclasses, TypedDicts, and similar
- [Function and callable nodes](#function-and-callable-nodes) - Functions and signatures
- [Helper types](#helper-types) - Supporting types for fields, parameters, and locations
- [Metadata collection](#metadata-collection) - Working with type metadata
- [Edge types](#edge-types) - Edge types for graph relationships
- [Exceptions](#exceptions) - Base, metadata, and traversal exceptions
- [Type guards](#type-guards) - Type narrowing functions
- [Utility functions](#utility-functions) - Helpers for unions and optional types
- [Cache management](#cache-management) - Managing the inspection cache

---

## Core inspection functions

Entry points for inspecting type annotations, classes, functions, modules, and type parameters.

::: typing_graph
    options:
      show_root_heading: false
      show_docstring_description: false
      heading_level: 3
      members:
        - inspect_type
        - inspect_class
        - inspect_dataclass
        - inspect_enum
        - inspect_named_tuple
        - inspect_protocol
        - inspect_typed_dict
        - inspect_function
        - inspect_signature
        - inspect_module
        - inspect_type_alias
        - inspect_type_param

## Traversal

The primary traversal function for depth-first iteration over type graphs.

::: typing_graph
    options:
      show_root_heading: false
      show_docstring_description: false
      heading_level: 3
      members:
        - walk

## Configuration

Classes for controlling inspection behavior.

::: typing_graph
    options:
      show_root_heading: false
      show_docstring_description: false
      heading_level: 3
      members:
        - InspectConfig
        - EvalMode

## Namespace extraction

Functions for extracting global and local namespaces from Python objects. These functions support forward reference resolution by providing namespace context from classes, functions, and modules.

For practical usage guidance, see [How to configure namespaces](../guides/namespace-configuration.md). For background on why namespace extraction matters, see [Forward references](../explanation/forward-references.md).

### Type aliases

::: typing_graph
    options:
      show_root_heading: false
      show_docstring_description: false
      heading_level: 4
      members:
        - NamespacePair
        - NamespaceSource

### Extraction functions

::: typing_graph
    options:
      show_root_heading: false
      show_docstring_description: false
      heading_level: 4
      members:
        - extract_namespace
        - extract_class_namespace
        - extract_function_namespace
        - extract_module_namespace

## Type nodes

### Base classes

The foundational type node class and type variable.

::: typing_graph
    options:
      show_root_heading: false
      show_docstring_description: false
      heading_level: 4
      members:
        - TypeNode
        - TypeNodeT

### Concrete and generic types

Nodes representing concrete types, generics, and annotated types.

::: typing_graph
    options:
      show_root_heading: false
      show_docstring_description: false
      heading_level: 4
      members:
        - ConcreteNode
        - SubscriptedGenericNode
        - GenericAliasNode
        - GenericTypeNode
        - AnnotatedNode
        - NewTypeNode
        - TypeAliasNode

### Union and intersection types

Nodes representing type unions and intersections.

::: typing_graph
    options:
      show_root_heading: false
      show_docstring_description: false
      heading_level: 4
      members:
        - UnionNode
        - IntersectionNode

### Type variables

Nodes representing type parameters and variance.

::: typing_graph
    options:
      show_root_heading: false
      show_docstring_description: false
      heading_level: 4
      members:
        - TypeVarNode
        - ParamSpecNode
        - TypeVarTupleNode
        - TypeParamNode
        - Variance

### Special types

Nodes for special typing constructs.

::: typing_graph
    options:
      show_root_heading: false
      show_docstring_description: false
      heading_level: 4
      members:
        - AnyNode
        - NeverNode
        - SelfNode
        - LiteralNode
        - LiteralStringNode
        - TupleNode
        - EllipsisNode
        - ForwardRefNode
        - MetaNode
        - ConcatenateNode
        - UnpackNode
        - TypeGuardNode
        - TypeIsNode

### Forward reference state

Types representing forward reference resolution states.

::: typing_graph
    options:
      show_root_heading: false
      show_docstring_description: false
      heading_level: 4
      members:
        - RefState
        - RefResolved
        - RefUnresolved
        - RefFailed

## Structured type nodes

Nodes representing classes, dataclasses, TypedDicts, and other structured types.

::: typing_graph
    options:
      show_root_heading: false
      show_docstring_description: false
      heading_level: 3
      members:
        - StructuredNode
        - ClassNode
        - DataclassNode
        - TypedDictNode
        - NamedTupleNode
        - EnumNode
        - ProtocolNode

## Function and callable nodes

Nodes representing functions, callables, and signatures.

::: typing_graph
    options:
      show_root_heading: false
      show_docstring_description: false
      heading_level: 3
      members:
        - FunctionNode
        - CallableNode
        - SignatureNode
        - MethodSig

## Helper types

Supporting types for field definitions, parameters, and source locations.

::: typing_graph
    options:
      show_root_heading: false
      show_docstring_description: false
      heading_level: 3
      members:
        - FieldDef
        - DataclassFieldDef
        - Parameter
        - SourceLocation
        - ClassInspectResult
        - ModuleTypes

## Metadata collection

Classes for working with type metadata.

::: typing_graph
    options:
      show_root_heading: false
      show_docstring_description: false
      heading_level: 3
      members:
        - MetadataCollection
        - SupportsLessThan

## Edge types

Types representing edges between nodes in the type graph.

::: typing_graph
    options:
      show_root_heading: false
      show_docstring_description: false
      heading_level: 3
      members:
        - TypeEdge
        - TypeEdgeKind
        - TypeEdgeConnection

## Exceptions

Exception classes for error handling.

### Base exception

::: typing_graph
    options:
      show_root_heading: false
      show_docstring_description: false
      heading_level: 4
      members:
        - TypingGraphError

### Metadata exceptions

::: typing_graph
    options:
      show_root_heading: false
      show_docstring_description: false
      heading_level: 4
      members:
        - MetadataNotFoundError
        - ProtocolNotRuntimeCheckableError

### Traversal exceptions

::: typing_graph
    options:
      show_root_heading: false
      show_docstring_description: false
      heading_level: 4
      members:
        - TraversalError

## Type guards

### Node type guards

Type guard functions for type narrowing on node types.

::: typing_graph
    options:
      show_root_heading: false
      show_docstring_description: false
      heading_level: 4
      members:
        - is_type_node
        - is_concrete_node
        - is_annotated_node
        - is_subscripted_generic_node
        - is_generic_alias_node
        - is_generic_node
        - is_union_type_node
        - is_intersection_node
        - is_type_var_node
        - is_param_spec_node
        - is_type_var_tuple_node
        - is_type_param_node
        - is_any_node
        - is_never_node
        - is_self_node
        - is_literal_node
        - is_literal_string_node
        - is_tuple_node
        - is_ellipsis_node
        - is_forward_ref_node
        - is_meta_node
        - is_concatenate_node
        - is_unpack_node
        - is_type_guard_node
        - is_type_is_node
        - is_ref_state_resolved
        - is_ref_state_unresolved
        - is_ref_state_failed
        - is_structured_node
        - is_class_node
        - is_dataclass_node
        - is_typed_dict_node
        - is_named_tuple_node
        - is_enum_node
        - is_protocol_node
        - is_function_node
        - is_callable_node
        - is_signature_node
        - is_method_sig
        - is_type_alias_node
        - is_new_type_node

### Class detection functions

Functions for detecting special class types at runtime.

::: typing_graph
    options:
      show_root_heading: false
      show_docstring_description: false
      heading_level: 4
      members:
        - is_dataclass_class
        - is_typeddict_class
        - is_namedtuple_class
        - is_enum_class
        - is_protocol_class

## Utility functions

Helper functions for working with union types and optional values.

::: typing_graph
    options:
      show_root_heading: false
      show_docstring_description: false
      heading_level: 3
      members:
        - get_union_members
        - is_union_node
        - is_optional_node
        - unwrap_optional
        - to_runtime_type

## Cache management

Functions for managing the type inspection cache.

::: typing_graph
    options:
      show_root_heading: false
      show_docstring_description: false
      heading_level: 3
      members:
        - cache_info
        - cache_clear

<!-- vale on -->
