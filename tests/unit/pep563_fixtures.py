# PEP 563 enables stringified annotations - all annotations become strings at runtime.
# This module MUST have `from __future__ import annotations` to test PEP 563 scenarios.
# Classes defined here are used by test_inspect_class.py for integration testing.
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Generic, NamedTuple, Protocol, TypedDict, TypeVar

# Self-referential dataclass


@dataclass
class TreeNodeDC:
    """Dataclass with self-referential forward reference."""

    value: int
    left: TreeNodeDC | None
    right: TreeNodeDC | None


# Sibling reference dataclasses


@dataclass
class ParentDC:
    """Dataclass referencing sibling class."""

    name: str
    children: list[ChildDC]


@dataclass
class ChildDC:
    """Dataclass referencing sibling class."""

    name: str
    parent: ParentDC | None


# Self-referential TypedDict


class TreeNodeTD(TypedDict):
    """TypedDict with self-referential forward reference."""

    value: int
    left: TreeNodeTD | None
    right: TreeNodeTD | None


# Sibling TypedDicts


class ParentTD(TypedDict):
    """TypedDict referencing sibling class."""

    name: str
    children: list[ChildTD]


class ChildTD(TypedDict):
    """TypedDict referencing sibling class."""

    name: str
    parent: ParentTD | None


# Self-referential NamedTuple


class TreeNodeNT(NamedTuple):
    """NamedTuple with self-referential forward reference."""

    value: int
    left: TreeNodeNT | None
    right: TreeNodeNT | None


# Sibling NamedTuples


class ParentNT(NamedTuple):
    """NamedTuple referencing sibling class."""

    name: str
    children: list[ChildNT]


class ChildNT(NamedTuple):
    """NamedTuple referencing sibling class."""

    name: str
    parent: ParentNT | None


# Self-referential Protocol


class TreeNodeProto(Protocol):
    """Protocol with self-referential forward reference."""

    value: int
    left: TreeNodeProto | None
    right: TreeNodeProto | None


# Sibling Protocols


class ParentProto(Protocol):
    """Protocol referencing sibling class."""

    name: str
    children: list[ChildProto]


class ChildProto(Protocol):
    """Protocol referencing sibling class."""

    name: str
    parent: ParentProto | None


# Generic dataclass with self-reference

T = TypeVar("T")


@dataclass
class GenericNode(Generic[T]):
    """Generic dataclass with self-referential forward reference."""

    value: T
    children: list[GenericNode[T]]


# Plain class with forward references


class PlainNode:
    """Plain class with forward reference annotations."""

    value: int  # pyright: ignore[reportUninitializedInstanceVariable]
    parent: PlainNode | None  # pyright: ignore[reportUninitializedInstanceVariable]
    children: list[PlainNode]  # pyright: ignore[reportUninitializedInstanceVariable]


# Enums for testing


class StatusEnum(Enum):
    """Simple enum for PEP 563 testing."""

    ACTIVE = auto()
    INACTIVE = auto()
    PENDING = auto()


