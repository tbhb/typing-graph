"""Tests for documentation examples in docs/guides/."""

from pathlib import Path  # noqa: TC003

import pytest
from pytest_examples import CodeExample, EvalExample, find_examples

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


def get_common_globals() -> dict[str, object]:
    """Provide common imports for documentation examples."""
    from dataclasses import dataclass, field
    from typing import Annotated, Any, NamedTuple, TypedDict
    from typing_extensions import Doc, NotRequired, Required

    import typing_graph
    from typing_graph import (
        AnnotatedType,
        ConcreteType,
        DataclassFieldDef,
        DataclassType,
        EvalMode,
        ForwardRef,
        FunctionNode,
        GenericTypeNode,
        InspectConfig,
        NamedTupleType,
        Parameter,
        SignatureNode,
        SubscriptedGeneric,
        TypedDictType,
        TypeNode,
        UnionType,
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

    return {
        # Standard library
        "Annotated": Annotated,
        "Any": Any,
        "dataclass": dataclass,
        "field": field,
        "NamedTuple": NamedTuple,
        "Required": Required,
        "NotRequired": NotRequired,
        "TypedDict": TypedDict,
        # typing_extensions
        "Doc": Doc,
        # typing_graph module
        "typing_graph": typing_graph,
        # typing_graph types
        "AnnotatedType": AnnotatedType,
        "ConcreteType": ConcreteType,
        "DataclassFieldDef": DataclassFieldDef,
        "DataclassType": DataclassType,
        "EvalMode": EvalMode,
        "ForwardRef": ForwardRef,
        "FunctionNode": FunctionNode,
        "GenericTypeNode": GenericTypeNode,
        "InspectConfig": InspectConfig,
        "NamedTupleType": NamedTupleType,
        "Parameter": Parameter,
        "SignatureNode": SignatureNode,
        "SubscriptedGeneric": SubscriptedGeneric,
        "TypedDictType": TypedDictType,
        "TypeNode": TypeNode,
        "UnionType": UnionType,
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

    return None


@pytest.mark.docexamples
@pytest.mark.parametrize("example", find_examples("docs/guides"), ids=str)
def test_guide_examples(example: CodeExample, eval_example: EvalExample) -> None:
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
