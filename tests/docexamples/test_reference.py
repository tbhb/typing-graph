"""Tests for documentation examples in docs/ root-level reference files."""

from pathlib import Path  # noqa: TC003
from typing import Protocol

import pytest
from pytest_examples import CodeExample, EvalExample, find_examples

from .conftest import check_version_skip

# Patterns that indicate non-executable examples
SKIP_PATTERNS = [
    "pip install",
    "uv add",
    "poetry add",
    "# Error!",
    "# Raises",
    "# This fails",
    "# snippet",  # Illustrative code snippets that aren't meant to be executed
]

# Root-level documentation files to test
ROOT_DOC_FILES = [
    "docs/metadata-collection.md",
]


def get_common_globals() -> dict[str, object]:
    """Provide common imports for documentation examples."""
    from dataclasses import dataclass, field
    from typing import Annotated, Any, NamedTuple, TypedDict
    from typing_extensions import Doc, NotRequired, Required

    import typing_graph
    from typing_graph import (
        AnnotatedNode,
        ConcreteNode,
        DataclassFieldDef,
        DataclassNode,
        EvalMode,
        ForwardRefNode,
        FunctionNode,
        GenericTypeNode,
        InspectConfig,
        NamedTupleNode,
        Parameter,
        SignatureNode,
        SubscriptedGenericNode,
        TypedDictNode,
        TypeNode,
        UnionNode,
        cache_clear,
        cache_info,
        inspect_class,
        inspect_dataclass,
        inspect_function,
        inspect_named_tuple,
        inspect_signature,
        inspect_type,
        inspect_typed_dict,
    )
    from typing_graph._metadata import (
        MetadataCollection,
        MetadataNotFoundError,
        ProtocolNotRuntimeCheckableError,
        SupportsLessThan,
    )

    return {
        # Standard library
        "Annotated": Annotated,
        "Any": Any,
        "dataclass": dataclass,
        "field": field,
        "NamedTuple": NamedTuple,
        "Protocol": Protocol,
        "Required": Required,
        "NotRequired": NotRequired,
        "TypedDict": TypedDict,
        # typing_extensions
        "Doc": Doc,
        # typing_graph module
        "typing_graph": typing_graph,
        # typing_graph types
        "AnnotatedNode": AnnotatedNode,
        "ConcreteNode": ConcreteNode,
        "DataclassFieldDef": DataclassFieldDef,
        "DataclassNode": DataclassNode,
        "EvalMode": EvalMode,
        "ForwardRefNode": ForwardRefNode,
        "FunctionNode": FunctionNode,
        "GenericTypeNode": GenericTypeNode,
        "InspectConfig": InspectConfig,
        "NamedTupleNode": NamedTupleNode,
        "Parameter": Parameter,
        "SignatureNode": SignatureNode,
        "SubscriptedGenericNode": SubscriptedGenericNode,
        "TypedDictNode": TypedDictNode,
        "TypeNode": TypeNode,
        "UnionType": UnionNode,
        # typing_graph functions
        "cache_clear": cache_clear,
        "cache_info": cache_info,
        "inspect_class": inspect_class,
        "inspect_dataclass": inspect_dataclass,
        "inspect_function": inspect_function,
        "inspect_named_tuple": inspect_named_tuple,
        "inspect_signature": inspect_signature,
        "inspect_type": inspect_type,
        "inspect_typed_dict": inspect_typed_dict,
        # MetadataCollection types
        "MetadataCollection": MetadataCollection,
        "MetadataNotFoundError": MetadataNotFoundError,
        "ProtocolNotRuntimeCheckableError": ProtocolNotRuntimeCheckableError,
        "SupportsLessThan": SupportsLessThan,
    }


# Store accumulated globals per file to allow examples to build on each other
_file_globals: dict[Path, dict[str, object]] = {}


def _get_globals_for_file(file_path: Path) -> dict[str, object]:
    """Get or create accumulated globals for a file."""
    if file_path not in _file_globals:
        _file_globals[file_path] = get_common_globals()
    return _file_globals[file_path]


def _should_skip_example(example: CodeExample) -> str | None:
    """Check if an example should be skipped, return reason or None."""
    prefix_tags = example.prefix_tags()
    if prefix_tags:
        python_tags = {"python", "py", "pycon"}
        if not prefix_tags & python_tags:
            return f"Non-Python example: {prefix_tags}"

    if any(pattern in example.source for pattern in SKIP_PATTERNS):
        return "Non-executable example"

    # Version-specific examples
    if version_skip := check_version_skip(example.source):
        return version_skip

    return None


def _get_reference_examples() -> list[CodeExample]:
    """Get all examples from root-level reference documentation files."""
    all_examples: list[CodeExample] = []
    for doc_file in ROOT_DOC_FILES:
        all_examples.extend(find_examples(doc_file))
    return all_examples


@pytest.mark.docexamples
@pytest.mark.parametrize("example", _get_reference_examples(), ids=str)
def test_reference_examples(example: CodeExample, eval_example: EvalExample) -> None:
    skip_reason = _should_skip_example(example)
    if skip_reason:
        pytest.skip(skip_reason)

    # Get accumulated globals for this file (allows examples to build on each other)
    file_path = example.path
    module_globals = _get_globals_for_file(file_path)

    # Run the example with accumulated state
    new_globals = eval_example.run(example, module_globals=module_globals)

    # Update accumulated globals with new definitions from this example
    module_globals.update(new_globals)