class PriorityEnum(Enum):
    """Enum with typed values."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


# Complex nested structures


@dataclass
class Item:
    """Item referencing Container."""

    name: str
    container: Container | None


@dataclass
class Container:
    """Container holding Items."""

    name: str
    items: list[Item]


# Protocol with method using forward references


class NodeFactory(Protocol):
    """Protocol with method returning forward-referenced type."""

    def create(self, value: int) -> TreeNodeDC:
        """Create a new tree node."""
        ...

    def clone(self, node: TreeNodeDC) -> TreeNodeDC:
        """Clone a tree node."""
        ...


# TypedDict with nested forward references


class NestedTD(TypedDict):
    """TypedDict with deeply nested forward references."""

    items: list[dict[str, TreeNodeTD]]
    mapping: dict[str, ParentTD]


# Function fixtures for PEP 563 scenarios


def create_tree_node(
    value: int,
    left: TreeNodeDC | None = None,
    right: TreeNodeDC | None = None,
) -> TreeNodeDC:
    """Function returning self-referential type."""
    return TreeNodeDC(value=value, left=left, right=right)


def process_tree(node: TreeNodeDC) -> TreeNodeDC | None:
    """Function with forward ref param and return."""
    return node.left


def create_parent(name: str, children: list[ChildDC]) -> ParentDC:
    """Function returning sibling type."""
    return ParentDC(name=name, children=children)


def create_child(name: str, parent: ParentDC | None = None) -> ChildDC:
    """Function returning sibling type."""
    return ChildDC(name=name, parent=parent)


def create_generic_node(
    value: T,
    children: list[GenericNode[T]] | None = None,
) -> GenericNode[T]:
    """Generic function returning self-referential generic type."""
    return GenericNode(value=value, children=children or [])


class NodeService:
    """Class with methods using forward references."""

    def get_node(self, value: int) -> TreeNodeDC:
        """Method returning forward-referenced type."""
        return TreeNodeDC(value=value, left=None, right=None)

    def process(self, node: TreeNodeDC) -> TreeNodeDC | None:
        """Method with forward ref param and return."""
        return node.left

    def create_self(self) -> NodeService:
        """Method with self-referential return type."""
        return NodeService()

    @classmethod
    def from_value(cls, value: int) -> NodeService:  # noqa: ARG003
        """Classmethod with self-referential return type."""
        return cls()

    @staticmethod
    def helper(node: TreeNodeDC) -> int:
        """Staticmethod with forward ref param."""
        return node.value


class NodeCreator:
    """Callable class with __call__ using forward references."""

    def __call__(self, value: int) -> TreeNodeDC:
        """Callable returning forward-referenced type."""
        return TreeNodeDC(value=value, left=None, right=None)


class TreeProcessor:
    """Callable with complex forward reference signature."""

    def __call__(
        self,
        parent: ParentDC,
        child: ChildDC,
    ) -> tuple[ParentDC, list[ChildDC]]:
        """Callable with multiple forward ref params and complex return."""
        return parent, [child]


class Outer:
    """Outer class for nested class testing."""

    class Inner:
        """Inner class with self-referential methods."""

        def get_inner(self) -> Outer.Inner:
            """Method returning containing class."""
            return self

        def get_outer(self) -> Outer:
            """Method returning outer class."""
            return Outer()


# Types for inspect_type() source parameter testing with PEP 563


class SelfRefConfig:
    """Class for testing self-referential inspect_type source parameter."""

    value: int  # pyright: ignore[reportUninitializedInstanceVariable]
    next_config: SelfRefConfig | None  # pyright: ignore[reportUninitializedInstanceVariable]


class LinkedListNode:
    """Self-referential class for testing source parameter resolution."""

    data: str  # pyright: ignore[reportUninitializedInstanceVariable]
    next: LinkedListNode | None  # pyright: ignore[reportUninitializedInstanceVariable]
    prev: LinkedListNode | None  # pyright: ignore[reportUninitializedInstanceVariable]


class SourceParentRef:
    """Parent class for sibling reference testing with source parameter."""

    name: str  # pyright: ignore[reportUninitializedInstanceVariable]
    child: SourceChildRef | None  # pyright: ignore[reportUninitializedInstanceVariable]


class SourceChildRef:
    """Child class for sibling reference testing with source parameter."""

    name: str  # pyright: ignore[reportUninitializedInstanceVariable]
    parent: SourceParentRef | None  # pyright: ignore[reportUninitializedInstanceVariable]


def source_param_func(
    x: TreeNodeDC,  # noqa: ARG001
    y: ParentDC | ChildDC,  # noqa: ARG001
) -> TreeNodeDC | None:
    """Function for testing source parameter with function context."""
    return None


def source_param_func_complex(
    nodes: list[TreeNodeDC],  # noqa: ARG001
    mapping: dict[str, ParentDC],  # noqa: ARG001
) -> dict[str, TreeNodeDC]:
    """Function with complex PEP 563 forward references for source testing."""
    return {}
