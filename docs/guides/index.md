# How-to guides

This section contains task-oriented guides that show how to achieve specific goals. Use these when you know what you want to do and need to find out how.

## By task

### Working with metadata

These guides cover [`MetadataCollection`][typing_graph.MetadataCollection] operations:

| Task                         | Guide                                                   |
| ---------------------------- | ------------------------------------------------------- |
| Find metadata by type        | [Querying metadata](metadata-queries.md)                |
| Apply custom predicates      | [Filtering metadata](metadata-filtering.md)             |
| Combine and sort collections | [Transforming metadata](metadata-transformations.md)    |
| Real-world patterns          | [Metadata recipes](metadata-recipes.md)                 |

### Traversing and configuring

| Task                         | Guide                                                   |
| ---------------------------- | ------------------------------------------------------- |
| Visit all nodes in a type    | [Walking the type graph](walking-type-graph.md)         |
| Filter with type narrowing   | [Filtering with walk()](filtering-with-walk.md)         |
| Control inspection behavior  | [Configuration options](configuration.md)               |

## All guides

[Querying metadata](metadata-queries.md)
:   Find, get, and count metadata items by type using [`MetadataCollection`][typing_graph.MetadataCollection]'s query methods.

[Filtering metadata](metadata-filtering.md)
:   Filter collections using predicates, type constraints, and runtime-checkable protocols.

[Transforming metadata](metadata-transformations.md)
:   Combine, sort, deduplicate, and transform metadata collections.

[Metadata recipes](metadata-recipes.md)
:   Real-world patterns for validation extraction, documentation generation, and troubleshooting.

[Walking the type graph](walking-type-graph.md)
:   Traverse the [type graph](../reference/glossary.md#type-graph) recursively using the [`children()`][typing_graph.TypeNode.children] method to process nested types.

[Filtering with walk()](filtering-with-walk.md)
:   Filter type graphs using [`walk()`][typing_graph.walk] with built-in type guards, custom [`TypeIs`][typing_extensions.TypeIs] predicates, and depth limits.

[Configuration options](configuration.md)
:   Customize inspection behavior with [`InspectConfig`][typing_graph.InspectConfig], [forward reference](../reference/glossary.md#forward-reference) modes, and cache management.

## Related resources

- **New to typing-graph?** Start with the [tutorials](../tutorials/index.md)
- **Want deeper understanding?** Read the [explanations](../explanation/index.md)
- **Looking up API details?** See the [API reference](../reference/api.md)
