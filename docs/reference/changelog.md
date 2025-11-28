---
toc_depth: 1
---

# Changelog

!!! tip "Unreleased changes"

    For changes that have not yet been released, see the [CHANGELOG.md](https://github.com/tbhb/typing-graph/blob/main/CHANGELOG.md) file in the repository.

## v0.1.0 (2025-11-27) { data-toc-label="v0.1.0 (2025-11-27)" }

[:material-github: GitHub release](https://github.com/tbhb/typing-graph/releases/tag/v0.1.0)

This is the initial release of typing-graph, a Python library for inspecting type annotations and building graph representations of type metadata.

### Added

#### Core type inspection

- `inspect_type()` function for inspecting any Python type annotation with caching support
- `clear_cache()` function to clear the global type inspection cache
- `get_type_hints_for_node()` function to convert `TypeNode` back to runtime type hints

#### Type node hierarchy

- `TypeNode` abstract base class with `source`, `metadata`, `qualifiers`, and `children()` for graph traversal
- `ConcreteType` for non-generic nominal types (`int`, `str`, custom classes)
- `GenericTypeNode` for unsubscripted generic types (`list`, `Dict`)
- `SubscriptedGeneric` for generic types with applied arguments (`list[int]`, `Dict[str, T]`)
- `UnionType` for union types (`A | B`)
- `TupleType` for heterogeneous and homogeneous tuple types
- `CallableType` for callable types with parameter and return type information
- `AnnotatedType` for `Annotated[T, ...]` when metadata is not hoisted

#### Special form nodes

- `AnyType` for `typing.Any`
- `NeverType` for `typing.Never` and `typing.NoReturn`
- `SelfType` for `typing.Self`
- `LiteralNode` for `Literal[...]` with specific values
- `LiteralStringType` for `typing.LiteralString` (PEP 675)
- `EllipsisType` for ellipsis in `Callable[..., R]` and `tuple[T, ...]`

#### Type variable nodes

- `TypeVarNode` for `TypeVar` with variance, bounds, constraints, and defaults (PEP 696)
- `ParamSpecNode` for `ParamSpec` (PEP 612)
- `TypeVarTupleNode` for `TypeVarTuple` (PEP 646)
- `ConcatenateNode` for `Concatenate[X, Y, P]`
- `UnpackNode` for `Unpack[Ts]`
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
- `GenericAlias` for PEP 695 parameterized type aliases (`type Vector[T] = list[T]`)
- `inspect_type_alias()` function for inspecting type aliases

#### Structured type inspection

- `DataclassType` with `DataclassFieldDef` for dataclass introspection
- `TypedDictType` with field requiredness tracking
- `NamedTupleType` with field definitions
- `ProtocolType` with methods and attributes
- `EnumType` with typed members
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

- Extraction and tracking of `ClassVar`, `Final`, `Required`, `NotRequired`, `ReadOnly`, and `InitVar` qualifiers
- Re-export of `Qualifier` from typing-inspection

#### Source location tracking

- `SourceLocation` class with `module`, `qualname`, `lineno`, and `file` attributes
- Optional source location extraction for type definitions

#### Type guard functions

- `TypeIs`-based type guard functions for all node types (`is_type_node`, `is_concrete_type`, `is_union_type_node`, etc.)

### Python version support

- Python 3.10, 3.11, 3.12, 3.13, 3.13t, 3.14, and 3.14t
