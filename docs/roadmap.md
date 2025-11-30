# Roadmap

This document outlines planned features and enhancements for typing-graph, organized by theme rather than strict priority order.

## Type inspection controls

### Type allow lists and block lists

Real-world applications often need to restrict which types the library can inspect. A validation framework might only want to process types from specific modules. A serialization library might need to reject types that cannot safely convert.

**Goals:**

- Define which types the inspection allows
- Specify behavior when encountering disallowed types (error, skip, substitute)
- Support both allow list ("only these") and block list ("not these") patterns
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
- Define depth limits per branch or globally
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
- Early termination when the traversal finds a target

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

[Pydantic](https://docs.pydantic.dev/) is the most widely used validation library in Python. While typing-graph builds on Pydantic's typing-inspection library, deeper integration would expose Pydantic-specific metadata.

**Goals:**

- Extract Pydantic field metadata (`Field()` options, validators, serializers)
- Support only Pydantic v2+
- Map Pydantic constraints to typing-graph's constraint vocabulary
- Recognize `BeforeValidator`, `AfterValidator`, and other Pydantic-specific annotations

**Use cases:**

- Analyzing Pydantic models alongside plain dataclasses in unified tooling
- Extracting validation rules for schema generation
- Building adapters between Pydantic and other validation frameworks

[annotated-types]: https://github.com/annotated-types/annotated-types
