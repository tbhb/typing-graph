"""Namespace extraction utilities for forward reference resolution."""

# Namespace dicts are inherently dict[str, Any] containing arbitrary Python objects.
# These suppressions are required for __dict__, __globals__, and dynamic attribute
# access - this is the correct type for namespaces, not a workaround.
# pyright: reportAny=false, reportExplicitAny=false, reportUnknownArgumentType=false

import dataclasses
import sys
from types import ModuleType
from typing import TYPE_CHECKING, Any, TypeAlias

if TYPE_CHECKING:
    from collections.abc import Callable

    from ._config import InspectConfig

NamespacePair: TypeAlias = tuple[dict[str, Any], dict[str, Any]]
"""Type alias for the (globalns, localns) tuple returned by extraction functions."""

NamespaceSource: TypeAlias = "type[Any] | Callable[..., Any] | ModuleType"
"""Type alias for valid namespace extraction sources (class, function, or module)."""

# Expected number of parts when splitting "ClassName.method_name"
_QUALNAME_PARTS_WITH_CLASS = 2


def _add_type_params_to_namespace(obj: object, localns: dict[str, Any]) -> None:
    """Add PEP 695 type parameters from an object to a local namespace.

    Args:
        obj: The class or function to extract type parameters from.
        localns: The local namespace dict to add type parameters to.
    """
    type_params = getattr(obj, "__type_params__", ())
    # Guard against non-iterable descriptors (e.g., in typing module classes)
    if not isinstance(type_params, tuple):
        return
    for param in type_params:  # pyright: ignore[reportUnknownVariableType]
        param_name = getattr(param, "__name__", None)
        if param_name is not None:
            localns[param_name] = param


def _resolve_owning_class(func: "Callable[..., Any]") -> type | None:
    """Attempt to resolve the owning class from a method's qualname.

    For methods, the qualname has the form "ClassName.method_name" or
    "Outer.Inner.method_name" for nested classes. This function attempts
    to resolve the class by traversing from the globals dict.

    Args:
        func: The function (method) to resolve owning class for.

    Returns:
        The owning class if resolution succeeds, None otherwise.
        Resolution fails for nested classes with complex qualnames,
        dynamically created methods, or when globals are unavailable.
    """
    qualname = getattr(func, "__qualname__", None)
    globals_dict = getattr(func, "__globals__", None)

    # Early validation: need both qualname and globals dict
    if qualname is None or not isinstance(globals_dict, dict):
        return None

    # Split qualname: "ClassName.method_name" or "Outer.Inner.method_name"
    parts = qualname.rsplit(".", 1)
    if len(parts) != _QUALNAME_PARTS_WITH_CLASS:
        return None  # Top-level function, no class

    class_qualname = parts[0]
    root_parts = class_qualname.split(".")

    # Traverse from globals to find the class
    return _traverse_to_class(globals_dict, root_parts)


def _traverse_to_class(globals_dict: dict[str, Any], parts: list[str]) -> type | None:
    """Traverse from globals dict through attribute chain to find a class.

    Args:
        globals_dict: The globals dict to start from.
        parts: The parts of the qualname path to traverse.

    Returns:
        The class if found, None otherwise.
    """
    if not parts:
        return None

    try:
        obj = globals_dict.get(parts[0])
        for part in parts[1:]:
            if obj is None:
                return None
            obj = getattr(obj, part, None)
        return obj if isinstance(obj, type) else None
    except (TypeError, AttributeError):
        return None


def extract_class_namespace(cls: type[Any]) -> NamespacePair:
    """Extract global and local namespaces from a class.

    The global namespace is extracted from the class's defining module via
    ``sys.modules[cls.__module__].__dict__``. The local namespace includes
    the class itself under its ``__name__`` to enable self-referential type
    resolution, plus any type parameters from ``__type_params__`` (PEP 695).

    Args:
        cls: The class to extract namespaces from.

    Returns:
        A tuple of (globalns, localns) dicts. The globalns is a copy of the
        module's namespace; the localns is a new dict containing the class
        and any type parameters.
    """
    globalns: dict[str, Any] = {}
    localns: dict[str, Any] = {}

    # Extract global namespace from module
    module_name = getattr(cls, "__module__", None)
    if module_name is not None:
        module = sys.modules.get(module_name)
        if module is not None:
            module_dict = getattr(module, "__dict__", None)
            if isinstance(module_dict, dict):
                globalns = dict(module_dict)

    # Add class itself to local namespace for self-referential resolution
    class_name = getattr(cls, "__name__", None)
    if class_name is not None:
        localns[class_name] = cls

    # Add type parameters (PEP 695, Python 3.12+)
    _add_type_params_to_namespace(cls, localns)

    return globalns, localns


def extract_function_namespace(
    func: "Callable[..., Any]",
) -> NamespacePair:
    """Extract global and local namespaces from a function.

    The global namespace is extracted from ``func.__globals__``. For methods,
    the system attempts to resolve the owning class via ``__qualname__`` parsing
    and includes it in the local namespace if found. Type parameters from
    ``__type_params__`` (PEP 695) are also included in the local namespace.

    Args:
        func: The function to extract namespaces from.

    Returns:
        A tuple of (globalns, localns) dicts. The globalns is a copy of the
        function's globals; the localns is a new dict containing the owning
        class (if a method) and any type parameters.
    """
    globalns: dict[str, Any] = {}
    localns: dict[str, Any] = {}

    # Extract global namespace from __globals__
    func_globals = getattr(func, "__globals__", None)
    if isinstance(func_globals, dict):
        globalns = dict(func_globals)

    # Attempt to resolve owning class for methods
    owning_class = _resolve_owning_class(func)
    if owning_class is not None:
        class_name = getattr(owning_class, "__name__", None)
        if class_name is not None:
            localns[class_name] = owning_class

    # Add type parameters (PEP 695, Python 3.12+)
    _add_type_params_to_namespace(func, localns)

    return globalns, localns


