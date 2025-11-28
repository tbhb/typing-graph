"""Class inspection for various Python class types."""

# pyright: reportAny=false, reportExplicitAny=false

import dataclasses
import inspect
import warnings
from enum import Enum
from typing import Any
from typing_extensions import (
    TypeIs,
    get_annotations,
    get_protocol_members,
    is_protocol,
    # Always use typing_extensions.is_typeddict because it recognizes TypedDicts
    # from both typing and typing_extensions, while typing.is_typeddict may not
    # recognize typing_extensions.TypedDict on some Python versions.
    is_typeddict as _is_typeddict,
)

from typing_inspection.typing_objects import is_namedtuple

from ._config import DEFAULT_CONFIG, InspectConfig
from ._context import (
    InspectContext,
    extract_field_metadata,
    get_source_location,
)
from ._inspect_function import (
    _inspect_signature,  # pyright: ignore[reportPrivateUsage]
)
from ._inspect_type import (
    _get_type_params,  # pyright: ignore[reportPrivateUsage]
    _inspect_type,  # pyright: ignore[reportPrivateUsage]
)
from ._node import (
    ClassNode,
    DataclassFieldDef,
    DataclassType,
    EnumType,
    FieldDef,
    MethodSig,
    NamedTupleType,
    ProtocolType,
    TypedDictType,
    TypeNode,
    TypeParamNode,
    UnionNode,
    is_type_param_node,
)

# Wrapper functions for type detection.
# These wrap stdlib/typing_extensions functions for consistent naming.
# is_enum_type uses TypeIs for type narrowing to type[Enum].


def is_dataclass_type(cls: type[Any]) -> bool:
    """Check if cls is a dataclass.

    Checks that cls is both a dataclass and a type (not an instance).
    """
    return dataclasses.is_dataclass(cls)


def is_typeddict_type(cls: type[Any]) -> bool:
    """Check if cls is a TypedDict."""
    return _is_typeddict(cls)


def is_namedtuple_type(cls: type[Any]) -> bool:
    """Check if cls is a NamedTuple."""
    return is_namedtuple(cls)


def is_protocol_type(cls: type[Any]) -> bool:
    """Check if cls is a Protocol."""
    return is_protocol(cls)


def is_enum_type(cls: type[Any]) -> TypeIs[type[Enum]]:
    """Check if cls is an Enum subclass with TypeIs narrowing.

    Uses TypeIs to narrow cls to type[Enum] for _inspect_enum.
    """
    try:
        return issubclass(cls, Enum)
    except TypeError:
        return False


ClassInspectResult = (
    ClassNode | DataclassType | TypedDictType | NamedTupleType | ProtocolType | EnumType
)
"""Type alias for possible class inspection results."""


def inspect_class(
    cls: type,
    *,
    config: InspectConfig | None = None,
) -> ClassInspectResult:
    """Inspect a class and return the appropriate TypeNode.

    Automatically detects and returns specialized nodes for:
    - dataclasses -> DataclassType
    - TypedDict -> TypedDictType
    - NamedTuple -> NamedTupleType
    - Protocol -> ProtocolType
    - Enum -> EnumType
    - Regular classes -> ClassNode

    Args:
        cls: The class to inspect.
        config: Introspection configuration. Uses defaults if None.

    Returns:
        A specialized TypeNode based on the class type.
    """
    config = config if config is not None else DEFAULT_CONFIG
    ctx = InspectContext(config=config)

    # Detect class type and dispatch using TypeIs wrappers for type narrowing
    if is_dataclass_type(cls):
        return _inspect_dataclass(cls, ctx)
    if is_typeddict_type(cls):
        return _inspect_typed_dict(cls, ctx)
    if is_namedtuple_type(cls):
        return _inspect_named_tuple(cls, ctx)
    if is_protocol_type(cls):
        return _inspect_protocol(cls, ctx)
    if is_enum_type(cls):
        return _inspect_enum(cls, ctx)

    # cls type is narrowed to Unknown after exhaustive TypeIs checks above;
    # it's still a valid type but pyright loses track of the original type
    return _inspect_class(cls, ctx)  # pyright: ignore[reportUnknownArgumentType]


def inspect_dataclass(
    cls: type,
    *,
    config: InspectConfig | None = None,
) -> DataclassType:
    """Inspect a dataclass specifically.

    Args:
        cls: The dataclass to inspect.
        config: Introspection configuration. Uses defaults if None.

    Returns:
        A DataclassType node representing the dataclass.

    Raises:
        TypeError: If cls is not a dataclass.
    """
    if not is_dataclass_type(cls):
        msg = f"{cls} is not a dataclass"
        raise TypeError(msg)

    config = config if config is not None else DEFAULT_CONFIG
    ctx = InspectContext(config=config)
    return _inspect_dataclass(cls, ctx)


