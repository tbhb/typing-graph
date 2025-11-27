"""Module-level inspection."""

# pyright: reportAny=false, reportExplicitAny=false

import logging
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ParamSpec, TypeVar
from typing_extensions import TypeAliasType, get_annotations

from ._config import DEFAULT_CONFIG, InspectConfig
from ._context import InspectContext
from ._inspect_class import ClassInspectResult, inspect_class
from ._inspect_function import inspect_function
from ._inspect_type import (
    _inspect_type,  # pyright: ignore[reportPrivateUsage]
    inspect_type_alias,
)
from ._node import is_type_param_node

if TYPE_CHECKING:
    import types

    from ._node import (
        FunctionNode,
        GenericAlias,
        ParamSpecNode,
        TypeAliasNode,
        TypeNode,
        TypeVarNode,
        TypeVarTupleNode,
    )

_logger = logging.getLogger(__name__)

if sys.version_info >= (3, 11):  # pragma: no cover
    from typing import TypeVarTuple  # pyright: ignore[reportUnreachable]
else:  # pragma: no cover
    from typing_extensions import TypeVarTuple


@dataclass(slots=True)
class ModuleTypes:
    """Collection of types discovered in a module.

    Attributes:
        classes: Mapping of class names to their inspection results.
        functions: Mapping of function names to their FunctionNode.
        type_aliases: Mapping of type alias names to their nodes.
        type_vars: Mapping of type variable names to their nodes.
        constants: Mapping of annotated constant names to their TypeNode.
    """

    classes: dict[str, ClassInspectResult] = field(default_factory=dict)
    functions: dict[str, "FunctionNode"] = field(default_factory=dict)
    type_aliases: dict[str, "GenericAlias | TypeAliasNode"] = field(
        default_factory=dict
    )
    type_vars: dict[str, "TypeVarNode | ParamSpecNode | TypeVarTupleNode"] = field(
        default_factory=dict
    )
    constants: dict[str, "TypeNode"] = field(default_factory=dict)


def inspect_module(
    module: "types.ModuleType",
    *,
    config: InspectConfig | None = None,
    include_imported: bool = False,
) -> ModuleTypes:
    """Inspect all public types in a module.

    Discovers and inspects all classes, functions, type aliases, type variables,
    and annotated constants in a module.

    Args:
        module: The module to inspect.
        config: Introspection configuration. Uses defaults if None.
        include_imported: Whether to include items imported from other modules
            (default False).

    Returns:
        A ModuleTypes containing all discovered types organized by category.
    """
    config = config if config is not None else DEFAULT_CONFIG
    ctx = InspectContext(config=config)
    format_val = ctx.config.get_format()

    result = ModuleTypes()
    module_name = module.__name__

    # Get module-level annotations
    try:
        module_annotations = get_annotations(
            module,
            format=format_val,
            globals=vars(module),
            locals=ctx.config.localns,
        )
    except Exception:  # noqa: BLE001 - Intentionally broad for robust module handling
        _logger.debug(
            "Failed to get annotations for module %s", module_name, exc_info=True
        )
        module_annotations = {}

    # Process module contents
    for name in dir(module):
        if not config.include_private and name.startswith("_"):
            continue

        try:
            obj = getattr(module, name)
        except AttributeError:  # pragma: no cover
            continue

        # Skip imported items unless requested
        if not include_imported:
            obj_module = getattr(obj, "__module__", None)
            if obj_module is not None and obj_module != module_name:
                continue

        # Classify and inspect
        _inspect_module_item(name, obj, config, ctx, result)

    # Process module annotations as constants
    for name, ann in module_annotations.items():
        if not config.include_private and name.startswith("_"):
            continue

        if name not in result.classes and name not in result.functions:
            result.constants[name] = _inspect_type(ann, ctx.child())

    return result


def _inspect_module_item(
    name: str,
    obj: object,
    config: InspectConfig,
    ctx: InspectContext,
    result: ModuleTypes,
) -> None:
    """Inspect a single module item and add it to the result."""
    if isinstance(obj, type):
        result.classes[name] = inspect_class(obj, config=config)
        return

    # Check for type variables first (they are not callable in Python 3.10+)
    is_typevar = isinstance(obj, (TypeVar, ParamSpec)) or (
        # TypeVarTuple may be None in Python 3.10
        TypeVarTuple is not None  # pyright: ignore[reportUnnecessaryComparison]
        and isinstance(obj, TypeVarTuple)
    )
    if is_typevar:
        tv_node = _inspect_type(obj, ctx.child())
        # TypeVar/ParamSpec/TypeVarTuple always produce TypeParamNode
        if is_type_param_node(tv_node):
            result.type_vars[name] = tv_node
        return

    # TypeAliasType check must come before callable check because TypeAliasType
    # is callable (supports subscripting like MyAlias[T])
    # TypeAliasType may be None in Python 3.10
    if TypeAliasType is not None and isinstance(obj, TypeAliasType):  # pyright: ignore[reportUnnecessaryComparison]
        # PEP 695 type alias
        result.type_aliases[name] = inspect_type_alias(obj, config=config)
        return

    if callable(obj) and not isinstance(obj, type):
        # Function
        result.functions[name] = inspect_function(obj, config=config)