def extract_module_namespace(
    module: ModuleType,
) -> NamespacePair:
    """Extract global and local namespaces from a module.

    The global namespace is the module's ``__dict__``. The local namespace
    is always empty for modules.

    Args:
        module: The module to extract namespaces from.

    Returns:
        A tuple of (globalns, localns) dicts. The globalns is a copy of the
        module's namespace; the localns is always an empty dict for modules.
    """
    globalns: dict[str, Any] = {}
    localns: dict[str, Any] = {}

    module_dict = getattr(module, "__dict__", None)
    if isinstance(module_dict, dict):
        globalns = dict(module_dict)

    return globalns, localns


def extract_namespace(source: NamespaceSource) -> NamespacePair:
    """Extract namespaces from any valid source object.

    Dispatches to the appropriate extraction function based on source type:

    - For classes: uses ``extract_class_namespace``
    - For callables (functions/methods): uses ``extract_function_namespace``
    - For modules: uses ``extract_module_namespace``

    Args:
        source: A class, function, or module.

    Returns:
        A tuple of (globalns, localns) dicts.

    Raises:
        TypeError: If source is not a class, callable, or module.
    """
    if isinstance(source, type):
        return extract_class_namespace(source)

    if isinstance(source, ModuleType):
        return extract_module_namespace(source)

    if callable(source):
        return extract_function_namespace(source)

    # Pyright correctly identifies this as unreachable based on the type signature,
    # but we keep this guard for runtime safety when called from untyped code
    msg = f"source must be a class, callable, or module, got {type(source).__name__!r}"  # pyright: ignore[reportUnreachable]
    raise TypeError(msg)


def merge_namespaces(
    auto_globalns: dict[str, Any],
    auto_localns: dict[str, Any],
    user_globalns: dict[str, Any] | None,
    user_localns: dict[str, Any] | None,
) -> NamespacePair:
    """Merge auto-detected and user-provided namespaces.

    User-provided values take precedence over auto-detected values.
    This function creates new dicts and does not modify the inputs.

    Args:
        auto_globalns: Auto-detected global namespace.
        auto_localns: Auto-detected local namespace.
        user_globalns: User-provided global namespace (may be None).
        user_localns: User-provided local namespace (may be None).

    Returns:
        A tuple of merged (globalns, localns) dicts.
    """
    merged_globalns = {**auto_globalns, **(user_globalns or {})}
    merged_localns = {**auto_localns, **(user_localns or {})}
    return merged_globalns, merged_localns


def _apply_namespace(
    auto_globalns: dict[str, Any],
    auto_localns: dict[str, Any],
    config: "InspectConfig",
) -> "InspectConfig":
    """Apply extracted namespaces to an InspectConfig.

    This is an internal helper that handles the common logic of merging
    auto-detected namespaces with user-provided namespaces and creating
    a new config.

    Args:
        auto_globalns: Auto-detected global namespace.
        auto_localns: Auto-detected local namespace.
        config: The InspectConfig to update with merged namespaces.

    Returns:
        A new config with merged globalns and localns.
    """
    merged_globalns, merged_localns = merge_namespaces(
        auto_globalns,
        auto_localns,
        config.globalns,
        config.localns,
    )
    return dataclasses.replace(
        config,
        globalns=merged_globalns,
        localns=merged_localns,
    )


def apply_class_namespace(cls: type[Any], config: "InspectConfig") -> "InspectConfig":
    """Apply auto-namespace extraction from a class to an InspectConfig.

    This is a convenience function that combines namespace extraction, merging,
    and config replacement into a single call. It extracts namespaces from the
    class and merges them with user-provided namespaces in the config, where
    user values take precedence.

    Args:
        cls: The class to extract namespaces from.
        config: The InspectConfig to update with merged namespaces.

    Returns:
        A new config with merged globalns and localns. If config.auto_namespace
        is False, returns the config unchanged.
    """
    if not config.auto_namespace:
        return config

    auto_globalns, auto_localns = extract_class_namespace(cls)
    return _apply_namespace(auto_globalns, auto_localns, config)


def apply_function_namespace(
    func: "Callable[..., Any]", config: "InspectConfig"
) -> "InspectConfig":
    """Apply auto-namespace extraction from a function to an InspectConfig.

    This is a convenience function that combines namespace extraction, merging,
    and config replacement into a single call. It extracts namespaces from the
    function and merges them with user-provided namespaces in the config, where
    user values take precedence.

    Args:
        func: The function to extract namespaces from.
        config: The InspectConfig to update with merged namespaces.

    Returns:
        A new config with merged globalns and localns. If config.auto_namespace
        is False, returns the config unchanged.
    """
    if not config.auto_namespace:
        return config

    auto_globalns, auto_localns = extract_function_namespace(func)
    return _apply_namespace(auto_globalns, auto_localns, config)