def inspect_typed_dict(
    cls: type,
    *,
    config: InspectConfig | None = None,
) -> TypedDictType:
    """Inspect a TypedDict specifically.

    Args:
        cls: The TypedDict to inspect.
        config: Introspection configuration. Uses defaults if None.

    Returns:
        A TypedDictType node representing the TypedDict.

    Raises:
        TypeError: If cls is not a TypedDict.
    """
    if not is_typeddict_type(cls):
        msg = f"{cls} is not a TypedDict"
        raise TypeError(msg)

    config = config if config is not None else DEFAULT_CONFIG
    ctx = InspectContext(config=config)
    return _inspect_typed_dict(cls, ctx)


def inspect_named_tuple(
    cls: type,
    *,
    config: InspectConfig | None = None,
) -> NamedTupleType:
    """Inspect a NamedTuple specifically.

    Args:
        cls: The NamedTuple to inspect.
        config: Introspection configuration. Uses defaults if None.

    Returns:
        A NamedTupleType node representing the NamedTuple.

    Raises:
        TypeError: If cls is not a NamedTuple.
    """
    if not is_namedtuple_type(cls):
        msg = f"{cls} is not a NamedTuple"
        raise TypeError(msg)

    config = config if config is not None else DEFAULT_CONFIG
    ctx = InspectContext(config=config)
    return _inspect_named_tuple(cls, ctx)


def inspect_protocol(
    cls: type,
    *,
    config: InspectConfig | None = None,
) -> ProtocolType:
    """Inspect a Protocol specifically.

    Args:
        cls: The Protocol to inspect.
        config: Introspection configuration. Uses defaults if None.

    Returns:
        A ProtocolType node representing the Protocol.

    Raises:
        TypeError: If cls is not a Protocol.
    """
    if not is_protocol_type(cls):
        msg = f"{cls} is not a Protocol"
        raise TypeError(msg)

    config = config if config is not None else DEFAULT_CONFIG
    ctx = InspectContext(config=config)
    return _inspect_protocol(cls, ctx)


def inspect_enum(
    cls: type,
    *,
    config: InspectConfig | None = None,
) -> EnumType:
    """Inspect an Enum specifically.

    Args:
        cls: The Enum to inspect.
        config: Introspection configuration. Uses defaults if None.

    Returns:
        An EnumType node representing the Enum.

    Raises:
        TypeError: If cls is not an Enum.
    """
    if not is_enum_type(cls):
        msg = f"{cls} is not an Enum"
        raise TypeError(msg)

    config = config if config is not None else DEFAULT_CONFIG
    ctx = InspectContext(config=config)
    return _inspect_enum(cls, ctx)


def _inspect_dataclass(cls: type, ctx: InspectContext) -> DataclassType:
    """Inspect a dataclass using a pre-configured context.

    Called internally by `inspect_dataclass` and `inspect_class`.
    """
    format_val = ctx.config.get_format()

    annotations = get_annotations(
        cls,
        format=format_val,
        globals=ctx.config.globalns,
        locals=ctx.config.localns,
    )

    dc_fields = dataclasses.fields(cls)
    fields: list[DataclassFieldDef] = []

    for f in dc_fields:
        if not ctx.config.include_private and f.name.startswith("_"):
            continue

        ann = annotations.get(f.name, Any)
        type_node = _inspect_type(ann, ctx.child())
        field_metadata = extract_field_metadata(type_node)

        has_default = f.default is not dataclasses.MISSING
        has_factory = f.default_factory is not dataclasses.MISSING

        fields.append(
            DataclassFieldDef(
                name=f.name,
                type=type_node,
                required=not (has_default or has_factory),
                metadata=field_metadata,
                default=f.default if has_default else None,
                default_factory=has_factory,
                init=f.init,
                repr=f.repr,
                compare=f.compare,
                kw_only=f.kw_only if f.kw_only is not dataclasses.MISSING else False,
                hash=f.hash,
            )
        )

    # Get dataclass params - __dataclass_params__ is a dataclass instance, not a dict
    dc_params = getattr(cls, "__dataclass_params__", None)

    return DataclassType(
        cls=cls,
        fields=tuple(fields),
        frozen=getattr(dc_params, "frozen", False) if dc_params else False,
        slots="__slots__" in cls.__dict__,
        kw_only=getattr(dc_params, "kw_only", False) if dc_params else False,
        source=get_source_location(cls, ctx.config),
    )


