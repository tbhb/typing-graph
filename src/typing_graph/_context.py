"""Internal context for type introspection."""

# pyright: reportAny=false, reportExplicitAny=false

import inspect
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ._node import SourceLocation, is_annotated_type_node

if TYPE_CHECKING:
    from ._config import InspectConfig
    from ._node import TypeNode

_logger = logging.getLogger(__name__)


@dataclass(slots=True)
class InspectContext:
    """Internal context for tracking introspection state.

    Attributes:
        config: The inspection configuration.
        depth: Current recursion depth.
        seen: Mapping of annotation id to TypeNode for cycle detection.
        resolving: Set of forward reference strings currently being resolved.
    """

    config: "InspectConfig"
    depth: int = 0
    seen: dict[int, "TypeNode"] = field(
        default_factory=dict
    )  # id -> node (cycle detection)
    resolving: set[str] = field(default_factory=set)

    def child(self) -> "InspectContext":
        """Create a child context with incremented depth.

        Returns:
            A new context sharing state but with incremented depth.
        """
        return InspectContext(
            config=self.config,
            depth=self.depth + 1,
            seen=self.seen,
            resolving=self.resolving,
        )

    def check_max_depth_exceeded(self) -> bool:
        """Check if we've exceeded max depth.

        Returns:
            True if depth is within limits, False if exceeded.
        """
        if self.config.max_depth is None:
            return True
        return self.depth < self.config.max_depth


def extract_field_metadata(type_node: "TypeNode") -> tuple[object, ...]:
    """Extract metadata from a type node for field definition.

    Prefers annotations from AnnotatedType, falls back to node metadata.

    Args:
        type_node: The type node to extract metadata from.

    Returns:
        A tuple of metadata objects, empty if no metadata found.
    """
    if is_annotated_type_node(type_node):
        return type_node.annotations
    return type_node.metadata


def get_source_location(obj: Any, config: "InspectConfig") -> SourceLocation | None:
    """Extract source location for an object if enabled.

    Args:
        obj: The object to get source location for.
        config: The inspection configuration.

    Returns:
        A SourceLocation if source tracking is enabled and successful,
        None otherwise.
    """
    if not config.include_source_locations:
        return None

    module = getattr(obj, "__module__", None)
    qualname = getattr(obj, "__qualname__", None)

    file = None
    lineno = None
    try:
        file = inspect.getfile(obj)
        _source_lines, lineno = inspect.getsourcelines(obj)
    except (TypeError, OSError):
        pass

    if module or qualname or file or lineno:
        return SourceLocation(
            module=module,
            qualname=qualname,
            file=file,
            lineno=lineno,
        )

    return None
