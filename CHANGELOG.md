# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [PEP 440 versioning](https://www.python.org/dev/peps/pep-0440/).

## [Unreleased](https://github.com/tbhb/typing-graph/compare/v0.3.0...HEAD)

### Added

#### Union normalization with `normalize_unions`

A new `InspectConfig.normalize_unions` option that normalizes all union types to `UnionNode` regardless of their runtime representation.

**Key features:**

- `normalize_unions=True` (default): Both `types.UnionType` (PEP 604 `|` syntax) and `typing.Union` produce `UnionNode`
- `normalize_unions=False`: Preserves native runtime representation (`typing.Union` produces `SubscriptedGenericNode`)
- Matches Python 3.14 behavior where all union expressions produce the same type
- Helper functions (`is_union_node()`, `get_union_members()`, `is_optional_node()`, `unwrap_optional()`) work uniformly regardless of normalization setting

**Rationale:** Eliminates the union representation inconsistency between `types.UnionType` and `typing.Union`, providing a consistent API surface that matches Python 3.14's native behavior.

**Documentation:**

- [Union types explanation](https://typing-graph.tbhb.dev/explanation/union-types/) - Understanding union normalization
- [Working with unions guide](https://typing-graph.tbhb.dev/guides/working-with-unions/) - Practical union handling patterns

#### Auto-namespace detection for forward reference resolution

Zero-configuration forward reference resolution for PEP 563 (`from __future__ import annotations`). The feature automatically extracts namespace context from source locations, eliminating manual `globalns` and `localns` parameters in most cases.

**Key features:**

- `auto_namespace` option on `InspectConfig` (default `True`): Enables automatic namespace extraction from source locations when resolving forward references
- `source` parameter on `inspect_type()` and related functions: Accepts a module, class, or function to extract namespace context from
- Namespace extraction utilities in `_namespace.py`: `extract_namespace()` for unified extraction, plus specialized `extract_class_namespace()`, `extract_function_namespace()`, and `extract_module_namespace()` for granular control

**How it works:**

1. When `auto_namespace=True` and a `source` is provided, typing-graph extracts `globalns` and `localns` from the source object
2. For modules, extracts the module's `__dict__` as the global namespace
3. For classes, extracts the class's module globals and the class `__dict__` as the local namespace
4. For functions, extracts the function's `__globals__` and closure variables

**Rationale:** PEP 563 defers annotation evaluation, requiring explicit namespace context to resolve forward references at runtime. Previously, users had to manually extract and pass namespaces. Auto-namespace detection handles this automatically, making PEP 563 support seamless.

**Documentation:**

- [Forward references explanation](https://typing-graph.tbhb.dev/explanation/forward-references/) - Understanding forward reference resolution and PEP 563
- [Namespace configuration guide](https://typing-graph.tbhb.dev/guides/namespace-configuration/) - Configuring namespace extraction for forward references
- [API reference: Namespace extraction](https://typing-graph.tbhb.dev/reference/api/#namespace-extraction) - Namespace utility functions

#### Other additions

- New "Common helper functions" how-to guide for `is_optional_node()`, `unwrap_optional()`, `get_union_members()`, and class type checks
- Quick start section in forward references explanation for common self-referential patterns
- Union check order warning in union types explanation

### Changed

- Clarified library scope with "What typing-graph is not" section in README and documentation landing page
- Fixed PEP 695 code examples to indicate Python 3.12+ requirement instead of "not yet implemented"

### Removed

- `DiscriminatedUnionNode` class and `is_discriminated_union_node()` type guard
- `TypeEdgeKind.VARIANT` edge kind

## [0.3.0](https://github.com/tbhb/typing-graph/compare/v0.2.0...v0.3.0) - 2025-12-10

### Added

#### Graph traversal with `walk()`

A new `walk()` function for depth-first traversal of type graphs with predicate filtering and depth limiting.

**Key features:**

- Depth-first iteration yielding unique nodes (by object identity)
- Iterative implementation prevents recursion depth errors
- Optional `predicate` filter with TypeIs support for type narrowing
- Optional `max_depth` parameter to limit traversal depth

#### Semantic edge metadata with `edges()`

A new `edges()` method on `TypeNode` that returns semantic edge metadata describing the relationship between parent and child nodes.

**New types:**

- `TypeEdge` - Frozen dataclass containing edge metadata (kind, optional name, optional index)
- `TypeEdgeKind` - Enum with 25 semantic edge kinds (ELEMENT, KEY, VALUE, FIELD, PARAM, RETURN, etc.)
- `TypeEdgeConnection` - Frozen dataclass pairing a `TypeEdge` with its target `TypeNode`

**Edge kinds by category:**

*Structural/container edges:*

- `ELEMENT` - Tuple element (positional)
- `KEY` - Dict key type
- `VALUE` - Dict value type
- `UNION_MEMBER` - Union variant
- `ALIAS_TARGET` - Type alias target definition
- `INTERSECTION_MEMBER` - Intersection member
- `VARIANT` - Discriminated union variant

*Named/attribute edges:*

- `FIELD` - Class/TypedDict field
- `METHOD` - Class method
- `PARAM` - Callable parameter
- `RETURN` - Callable return type

*Secondary/meta-type edges:*

- `ORIGIN` - Generic origin (`list` in `list[int]`)
- `BOUND` - TypeVar bound
- `CONSTRAINT` - TypeVar constraint
- `DEFAULT` - TypeParam default
- `BASE` - Class base class
- `TYPE_PARAM` - TypeVar definition
- `TYPE_ARG` - Applied type argument
- `SIGNATURE` - Function signature
- `NARROWS` - TypeGuard/TypeIs target
- `SUPERTYPE` - NewType supertype
- `ANNOTATED_BASE` - `Annotated[T, ...]` base type
- `META_OF` - `Type[T]` target
- `TARGET` - `Unpack[T]` target
- `PREFIX` - `Concatenate` prefix types
- `PARAM_SPEC` - `Concatenate` ParamSpec
- `RESOLVED` - ForwardRef resolved type
- `VALUE_TYPE` - Enum value type

**Helper constructors:**

- `TypeEdge.field(name)` - Create a FIELD edge with the given name
- `TypeEdge.element(index)` - Create an ELEMENT edge with the given index

#### TraversalError exception

A new `TraversalError` exception raised when `walk()` encounters invalid parameters (e.g., negative `max_depth`).

### Changed

- **`children()` is now O(1)**: The `children()` method on all `TypeNode` subclasses is now backed by a pre-computed tuple, making repeated access constant-time rather than recomputing the child list on each call.

### Documentation

**Tutorials:**

- [Traversing type graphs](https://typing-graph.tbhb.dev/tutorials/traversing-type-graphs/) - Introduction to graph traversal with `walk()`

**How-to guides:**

- [Filtering with walk()](https://typing-graph.tbhb.dev/guides/filtering-with-walk/) - Using predicates and depth limits to filter traversal

**Explanations:**

- [Graph edges](https://typing-graph.tbhb.dev/explanation/graph-edges/) - Understanding semantic edge metadata and relationships

**Updates to existing docs:**

- Added `walk()` reference to "Your first type inspection" tutorial
- Added graph traversal section to "Architecture overview" explanation

## [0.2.0](https://github.com/tbhb/typing-graph/compare/v0.1.0...v0.2.0) - 2025-11-30

### Added

#### MetadataCollection class

A new immutable, sequence-like container for working with type annotation metadata. The class provides a comprehensive API for querying, filtering, and transforming metadata extracted from `Annotated` types.

**Core features:**

- Full sequence protocol support (`__len__`, `__getitem__`, `__contains__`, `__iter__`, `__bool__`, `__reversed__`)
- Hashable when all contained metadata is hashable
- `EMPTY` singleton for representing empty collections
- Truncated `__repr__` for readable debugging output

**Factory methods:**

- `MetadataCollection.of(*items, auto_flatten=True)` - Create from arbitrary metadata items with optional GroupedMetadata flattening
- `MetadataCollection.from_annotated(annotated_type, *, recursive=False)` - Extract metadata from Annotated types
- `flatten()` - Expand GroupedMetadata at the top level
- `flatten_deep()` - Recursively expand all nested GroupedMetadata

**Query methods:**

- `find(type_)` - Find first metadata of exact type, returns `T | None`
- `find_first(*types)` - Find first metadata matching any of the given types
- `find_all(*types)` - Find all metadata matching given types (single type returns `MetadataCollection[T]`)
- `has(*types)` - Check if any metadata matches the given types
- `count(*types)` - Count metadata items matching the given types
- `get(type_, default=...)` - Get first metadata of type with optional default
- `get_required(type_)` - Get first metadata of type, raising `MetadataNotFoundError` if not found

**Filtering methods:**

- `filter(predicate)` - Filter by arbitrary predicate function
- `filter_by_type(type_, predicate)` - Type-safe filtering with typed predicate
- `first(predicate=None)` - Get first item optionally matching predicate
- `first_of_type(type_, predicate=None)` - Get first item of type optionally matching predicate
- `any(predicate)` - Check if any item matches predicate
- `find_protocol(protocol)` - Find first item implementing a runtime-checkable Protocol
- `has_protocol(protocol)` - Check if any item implements a Protocol
- `count_protocol(protocol)` - Count items implementing a Protocol

**Transformation methods:**

- `__add__` and `__or__` - Combine collections (both operators supported for ergonomics)
- `exclude(*types)` - Remove items of specified types
- `unique()` - Remove duplicate items (preserves order)
- `sorted(key=None)` - Sort items with optional key function
- `reversed()` - Reverse item order
- `map(func)` - Apply function to each item (terminal operation returning `list`)
- `partition(predicate)` - Split into matching and non-matching collections

**Introspection methods:**

- `types()` - Get frozenset of all metadata types in collection
- `by_type()` - Group metadata by type into a dict
- `is_empty` - Property indicating if collection has no items
- `is_hashable()` - Check if all items are hashable

**Exceptions:**

- `MetadataNotFoundError` - Raised by `get_required()` when metadata is not found
- `ProtocolNotRuntimeCheckableError` - Raised when Protocol methods receive non-runtime-checkable protocols

**Protocol:**

- `SupportsLessThan` - Protocol for items supporting `<` comparison, used by `sorted()`

### Changed

#### Breaking changes

- **`TypeNode.metadata` type changed from `tuple[Any, ...]` to `MetadataCollection[Any]`** - The metadata property on all TypeNode subclasses now returns a MetadataCollection instead of a plain tuple. MetadataCollection is fully backwards-compatible with tuple access patterns (indexing, iteration, length, containment), but code using tuple-specific methods may need updates.

- **`FieldDef.metadata` type changed from `tuple[Any, ...]` to `MetadataCollection[Any]`** - Field definitions for dataclasses, TypedDict, NamedTuple, attrs, and Pydantic models now return MetadataCollection.

- **`Parameter.metadata` type changed from `tuple[Any, ...]` to `MetadataCollection[Any]`** - Function parameter metadata now returns MetadataCollection.

### Documentation

Documentation has been reorganized following the [Diataxis framework](https://diataxis.fr/) with four distinct content types:

**Tutorials (learning-oriented):**

- First type inspection - Introduction to inspecting type annotations
- Working with metadata - Using MetadataCollection for metadata queries
- Structured types - Exploring dataclasses, TypedDict, and NamedTuple
- Functions and signatures - Inspecting function types and parameters

**How-to guides (goal-oriented):**

- How to query metadata - Find, filter, and extract metadata from types
- How to filter metadata - Narrow down metadata with predicates and protocols
- How to transform metadata - Combine, sort, and reshape metadata collections
- Metadata recipes - Common patterns and advanced techniques
- How to walk the type graph - Traverse and analyze type structures
- How to configure inspection - Customize inspection behavior

**Explanations (understanding-oriented):**

- Forward references - Reference resolution strategies and trade-offs
- Architecture - Design principles and internal structure
- Metadata and annotations - How metadata extraction and hoisting works
- Union types - Union handling and normalization
- Type aliases - PEP 695 type alias support
- Generics - Generic type handling and variance
- Qualifiers - Type qualifier extraction and representation

**Reference (information-oriented):**

- API reference reorganized into 11 logical sections with 122 public members
- Glossary with comprehensive terminology definitions
- Changelog with Keep a Changelog format

**LLM context files:**

- `llms.txt` - Concise project summary for LLM context windows
- `llms-full.txt` - Comprehensive documentation dump for detailed LLM assistance

## [0.1.0](https://github.com/tbhb/typing-graph/releases/tag/v0.1.0) - 2025-11-27

Initial release of typing-graph, a Python library for inspecting type annotations and building graph representations of type metadata.

### Added

#### Core type inspection

- `inspect_type()` function for inspecting any Python type annotation with caching support
- `clear_cache()` function to clear the global type inspection cache
- `get_type_hints_for_node()` function to convert TypeNode back to runtime type hints

#### Type node hierarchy

- `TypeNode` abstract base class with `source`, `metadata`, `qualifiers`, and `children()` for graph traversal
- `ConcreteType` for non-generic nominal types (int, str, custom classes)
- `GenericTypeNode` for unsubscripted generic types (list, Dict)
- `SubscriptedGeneric` for generic types with applied arguments (list[int], Dict[str, T])
- `UnionType` for union types (Union[A, B], A | B)
- `TupleType` for heterogeneous and homogeneous tuple types
- `CallableType` for callable types with parameter and return type information
- `AnnotatedType` for Annotated[T, ...] when metadata is not hoisted

#### Special form nodes

- `AnyType` for typing.Any
- `NeverType` for typing.Never and typing.NoReturn
- `SelfType` for typing.Self
- `LiteralNode` for Literal[...] with specific values
- `LiteralStringType` for typing.LiteralString (PEP 675)
- `EllipsisType` for ellipsis in Callable[..., R] and tuple[T, ...]

#### Type variable nodes

- `TypeVarNode` for TypeVar with variance, bounds, constraints, and defaults (PEP 696)
- `ParamSpecNode` for ParamSpec (PEP 612)
- `TypeVarTupleNode` for TypeVarTuple (PEP 646)
- `ConcatenateNode` for Concatenate[X, Y, P]
- `UnpackNode` for Unpack[Ts]
- `Variance` enum for type variable variance (invariant, covariant, contravariant)

#### Forward reference handling

- `ForwardRef` node for string forward references
- `RefState` with Unresolved, Resolved, and Failed states
- Three evaluation modes via `EvalMode`: EAGER, DEFERRED, STRINGIFIED

#### Type narrowing nodes

- `TypeGuardType` for TypeGuard[T] (PEP 647)
- `TypeIsType` for TypeIs[T] (PEP 742)
- `MetaType` for Type[T] and type[T]
- `NewTypeNode` for NewType definitions

#### Type alias support

- `TypeAliasNode` for simple type aliases
- `GenericAlias` for PEP 695 parameterized type aliases (type Vector[T] = list[T])
- `inspect_type_alias()` function for inspecting type aliases

#### Structured type inspection

- `DataclassType` with `DataclassFieldDef` for dataclass introspection
- `TypedDictType` with field requiredness tracking
- `NamedTupleType` with field definitions
- `ProtocolType` with methods and attributes
- `EnumType` with typed members
- `AttrsType` with `AttrsFieldDef` for attrs class introspection
- `PydanticModelType` with `PydanticFieldDef` for Pydantic model introspection
- `FieldDef` base class for field definitions

#### Class inspection

- `inspect_class()` for auto-detecting and inspecting any class type
- `inspect_dataclass()` for dataclass-specific inspection
- `inspect_enum()` for enum-specific inspection
- `ClassNode` for general class inspection with type parameters, bases, methods, and variables

#### Function inspection

- `inspect_function()` for function introspection with signature details
- `inspect_signature()` for callable signature inspection
- `FunctionNode` with async, generator, and decorator detection
- `SignatureNode` with full parameter information
- `Parameter` class with name, type, kind, default, and metadata

#### Module inspection

- `inspect_module()` for discovering all public types in a module
- `ModuleTypes` result class containing classes, functions, type aliases, type vars, and constants

#### Configuration

- `InspectConfig` for controlling inspection behavior
- Configurable forward reference evaluation mode
- Optional recursion depth limits
- Options for including private members, inherited members, methods, class vars, and instance vars
- Optional metadata hoisting from Annotated types
- Optional source location tracking

#### Type qualifier support

- Extraction and tracking of ClassVar, Final, Required, NotRequired, ReadOnly, and InitVar qualifiers
- Re-export of `Qualifier` from typing-inspection

#### Source location tracking

- `SourceLocation` class with module, qualname, lineno, and file attributes
- Optional source location extraction for type definitions

#### Type guard functions

- TypeIs-based type guard functions for all node types (is_type_node, is_concrete_type, is_union_type_node, etc.)

### Python version support

- Python 3.10, 3.11, 3.12, 3.13, and 3.14
