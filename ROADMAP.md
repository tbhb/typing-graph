# typing-graph roadmap

This document outlines planned features and enhancements for typing-graph. Items are organized by theme rather than strict priority order.

## Design principles

These principles guide feature decisions and explain the library's trade-offs.

**Minimal dependencies.** Standard library first. The only runtime dependencies are `typing-inspection`, `typing-extensions`, and optionally `annotated-types`.

**SOLID, DRY, YAGNI, KISS.** Simplicity wins. A solution covering 90% of use cases beats an elaborate one for edge cases.

**Secure by default.** Explicit opt-in for any behavior that could process untrusted input unsafely or trigger unexpected code paths.

**Measure, don't guess.** No speculative optimizations. Performance work requires profiling data.

**Pay for what you use.** Lazy caching, on-demand traversal, and optional integrations that don't import until needed.

## Metadata querying API

One of the core value propositions of typing-graph is making metadata accessible. While the graph structure captures the full type hierarchy, most users need focused queries: "What constraints apply to this field?" or "Does any nested type have validation metadata?" This API provides ergonomic, type-safe access to metadata throughout the graph.

### Predicate-based filtering

Query metadata using composable predicates that work with Python's type system.

**Goals:**

- Type-safe predicates using generics and TypeIs/TypeGuard for narrowing
- Composable operators (and, or, not) for building complex filters
- Built-in predicates for common patterns (is_instance, has_attr, matches_protocol)
- Short-circuit evaluation for performance

**Use cases:**

- Finding all `Gt(0)` constraints in a model's fields
- Filtering metadata to only annotated-types constraints
- Combining multiple conditions: "Gt constraints on string fields"
- Custom predicates for application-specific metadata types

### Query operations

Standard query patterns with consistent semantics across the API.

**Goals:**

- `find_first(predicate)` - Return first matching metadata with short-circuit, or None
- `find_all(predicate)` - Collect all matching metadata as a sequence
- `exists(predicate)` - Boolean check without materializing results
- `count(predicate)` - Count matches without collecting
- All operations return rich context: the metadata, its containing node, and the path

**Use cases:**

- Extracting the first `Doc()` annotation for documentation generation
- Collecting all validators attached to a TypedDict's fields
- Checking whether any field has a `Ge` constraint before enabling range validation
- Counting how many fields have custom metadata for complexity analysis

### Type-based metadata extraction

Query metadata by type with full type inference support.

**Goals:**

- `get[T](type)` - Extract metadata of a specific type with inferred return type
- `get_all[T](type)` - Collect all metadata instances of a type
- Support for Union types in queries (e.g., `get[Gt | Ge]`)
- Handle inheritance: query for base class, match subclasses
- Integration with `@runtime_checkable` protocols for structural queries

**Use cases:**

- `get[Doc](node)` returns `Doc | None` with correct type inference
- `get_all[Constraint](node)` collects all annotated-types constraints
- Querying for any `SupportsValidation` protocol implementer
- Extracting all JSON schema extension metadata

### Scoped queries

Control query scope to target specific parts of the type graph.

**Goals:**

- Query node-local metadata only (no traversal)
- Query immediate children only (one level)
- Query full subtree with configurable depth limits
- Query along specific paths (e.g., "all metadata on dict values")
- Scope to specific node types (e.g., "metadata on FieldDef nodes only")

**Use cases:**

- Getting only the top-level type's metadata, not nested types
- Extracting field-level metadata without descending into field types
- Querying metadata on union members but not their nested types
- Limiting query depth for performance on deeply nested structures

### annotated-types integration

First-class support for the annotated-types constraint vocabulary.

**Goals:**

- Convenience methods for common constraints and combined queries
- Type-aware queries: numeric constraints on numeric types, string constraints on strings
- Support for custom GroupedMetadata flattening and custom implementations

**Use cases:**

- Building validators from `Gt`, `Le`, `MultipleOf` constraints
- Generating JSON Schema `minimum`/`maximum` from numeric bounds
- Extracting `Len` constraints for string/collection validation
- Processing `Predicate` constraints for custom validation logic

### Result types and context

Rich result objects that provide full context for each match.

**Goals:**

- `QueryMatch` dataclass with: metadata value, containing node, path from root
- Immutable result sequences with lazy evaluation
- Methods to access just values, just nodes, or just paths
- Grouping results by node, by path depth, or by metadata type

**Use cases:**