def _inspect_typed_dict(cls: type, ctx: InspectContext) -> TypedDictType:
    """Inspect a TypedDict using a pre-configured context.

    Called internally by `inspect_class`.
    """
    format_val = ctx.config.get_format()

    annotations = get_annotations(
        cls,
        format=format_val,
        globals=ctx.config.globalns,
        locals=ctx.config.localns,
    )

    required_keys: frozenset[str] = getattr(cls, "__required_keys__", frozenset())
    total: bool = getattr(cls, "__total__", True)
    closed: bool = getattr(cls, "__closed__", False)

    fields: list[FieldDef] = []
    for name, ann in annotations.items():
        if not ctx.config.include_private and name.startswith("_"):
            continue

        type_node = _inspect_type(ann, ctx.child())

        # Filter out Required/NotRequired qualifiers from the type since
        # the requiredness is already captured in field.required via
        # __required_keys__/__optional_keys__. This avoids duplication.
        # Keep other qualifiers (e.g., read_only).
        remaining_qualifiers = frozenset(
            q for q in type_node.qualifiers if q not in ("required", "not_required")
        )
        if remaining_qualifiers != type_node.qualifiers:
            type_node = dataclasses.replace(type_node, qualifiers=remaining_qualifiers)

        field_metadata = extract_field_metadata(type_node)

        fields.append(
            FieldDef(
                name=name,
                type=type_node,
                required=name in required_keys,
                metadata=field_metadata,
            )
        )

    return TypedDictType(
        name=cls.__name__,
        fields=tuple(fields),
        total=total,
        closed=closed,
        source=get_source_location(cls, ctx.config),
    )


def _inspect_named_tuple(cls: type, ctx: InspectContext) -> NamedTupleType:
    """Inspect a NamedTuple using a pre-configured context.

    Called internally by `inspect_class`.
    """
    format_val = ctx.config.get_format()

    # NamedTuple stores types in __annotations__ (Python 3.10+)
    field_types = get_annotations(
        cls,
        format=format_val,
        globals=ctx.config.globalns,
        locals=ctx.config.localns,
    )

    field_names: tuple[str, ...] = getattr(cls, "_fields", ())
    field_defaults = getattr(cls, "_field_defaults", {})

    # Note: NamedTuple doesn't allow underscore-prefixed field names at
    # definition time, so there's no need for private field filtering here.
    fields: list[FieldDef] = []
    for name in field_names:
        ann = field_types.get(name, Any)
        type_node = _inspect_type(ann, ctx.child())
        field_metadata = extract_field_metadata(type_node)

        fields.append(
            FieldDef(
                name=name,
                type=type_node,
                required=name not in field_defaults,
                metadata=field_metadata,
            )
        )

    return NamedTupleType(
        name=cls.__name__,
        fields=tuple(fields),
        source=get_source_location(cls, ctx.config),
    )


def _inspect_protocol(cls: type, ctx: InspectContext) -> ProtocolType:
    """Inspect a Protocol using a pre-configured context.

    Called internally by `inspect_class`.
    """
    format_val = ctx.config.get_format()

    methods: list[MethodSig] = []
    attributes: list[FieldDef] = []

    # Get annotations for attributes
    annotations = get_annotations(
        cls,
        format=format_val,
        globals=ctx.config.globalns,
        locals=ctx.config.localns,
    )

    # Get protocol members using the official typing_extensions API
    # get_protocol_members returns a frozenset of member names
    protocol_attrs = get_protocol_members(cls)

    for name in protocol_attrs:
        if not ctx.config.include_private and name.startswith("_"):
            continue

        member = getattr(cls, name, None)

        if callable(member) and not isinstance(member, type):
            # It's a method
            sig = _inspect_signature(member, ctx)
            methods.append(
                MethodSig(
                    name=name,
                    signature=sig,
                    is_classmethod=isinstance(
                        inspect.getattr_static(cls, name, None),
                        classmethod,
                    ),
                    is_staticmethod=isinstance(
                        inspect.getattr_static(cls, name, None),
                        staticmethod,
                    ),
                    is_property=isinstance(
                        inspect.getattr_static(cls, name, None),
                        property,
                    ),
                )
            )
        elif name in annotations:
            # It's an attribute
            ann = annotations[name]
            type_node = _inspect_type(ann, ctx.child())
            field_metadata = extract_field_metadata(type_node)

            attributes.append(
                FieldDef(
                    name=name,
                    type=type_node,
                    metadata=field_metadata,
                )
            )

    return ProtocolType(
        name=cls.__name__,
        methods=tuple(methods),
        attributes=tuple(attributes),
        is_runtime_checkable=getattr(cls, "_is_runtime_protocol", False),
        source=get_source_location(cls, ctx.config),
    )


