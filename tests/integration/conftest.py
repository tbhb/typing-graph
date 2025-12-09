from dataclasses import dataclass, field
from enum import Enum, IntEnum, auto
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Annotated,
    TypeVar,
)
from typing_extensions import Doc

if TYPE_CHECKING:
    from collections.abc import Iterable

import pytest
from annotated_types import Gt, MaxLen, MinLen

_THIS_DIR = Path(__file__).parent


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Add 'integration' marker to all tests in this directory."""
    for item in items:
        if Path(item.fspath).is_relative_to(_THIS_DIR):
            item.add_marker(pytest.mark.integration)


@dataclass(frozen=True, slots=True)
class Pattern:
    """Regex pattern constraint for string validation."""

    regex: str


@dataclass(frozen=True, slots=True)
class Format:
    """String format constraint (email, uri, uuid, etc.)."""

    format: str


@dataclass(frozen=True, slots=True)
class Address:
    """A physical address with validation constraints."""

    street: Annotated[str, MinLen(1), MaxLen(200)]
    city: Annotated[str, MinLen(1), MaxLen(100)]
    zip_code: Annotated[str, Pattern(r"^\d{5}(-\d{4})?$")]
    country: Annotated[str, MinLen(2), MaxLen(2)] = "US"


@dataclass(frozen=True, slots=True)
class Customer:
    """Customer with nested address."""

    name: Annotated[str, MinLen(1), MaxLen(100), Doc("Customer full name")]
    email: Annotated[str, Format("email")]
    address: Address | None = None


@dataclass(frozen=True, slots=True)
class OrderItem:
    """Line item in an order with numeric constraints."""

    product_id: Annotated[str, MinLen(1), Pattern(r"^SKU-\d+$")]
    quantity: Annotated[int, Gt(0)]
    unit_price: Annotated[float, Gt(0)]


@dataclass(frozen=True, slots=True)
class Order:
    """Order with customer and items (demonstrating nested structure)."""

    id: Annotated[str, Pattern(r"^ORD-\d+$")]
    customer: Customer
    items: Annotated[list[OrderItem], MinLen(1)]
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class TreeNode:
    """Self-referencing tree node (recursive type)."""

    value: Annotated[str, MinLen(1)]
    children: "list[TreeNode]" = field(default_factory=list)


class LogLevel(str, Enum):
    """Log level enum (string-valued)."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class Priority(IntEnum):
    """Priority enum (integer-valued)."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Status(Enum):
    """Status enum (auto-valued)."""

    PENDING = auto()
    ACTIVE = auto()
    COMPLETED = auto()


_T = TypeVar("_T")


def find_metadata_of_type(
    metadata: "Iterable[object]", marker_type: type[_T]
) -> _T | None:
    """Find first metadata item of the given type.

    Args:
        metadata: Iterable of metadata objects (tuple, list, MetadataCollection, etc.).
        marker_type: The type to search for.

    Returns:
        First matching metadata item or None.
    """
    for item in metadata:
        if isinstance(item, marker_type):
            return item
    return None


def find_all_metadata_of_type(
    metadata: "Iterable[object]", marker_type: type[_T]
) -> list[_T]:
    """Find all metadata items of the given type.

    Args:
        metadata: Iterable of metadata objects (tuple, list, MetadataCollection, etc.).
        marker_type: The type to search for.

    Returns:
        List of all matching metadata items.
    """
    return [item for item in metadata if isinstance(item, marker_type)]


def has_metadata_of_type(metadata: "Iterable[object]", marker_type: type[_T]) -> bool:
    """Check if metadata contains an item of the given type.

    Args:
        metadata: Iterable of metadata objects (tuple, list, MetadataCollection, etc.).
        marker_type: The type to search for.

    Returns:
        True if a matching item exists.
    """
    return find_metadata_of_type(metadata, marker_type) is not None
