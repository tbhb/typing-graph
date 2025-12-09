from typing import TYPE_CHECKING

import pytest

from typing_graph import EvalMode, InspectConfig, TypeNode, cache_clear
from typing_graph._node import (
    ConcreteNode,
    SubscriptedGenericNode,
    is_concrete_node,
    is_generic_node,
    is_subscripted_generic_node,
)

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(autouse=True)
def clear_type_cache() -> "Generator[None]":
    """Clear type inspection cache before and after each test."""
    cache_clear()
    yield
    cache_clear()


def assert_concrete_type(node: TypeNode, expected_cls: type) -> ConcreteNode:
    """Assert node is ConcreteNode with expected class."""
    assert is_concrete_node(node), f"Expected ConcreteNode, got {type(node).__name__}"
    assert node.cls is expected_cls, f"Expected {expected_cls}, got {node.cls}"
    return node


def assert_subscripted_generic(
    node: TypeNode,
    origin_cls: type,
    arg_count: int | None = None,
) -> SubscriptedGenericNode:
    """Assert node is SubscriptedGenericNode with expected origin."""
    assert is_subscripted_generic_node(node), (
        f"Expected SubscriptedGenericNode, got {type(node).__name__}"
    )
    assert is_generic_node(node.origin), "Expected GenericNode origin"
    assert node.origin.cls is origin_cls
    if arg_count is not None:
        assert len(node.args) == arg_count
    return node


def assert_no_extras(node: TypeNode) -> None:
    """Assert node has no metadata or qualifiers."""
    assert not node.metadata, f"Unexpected metadata: {node.metadata}"
    assert node.qualifiers == frozenset(), f"Unexpected qualifiers: {node.qualifiers}"


@pytest.fixture
def eager_config() -> InspectConfig:
    """Config with eager forward reference evaluation."""
    return InspectConfig(eval_mode=EvalMode.EAGER)


@pytest.fixture
def deferred_config() -> InspectConfig:
    """Config with deferred forward reference evaluation."""
    return InspectConfig(eval_mode=EvalMode.DEFERRED)


@pytest.fixture
def full_inspection_config() -> InspectConfig:
    """Config that inspects all class members."""
    return InspectConfig(
        include_private=True,
        include_inherited=True,
        include_methods=True,
        include_class_vars=True,
        include_instance_vars=True,
    )
