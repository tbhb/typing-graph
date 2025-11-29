"""Function and signature inspection."""

# pyright: reportAny=false, reportExplicitAny=false

import inspect
import logging
from typing import TYPE_CHECKING, Any
from typing_extensions import get_annotations

from ._config import DEFAULT_CONFIG, InspectConfig
from ._context import (
    InspectContext,
    extract_field_metadata,
    get_source_location,
)
from ._inspect_type import _inspect_type  # pyright: ignore[reportPrivateUsage]
from ._node import (
    AnyNode,
    FunctionNode,
    Parameter,
    SignatureNode,
    TypeParamNode,
    is_type_param_node,
)

if TYPE_CHECKING:
    from collections.abc import Callable

_logger = logging.getLogger(__name__)


def inspect_function(
    func: "Callable[..., Any]",
    *,
    config: InspectConfig | None = None,
) -> FunctionNode:
    """Inspect a function and return a FunctionNode.

    Args:
        func: The function to inspect.
        config: Introspection configuration. Uses defaults if None.

    Returns:
        A FunctionNode representing the function's structure.
    """
    config = config if config is not None else DEFAULT_CONFIG
    ctx = InspectContext(config=config)

    sig = _inspect_signature(func, ctx)

    # Determine function properties
    is_async = inspect.iscoroutinefunction(func)
    is_generator = inspect.isgeneratorfunction(func)

    # Get decorators (best effort)
    decorators: list[str] = []
    if is_async:
        decorators.append("async")
    if isinstance(func, staticmethod):
        decorators.append("staticmethod")
    if isinstance(func, classmethod):
        decorators.append("classmethod")

    return FunctionNode(
        name=getattr(func, "__name__", "<anonymous>"),
        signature=sig,
        is_async=is_async,
        is_generator=is_generator,
        decorators=tuple(decorators),
        source=get_source_location(func, ctx.config),
    )


def inspect_signature(
    callable_obj: "Callable[..., Any]",
    *,
    config: InspectConfig | None = None,
    follow_wrapped: bool = True,
) -> SignatureNode:
    """Inspect a callable's signature.

    Args:
        callable_obj: The callable to inspect.
        config: Introspection configuration. Uses defaults if None.
        follow_wrapped: Whether to unwrap decorated functions (default True).

    Returns:
        A SignatureNode representing the callable's signature.
    """
    config = config if config is not None else DEFAULT_CONFIG
    ctx = InspectContext(config=config)
    return _inspect_signature(callable_obj, ctx, follow_wrapped=follow_wrapped)


def _inspect_signature(
    callable_obj: "Callable[..., Any]",
    ctx: InspectContext,
    *,
    follow_wrapped: bool = True,
) -> SignatureNode:
    """Inspect a callable's signature using a pre-configured context.

    Called internally by `inspect_signature`, `inspect_function`, and class
    inspection for methods.

    Args:
        callable_obj: The callable to inspect.
        ctx: The inspection context.
        follow_wrapped: Whether to unwrap decorated functions.

    Returns:
        A SignatureNode representing the callable's signature.
    """
    format_val = ctx.config.get_format()

    func = callable_obj
    if follow_wrapped:
        func = inspect.unwrap(callable_obj)

    try:
        annotations = get_annotations(
            func,
            format=format_val,
            globals=ctx.config.globalns,
            locals=ctx.config.localns,
        )
    except (NameError, TypeError, ValueError, SyntaxError, AttributeError):
        _logger.debug("Failed to get annotations for %r", func, exc_info=True)
        annotations = {}

    try:
        sig = inspect.signature(func)
    except (ValueError, TypeError):
        # Can't get signature - return minimal node
        return SignatureNode(
            parameters=(),
            returns=AnyNode(),
        )

    parameters: list[Parameter] = []
    for name, param in sig.parameters.items():
        ann = annotations.get(name, Any)
        type_node = _inspect_type(ann, ctx.child())
        param_metadata = extract_field_metadata(type_node)

        parameters.append(
            Parameter(
                name=name,
                type=type_node,
                kind=param.kind.name,
                default=param.default
                if param.default is not inspect.Parameter.empty
                else None,
                has_default=param.default is not inspect.Parameter.empty,
                metadata=param_metadata,
            )
        )

    return_ann = annotations.get("return", Any)
    returns = _inspect_type(return_ann, ctx.child())

    type_params: list[TypeParamNode] = []
    for tp in getattr(func, "__type_params__", ()):
        tp_node = _inspect_type(tp, ctx.child())
        if is_type_param_node(tp_node):
            type_params.append(tp_node)

    return SignatureNode(
        parameters=tuple(parameters),
        returns=returns,
        type_params=tuple(type_params),
        source=get_source_location(func, ctx.config),
    )