def _inspect_enum(cls: type[Enum], ctx: InspectContext) -> EnumType:
    """Inspect an Enum using a pre-configured context.

    Called internally by `inspect_enum` and `inspect_class`.
    """
    enum_members: list[Enum] = list(cls)
    value_types: set[type[Any]] = {type(m.value) for m in enum_members}
    if len(value_types) == 1:
        value_type: TypeNode = _inspect_type(value_types.pop(), ctx.child())
    else:
        # Mixed types - use Union
        value_type = UnionNode(
            members=tuple(_inspect_type(t, ctx.child()) for t in value_types)
        )

    members: tuple[tuple[str, Any], ...] = tuple(
        (m.name, m.value) for m in enum_members
    )

    return EnumType(
        cls=cls,
        value_type=value_type,
        members=members,
        source=get_source_location(cls, ctx.config),
    )


def _inspect_class(  # noqa: PLR0912 - Inherently complex class introspection
    cls: type, ctx: InspectContext
) -> ClassNode:
    """Inspect a regular class using a pre-configured context.

    Called internally by `inspect_class` for non-specialized class types.
    """
    format_val = ctx.config.get_format()

    # Get type parameters
    type_params: list[TypeParamNode] = []
    for tp in _get_type_params(cls):
        tp_node = _inspect_type(tp, ctx.child())
        # TypeVar/ParamSpec/TypeVarTuple always produce TypeParamNode
        if is_type_param_node(tp_node):
            type_params.append(tp_node)

    # Get base classes
    bases: list[TypeNode] = []
    for base in cls.__bases__:
        if base is object:
            continue
        bases.append(_inspect_type(base, ctx.child()))

    # Get annotations
    annotations = get_annotations(
        cls,
        format=format_val,
        globals=ctx.config.globalns,
        locals=ctx.config.localns,
    )

    # Separate class vars and instance vars
    class_vars: list[FieldDef] = []
    instance_vars: list[FieldDef] = []

    for name, ann in annotations.items():
        if not ctx.config.include_private and name.startswith("_"):
            continue

        type_node = _inspect_type(ann, ctx.child())
        field_metadata = extract_field_metadata(type_node)

        field_def = FieldDef(
            name=name,
            type=type_node,
            metadata=field_metadata,
        )

        # Check if it's a ClassVar (qualifier is 'class_var' in the qualifiers set)
        if "class_var" in type_node.qualifiers:
            if ctx.config.include_class_vars:
                class_vars.append(field_def)
            continue

        if ctx.config.include_instance_vars:
            instance_vars.append(field_def)

    # Get methods
    methods: list[MethodSig] = []
    if ctx.config.include_methods:
        for name in dir(cls):
            is_private = not ctx.config.include_private and name.startswith("_")
            is_special = name in ("__init__", "__new__", "__call__")
            if is_private and not is_special:
                continue

            if not ctx.config.include_inherited and name not in cls.__dict__:
                continue

            try:
                # Suppress deprecation warnings that may be triggered when accessing
                # certain attributes (e.g., typing.io in Python 3.11)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", DeprecationWarning)
                    member = getattr(cls, name)
            except AttributeError:
                continue

            if not callable(member) or isinstance(member, type):
                continue

            sig = _inspect_signature(member, ctx)
            static_member = inspect.getattr_static(cls, name, None)
            methods.append(
                MethodSig(
                    name=name,
                    signature=sig,
                    is_classmethod=isinstance(static_member, classmethod),
                    is_staticmethod=isinstance(static_member, staticmethod),
                    is_property=isinstance(static_member, property),
                )
            )

    return ClassNode(
        cls=cls,
        name=cls.__name__,
        type_params=tuple(type_params),
        bases=tuple(bases),
        methods=tuple(methods),
        class_vars=tuple(class_vars),
        instance_vars=tuple(instance_vars),
        is_abstract=inspect.isabstract(cls),
        is_final=False,  # Can't easily detect @final
        source=get_source_location(cls, ctx.config),
    )
