# Installation

typing-graph requires Python 3.10 or later.

## Basic installation

=== "pip"

    ```bash
    pip install typing-graph
    ```

=== "uv"

    ```bash
    uv add typing-graph
    ```

=== "Poetry"

    ```bash
    poetry add typing-graph
    ```

## Dependencies

typing-graph has minimal dependencies to keep your dependency tree lean:

| Package                                                        | Purpose                                                  |
|----------------------------------------------------------------|----------------------------------------------------------|
| [typing-inspection](https://typing-inspection.pydantic.dev/)   | Low-level type introspection utilities from Pydantic     |
| [typing-extensions](https://typing-extensions.readthedocs.io/) | Backports of typing features for older Python versions   |

## Optional dependencies

### annotated-types

For convenience methods that work with [annotated-types](https://github.com/annotated-types/annotated-types) constraint metadata (like `Gt`, `Lt`, `MinLen`), install with the extra:

=== "pip"

    ```bash
    pip install 'typing-graph[annotated-types]'
    ```

=== "uv"

    ```bash
    uv add 'typing-graph[annotated-types]'
    ```

=== "Poetry"

    ```bash
    poetry add 'typing-graph[annotated-types]'
    ```

## Install from repository

To install the latest development version directly from GitHub:

=== "pip"

    ```bash
    pip install git+https://github.com/tbhb/typing-graph.git
    ```

=== "uv"

    ```bash
    uv add git+https://github.com/tbhb/typing-graph.git
    ```

=== "Poetry"

    ```bash
    poetry add git+https://github.com/tbhb/typing-graph.git
    ```