- Error messages that reference the exact location of problematic metadata
- Building metadata registries indexed by path
- Aggregating constraints by field for validation rule generation
- Debugging which metadata came from which level of type nesting

## Type inspection controls

### Type allowlists and blocklists

Real-world applications often need to restrict which types can be inspected. A validation framework might only want to process types from specific modules. A serialization library might need to reject types that cannot be safely converted.

**Goals:**

- Define which types are permitted during inspection
- Specify behavior when encountering disallowed types (error, skip, substitute)
- Support both allowlist ("only these") and blocklist ("not these") patterns
- Filter by type identity, module origin, or custom predicates

**Use cases:**

- Restricting inspection to application-defined types only
- Excluding third-party types that lack proper annotations
- Preventing inspection of sensitive internal types
- Substituting placeholder nodes for types that cannot be fully inspected

### Inspection depth boundaries

Type graphs can grow unbounded through recursive types, deeply nested generics, or complex class hierarchies. Applications need fine-grained control over where inspection stops.

**Goals:**

- Set boundaries based on type categories (stop at Protocol, stop at generic)
- Define maximum depth per branch or globally
- Distinguish between "stop and mark as terminal" vs "stop and error"
- Support custom boundary conditions via callbacks

**Use cases:**

- Treating Pydantic models as opaque leaves rather than recursing into their fields
- Limiting generic type argument inspection depth
- Creating summary views of complex type hierarchies

### Namespace control for forward references

Forward reference resolution depends on namespace context. Different evaluation strategies need different namespace configurations.

**Goals:**

- Explicit namespace injection for controlled resolution environments
- Module-relative resolution for cross-module type references
- Deferred resolution with configurable retry policies
- Clear error reporting when resolution fails

## Graph traversal API

### Walk function

A generator-based API for iterating through type graphs with control over traversal order and strategy.

**Goals:**

- Pre-order and post-order traversal modes
- Depth-first and breadth-first strategies
- Configurable depth limits with safe defaults
- Predicate-based filtering without interrupting traversal
- Cycle detection to handle recursive types safely

**Use cases:**

- Collecting all metadata annotations in a type hierarchy
- Finding the first occurrence of a specific type pattern
- Transforming types bottom-up (post-order) or top-down (pre-order)
- Early termination when a target is found

### Visitor pattern

A type-dispatched visitor for implementing structured type processing with minimal boilerplate.

**Goals:**

- Automatic dispatch to type-specific visit methods
- Default behavior delegation for unhandled types
- Helper methods for visiting child nodes with path tracking
- Support for stateful visitors that accumulate results

**Use cases:**

- JSON Schema generation from type annotations
- Validation rule extraction from metadata
- Type transformation pipelines
- Documentation generators

### Path tracking

Precise location tracking through type graphs for error reporting and debugging.

**Goals:**

- Immutable path representation from root to current node
- Semantic path segments (field, parameter, type argument, union member, etc.)
- Human-readable path formatting
- Path-based filtering and querying

**Use cases:**

- Error messages that pinpoint exact location in nested types
- Selective processing based on path patterns
- Debugging complex type resolution issues

## Third-party library integration

While typing-graph can inspect any Python type, certain libraries have rich type annotation ecosystems that deserve first-class support. Deep integration means understanding their metadata conventions, field definitions, and validation rules.

### attrs support

[attrs](https://www.attrs.org/) pioneered many patterns that later influenced dataclasses. Full attrs support would bridge typing-graph with the attrs ecosystem.

**Goals:**

- Extract attrs field metadata (`attr.ib` options, validators, converters)
- Recognize attrs-specific validators and map to constraint metadata
- Support both `@attr.s` and `@define` class styles
- Handle attrs' `Factory` and other field default patterns

**Use cases:**

- Migrating attrs validation logic to type-driven approaches
- Generating documentation from attrs field metadata
- Building serialization layers that respect attrs converters

### Pydantic support

[Pydantic](https://docs.pydantic.dev/) is the most widely-used validation library in Python. While typing-graph builds on Pydantic's typing-inspection library, deeper integration would expose Pydantic-specific metadata.

**Goals:**

- Extract Pydantic field metadata (`Field()` options, validators, serializers)
- Support only Pydantic v2+
- Map Pydantic constraints to typing-graph's constraint vocabulary
- Recognize `BeforeValidator`, `AfterValidator`, and other Pydantic-specific annotations

**Use cases:**

- Analyzing Pydantic models alongside plain dataclasses in unified tooling
- Extracting validation rules for schema generation
- Building adapters between Pydantic and other validation frameworks
