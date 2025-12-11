"""Configuration for type introspection."""

# pyright: reportAny=false, reportExplicitAny=false

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Final
from typing_extensions import Format


class EvalMode(Enum):
    """How to evaluate annotations during introspection.

    Attributes:
        EAGER: Fully resolve annotations, fail on errors.
        DEFERRED: Use ForwardRef for unresolvable annotations (default).
        STRINGIFIED: Keep annotations as strings, resolve lazily.
    """

    EAGER = auto()
    DEFERRED = auto()
    STRINGIFIED = auto()


EVAL_MODE_TO_FORMAT: Final[dict[EvalMode, Format]] = {
    EvalMode.EAGER: Format.VALUE,
    EvalMode.DEFERRED: Format.FORWARDREF,
    EvalMode.STRINGIFIED: Format.STRING,
}


@dataclass(slots=True, frozen=True)
class InspectConfig:
    """Configuration for type introspection.

    Attributes:
        eval_mode: How to evaluate annotations (default: DEFERRED).
        globalns: Global namespace for forward reference resolution.
        localns: Local namespace for forward reference resolution.
        max_depth: Maximum recursion depth (None = unlimited).
        include_private: Include private members starting with underscore.
        include_inherited: Include inherited members from base classes.
        include_methods: Include methods in class inspection.
        include_class_vars: Include ClassVar annotations.
        include_instance_vars: Include instance variable annotations.
        hoist_metadata: Move Annotated metadata to node.metadata.
        normalize_unions: Represent all union types as UnionNode regardless
            of runtime form. When True (default), both types.UnionType and
            typing.Union produce UnionNode, matching Python 3.14 behavior.
            Set to False to preserve native runtime representation. Use
            :func:`~typing_graph.is_union_node` to check if a node represents
            a union regardless of the normalization setting.
        include_source_locations: Track source file and line numbers
            (disabled by default as inspect.getsourcelines is expensive).

    Note:
        **Cache behavior:** Only the default ``InspectConfig()`` singleton uses
        the global inspection cache. Creating a custom config instance (even with
        identical values) bypasses the cache entirely. This ensures configuration
        isolation but may impact performance for repeated inspections with custom
        configs. If you need caching with custom settings, consider reusing the
        same config instance across calls.
    """

    # Annotation evaluation strategy
    eval_mode: EvalMode = EvalMode.DEFERRED

    # Namespaces for resolution
    globalns: dict[str, Any] | None = None
    localns: dict[str, Any] | None = None

    # Recursion control
    max_depth: int | None = None  # None = unlimited

    # Class inspection options
    include_private: bool = False
    include_inherited: bool = True
    include_methods: bool = True
    include_class_vars: bool = True
    include_instance_vars: bool = True

    # Annotated handling
    hoist_metadata: bool = True  # Move Annotated metadata to node.metadata

    # Union normalization
    normalize_unions: bool = True  # All unions → UnionNode (matches Python 3.14)

    # Source tracking (disabled by default - inspect.getsourcelines is expensive)
    include_source_locations: bool = False

    def get_format(self) -> Format:
        """Map eval_mode to typing_extensions.Format.

        Returns:
            The Format corresponding to the current eval_mode.
        """
        return EVAL_MODE_TO_FORMAT[self.eval_mode]


DEFAULT_CONFIG: Final[InspectConfig] = InspectConfig()

# Sentinel for detecting missing attributes
MISSING: Final[object] = object()
