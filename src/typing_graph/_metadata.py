"""Metadata collection for type annotations."""

import builtins
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import (
    TYPE_CHECKING,
    Annotated,
    ClassVar,
    Protocol,
    TypeVar,
    final,
    get_args,
    get_origin,
    overload,
)
from typing_extensions import Self, override

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Mapping

# Type variables for generic query operations
T = TypeVar("T")
D = TypeVar("D")

# Annotated[T, ...] requires at least the base type T plus one metadata item
_MIN_ANNOTATED_ARGS = 2


def _is_grouped_metadata(item: object) -> bool:
    """Check if item is GroupedMetadata without importing annotated-types.

    Uses duck typing to avoid runtime dependency on annotated-types.
    Checks if the item's type or any of its base classes is named
    'GroupedMetadata', which handles both the protocol itself and
    concrete implementations like Interval.

    Args:
        item: Any object to check.

    Returns:
        True if item appears to be a GroupedMetadata instance.
    """
    if not hasattr(item, "__iter__"):
        return False
    # Check if 'GroupedMetadata' is anywhere in the MRO
    return any(cls.__name__ == "GroupedMetadata" for cls in type(item).__mro__)


def _flatten_items(items: "Iterable[object]") -> tuple[object, ...]:
    """Flatten GroupedMetadata items (single level).

    Args:
        items: Iterable of metadata objects, possibly containing GroupedMetadata.

    Returns:
        Tuple with GroupedMetadata items expanded one level.
    """
    result: list[object] = []
    for item in items:
        if _is_grouped_metadata(item):
            # Duck-typed GroupedMetadata is iterable but pyright can't track this
            result.extend(item)  # pyright: ignore[reportArgumentType]
        else:
            result.append(item)
    return tuple(result)


def _default_sort_key(item: object) -> tuple[str, str]:
    """Default sort key: (type_name, repr) for stable heterogeneous sorting."""
    return (type(item).__name__, repr(item))


def _ensure_runtime_checkable(protocol: type) -> None:
    """Validate that a type is a @runtime_checkable Protocol.

    Args:
        protocol: The type to validate.

    Raises:
        TypeError: If the type is not a Protocol.
        ProtocolNotRuntimeCheckableError: If the protocol lacks @runtime_checkable.
    """
    if not getattr(protocol, "_is_protocol", False):
        msg = f"{protocol.__name__} is not a Protocol"
        raise TypeError(msg)
    if not getattr(protocol, "_is_runtime_protocol", False):
        raise ProtocolNotRuntimeCheckableError(protocol)


class SupportsLessThan(Protocol):
    """Protocol for types supporting the < operator.

    This protocol is used to type the `key` parameter in sorting operations,
    ensuring type safety while allowing any comparable type.
    """

    def __lt__(self, other: object, /) -> bool:
        """Compare this object to another for less-than ordering."""
        ...


@final
class MetadataNotFoundError(LookupError):
    """Raised when requested metadata type is not found in a collection.

    This exception provides context about what type was requested and the
    collection that was searched, enabling better error messages and debugging.

    Attributes:
        requested_type: The type that was searched for but not found.
        collection: The MetadataCollection that was searched.

    Examples:
        >>> coll = MetadataCollection()
        >>> try:
        ...     raise MetadataNotFoundError(int, coll)
        ... except MetadataNotFoundError as e:
        ...     print(e.requested_type)
        <class 'int'>
    """

    requested_type: type
    collection: "MetadataCollection"

    def __init__(self, requested_type: type, collection: "MetadataCollection") -> None:
        """Initialize the exception with the requested type and collection.

        Args:
            requested_type: The type that was not found.
            collection: The collection that was searched.
        """
        self.requested_type = requested_type
        self.collection = collection
        msg = (
            f"No metadata of type {requested_type.__name__!r} found. "
            f"Use find() instead of get_required() if the type may not exist."
        )
        super().__init__(msg)


@final
class ProtocolNotRuntimeCheckableError(TypeError):
    """Raised when a protocol without @runtime_checkable is used for matching.

    Protocol-based methods like find_protocol() and has_protocol() require
    the protocol to be decorated with @runtime_checkable. This exception
    provides clear guidance on how to fix the error.

    Attributes:
        protocol: The protocol type that is not runtime checkable.

    Examples:
        >>> from typing import Protocol
        >>> class NotRuntime(Protocol):
        ...     value: int
        >>> try:
        ...     raise ProtocolNotRuntimeCheckableError(NotRuntime)
        ... except ProtocolNotRuntimeCheckableError as e:
        ...     print(e.protocol.__name__)
        NotRuntime
    """

    protocol: type

    def __init__(self, protocol: type) -> None:
        """Initialize the exception with the non-runtime-checkable protocol.

        Args:
            protocol: The protocol that is not runtime checkable.
        """
        self.protocol = protocol
        msg = (
            f"{protocol.__name__} is not @runtime_checkable. "
            "Add @runtime_checkable decorator to use with "
            "find_protocol() or has_protocol()."
        )
        super().__init__(msg)


@dataclass(slots=True, frozen=True)
class MetadataCollection:
    """Immutable collection of metadata from Annotated types.

    MetadataCollection provides a type-safe, immutable container for metadata
    extracted from Annotated type annotations. It implements the sequence
    protocol for familiar Python iteration patterns.

    The collection is frozen (immutable) and uses slots for memory efficiency.
    All transformation methods return new collections rather than modifying
    the existing one.

    Attributes:
        _items: The internal tuple storing metadata items.

    Examples:
        >>> # Create an empty collection
        >>> empty = MetadataCollection()
        >>> len(empty)
        0

        >>> # Use the EMPTY singleton for empty collections
        >>> MetadataCollection.EMPTY is MetadataCollection.EMPTY
        True

        >>> # Create a collection with items (factory method in later stage)
        >>> coll = MetadataCollection(_items=("doc", 42, True))
        >>> len(coll)
        3
        >>> list(coll)
        ['doc', 42, True]

        >>> # Membership testing
        >>> "doc" in coll
        True
        >>> "missing" in coll
        False

        >>> # Indexing and slicing
        >>> coll[0]
        'doc'
        >>> coll[-1]
        True
    """

    _items: tuple[object, ...] = field(default=())

    EMPTY: ClassVar[Self]
    """Singleton empty collection.

    Use this instead of creating new empty collections to avoid
    repeated allocations.
    """

    def __len__(self) -> int:
        """Return the number of items in the collection.

        Returns:
            The count of metadata items.

        Examples:
            >>> coll = MetadataCollection(_items=(1, 2, 3))
            >>> len(coll)
            3
        """
        return len(self._items)

    def __iter__(self) -> "Iterator[object]":
        """Yield items in insertion order.

        Yields:
            Each metadata item in the order it was added.

        Examples:
            >>> coll = MetadataCollection(_items=("a", "b", "c"))
            >>> list(coll)
            ['a', 'b', 'c']
        """
        return iter(self._items)

    def __contains__(self, item: object) -> bool:
        """Check if an item is in the collection using equality comparison.

        Args:
            item: The item to check for membership.

        Returns:
            True if the item is in the collection, False otherwise.

        Examples:
            >>> coll = MetadataCollection(_items=("doc", 42))
            >>> "doc" in coll
            True
            >>> "missing" in coll
            False
        """
        return item in self._items

    @overload
    def __getitem__(self, index: int) -> object: ...

    @overload
    def __getitem__(self, index: slice) -> "MetadataCollection": ...

    def __getitem__(self, index: int | slice) -> "object | MetadataCollection":
        """Access items by index or slice.

        Integer indexing returns the item at that position. Slice indexing
        returns a new MetadataCollection containing the sliced items.

        Args:
            index: An integer index or slice object.

        Returns:
            The item at the index (for int) or a new MetadataCollection
            containing the sliced items (for slice).

        Raises:
            IndexError: If the integer index is out of range.

        Examples:
            >>> coll = MetadataCollection(_items=("a", "b", "c", "d"))
            >>> coll[0]
            'a'
            >>> coll[-1]
            'd'
            >>> list(coll[1:3])
            ['b', 'c']
            >>> coll[::2]  # Returns MetadataCollection
            MetadataCollection(['a', 'c'])
        """
        if isinstance(index, int):
            return self._items[index]
        sliced = self._items[index]
        if not sliced:
            return MetadataCollection.EMPTY
        return MetadataCollection(_items=sliced)

    def __bool__(self) -> bool:
        """Return True if the collection is non-empty.

        Returns:
            True if the collection contains items, False if empty.

        Examples:
            >>> bool(MetadataCollection.EMPTY)
            False
            >>> bool(MetadataCollection(_items=(1,)))
            True
        """
        return bool(self._items)

    @override
    def __eq__(self, other: object) -> bool:
        """Compare collections for equality.

        Two MetadataCollections are equal if they contain the same items
        in the same order.

        Args:
            other: The object to compare with.

        Returns:
            True if other is a MetadataCollection with equal items,
            NotImplemented if other is not a MetadataCollection.

        Examples:
            >>> a = MetadataCollection(_items=(1, 2, 3))
            >>> b = MetadataCollection(_items=(1, 2, 3))
            >>> a == b
            True
            >>> c = MetadataCollection(_items=(3, 2, 1))
            >>> a == c
            False
        """
        if not isinstance(other, MetadataCollection):
            return NotImplemented
        # O(1) early-exit for different lengths
        if len(self._items) != len(other._items):
            return False
        return self._items == other._items

    @override
    def __hash__(self) -> int:
        """Return hash value if all items are hashable.

        The hash is computed from the tuple of items, enabling use of
        MetadataCollection as dict keys or set members when all items
        are hashable.

        Returns:
            Hash value based on the items tuple.

        Raises:
            TypeError: If any item in the collection is unhashable.
                The error message indicates which items caused the issue.

        Examples:
            >>> coll = MetadataCollection(_items=(1, "doc", (2, 3)))
            >>> hash(coll)  # Works for hashable items
            >>> coll_unhashable = MetadataCollection(_items=([1, 2],))
            >>> hash(coll_unhashable)  # doctest: +IGNORE_EXCEPTION_DETAIL
            Traceback (most recent call last):
                ...
            TypeError: MetadataCollection contains unhashable items...
        """
        try:
            return hash(self._items)
        except TypeError as e:
            msg = f"MetadataCollection contains unhashable items: {e}"
            raise TypeError(msg) from e

    @override
    def __repr__(self) -> str:
        """Return a debug representation of the collection.

        For collections with more than 5 items, the representation is
        truncated to show the first 5 items plus a count of remaining items.

        Returns:
            A string in the format MetadataCollection([item1, item2, ...]).

        Examples:
            >>> MetadataCollection(_items=())
            MetadataCollection([])
            >>> MetadataCollection(_items=(1, 2))
            MetadataCollection([1, 2])
            >>> MetadataCollection(_items=(1, 2, 3, 4, 5, 6, 7))
            MetadataCollection([1, 2, 3, 4, 5, ...<2 more>])
        """
        max_display = 5
        if len(self._items) <= max_display:
            items_repr = ", ".join(repr(item) for item in self._items)
            return f"MetadataCollection([{items_repr}])"
        displayed = ", ".join(repr(item) for item in self._items[:max_display])
        remaining = len(self._items) - max_display
        return f"MetadataCollection([{displayed}, ...<{remaining} more>])"

    def __add__(self, other: object) -> "MetadataCollection":
        """Concatenate two collections.

        Returns a new collection containing items from both collections,
        with self's items first followed by other's items.

        Args:
            other: Another MetadataCollection to concatenate.

        Returns:
            New MetadataCollection with concatenated items, or EMPTY if
            both collections are empty. Returns NotImplemented if other
            is not a MetadataCollection.

        Examples:
            >>> a = MetadataCollection(_items=(1, 2))
            >>> b = MetadataCollection(_items=(3, 4))
            >>> list(a + b)
            [1, 2, 3, 4]
            >>> empty = MetadataCollection.EMPTY
            >>> (empty + empty) is MetadataCollection.EMPTY
            True
        """
        if not isinstance(other, MetadataCollection):
            return NotImplemented
        combined = self._items + other._items
        if not combined:
            return MetadataCollection.EMPTY
        return MetadataCollection(_items=combined)

    def __or__(self, other: object) -> "MetadataCollection":
        """Concatenate two collections using the | operator.

        This is an alias for __add__, providing an alternative syntax
        for collection concatenation.

        Args:
            other: Another MetadataCollection to concatenate.

        Returns:
            New MetadataCollection with concatenated items.

        Examples:
            >>> a = MetadataCollection(_items=(1, 2))
            >>> b = MetadataCollection(_items=(3, 4))
            >>> list(a | b)
            [1, 2, 3, 4]
        """
        return self.__add__(other)

    @property
    def is_hashable(self) -> bool:
        """Check if all items are hashable without raising an exception.

        This property allows checking hashability before attempting
        operations that require it (like using the collection as a
        dict key or set member).

        Returns:
            True if all items are hashable, False otherwise.

        Examples:
            >>> coll = MetadataCollection(_items=(1, "doc"))
            >>> coll.is_hashable
            True
            >>> coll_unhashable = MetadataCollection(_items=([1, 2],))
            >>> coll_unhashable.is_hashable
            False
        """
        try:
            _ = hash(self._items)
        except TypeError:
            return False
        else:
            return True

    @property
    def is_empty(self) -> bool:
        """Check if the collection has no items.

        Returns:
            True if the collection contains no items, False otherwise.

        Examples:
            >>> MetadataCollection.EMPTY.is_empty
            True
            >>> MetadataCollection(_items=(1, 2)).is_empty
            False
        """
        return not self._items

    def find(self, type_: type[T]) -> T | None:
        """Return the first item that is an instance of the given type.

        Uses ``isinstance`` semantics, so subclasses match. For example,
        ``find(int)`` will match ``bool`` values since ``bool`` is a
        subclass of ``int``.

        Args:
            type_: The type to search for (including subclasses).

        Returns:
            The first matching item, or None if no match is found.

        Examples:
            >>> coll = MetadataCollection(_items=("doc", 42, True))
            >>> coll.find(int)  # Returns 42, not True (first match)
            42
            >>> coll.find(str)
            'doc'
            >>> coll.find(float) is None
            True
        """
        for item in self._items:
            if isinstance(item, type_):
                return item
        return None

    def find_first(self, *types: type) -> object | None:
        """Return the first item matching any of the given types.

        Args:
            *types: One or more types to search for.

        Returns:
            The first item that is an instance of any of the given types,
            or None if no match is found or no types are provided.

        Examples:
            >>> coll = MetadataCollection(_items=("doc", 42, True))
            >>> coll.find_first(int, bool)
            42
            >>> coll.find_first(float, complex) is None
            True
            >>> coll.find_first() is None
            True
        """
        if not types:
            return None
        for item in self._items:
            if isinstance(item, types):
                return item
        return None

    def has(self, *types: type) -> bool:
        """Check if any item is an instance of any of the given types.

        Args:
            *types: One or more types to check for.

        Returns:
            True if any item matches any of the given types,
            False otherwise or if no types are provided.

        Examples:
            >>> coll = MetadataCollection(_items=("doc", 42))
            >>> coll.has(int)
            True
            >>> coll.has(float)
            False
            >>> coll.has(str, int)
            True
            >>> coll.has()
            False
        """
        if not types:
            return False
        return any(isinstance(item, types) for item in self._items)

    def count(self, *types: type) -> int:
        """Count items that are instances of any of the given types.

        Args:
            *types: One or more types to count.

        Returns:
            The number of items matching any of the given types,
            or 0 if no types are provided.

        Examples:
            >>> coll = MetadataCollection(_items=("a", "b", 1, 2, 3))
            >>> coll.count(str)
            2
            >>> coll.count(int)
            3
            >>> coll.count(str, int)
            5
            >>> coll.count()
            0
        """
        if not types:
            return 0
        return sum(1 for item in self._items if isinstance(item, types))

    @overload
    def find_all(self) -> "MetadataCollection": ...

    @overload
    def find_all(self, type_: type[T], /) -> "MetadataCollection": ...

    @overload
    def find_all(
        self, type_: type[T], type2_: type, /, *types: type
    ) -> "MetadataCollection": ...

    def find_all(self, *types: type) -> "MetadataCollection":
        """Return all items that are instances of any of the given types.

        Uses ``isinstance`` semantics, so subclasses match. For example,
        ``find_all(int)`` will match both ``int`` and ``bool`` values.

        If called with no arguments, returns a copy of the entire collection.

        Args:
            *types: Zero or more types to filter by (including subclasses).

        Returns:
            A new MetadataCollection containing matching items,
            or all items if no types are specified.

        Examples:
            >>> coll = MetadataCollection(_items=("a", 1, "b", 2))
            >>> list(coll.find_all())
            ['a', 1, 'b', 2]
            >>> list(coll.find_all(str))
            ['a', 'b']
            >>> list(coll.find_all(int, str))
            ['a', 1, 'b', 2]
            >>> coll.find_all(float) is MetadataCollection.EMPTY
            True
        """
        if not types:
            # Return copy of all items
            if not self._items:
                return MetadataCollection.EMPTY
            return MetadataCollection(_items=self._items)
        matches = tuple(item for item in self._items if isinstance(item, types))
        if not matches:
            return MetadataCollection.EMPTY
        return MetadataCollection(_items=matches)

    @overload
    def get(self, type_: type[T]) -> T | None: ...

    @overload
    def get(self, type_: type[T], default: D) -> T | D: ...

    def get(self, type_: type[T], default: D | None = None) -> T | D | None:
        """Return the first matching item or a default value.

        Follows the ``dict.get()`` pattern for familiarity. Unlike ``find()``,
        this method correctly handles falsy values like ``0``, ``False``, or
        empty strings.

        Args:
            type_: The type to search for.
            default: Value to return if no match is found. Defaults to None.

        Returns:
            The first matching item, or the default value if not found.

        Examples:
            >>> coll = MetadataCollection(_items=("doc", 42))
            >>> coll.get(int)
            42
            >>> coll.get(float) is None
            True
            >>> coll.get(float, -1)
            -1
            >>> coll.get(float, "missing")
            'missing'
            >>> # Falsy values are returned correctly
            >>> coll = MetadataCollection(_items=(0, False, ""))
            >>> coll.get(int, -1)
            0
            >>> coll.get(bool, True)
            False
        """
        # Iterate directly instead of using find() to handle falsy values
        for item in self._items:
            if isinstance(item, type_):
                return item  # pyright narrows type after isinstance check
        return default

    def get_required(self, type_: type[T]) -> T:
        """Return the first matching item or raise MetadataNotFoundError.

        Use this method when the metadata is expected to exist. For optional
        metadata, use ``find()`` or ``get()`` instead.

        Args:
            type_: The type to search for.

        Returns:
            The first matching item.

        Raises:
            MetadataNotFoundError: If no item of the given type is found.

        Examples:
            >>> coll = MetadataCollection(_items=("doc", 42))
            >>> coll.get_required(int)
            42
            >>> coll.get_required(float)  # doctest: +IGNORE_EXCEPTION_DETAIL
            Traceback (most recent call last):
                ...
            MetadataNotFoundError: No metadata of type 'float' found...
        """
        # Iterate directly to correctly handle falsy values like 0, False, ""
        for item in self._items:
            if isinstance(item, type_):
                return item
        raise MetadataNotFoundError(type_, self)

    def filter(self, predicate: "Callable[[object], bool]") -> "MetadataCollection":
        """Return items for which predicate returns True.

        Args:
            predicate: Callable taking an item, returning True if it should be included.

        Returns:
            New MetadataCollection with matching items, or EMPTY if none match.

        Security:
            Predicates execute arbitrary code. Use only trusted sources.
        """
        matches = tuple(item for item in self._items if predicate(item))
        if not matches:
            return MetadataCollection.EMPTY
        return MetadataCollection(_items=matches)

    def filter_by_type(
        self, type_: type[T], predicate: "Callable[[T], bool]"
    ) -> "MetadataCollection":
        """Return items of given type for which predicate returns True.

        Provides type-safe filtering - predicate receives typed items.

        Args:
            type_: Type to filter by.
            predicate: Callable taking typed item, returning True to include.

        Returns:
            New MetadataCollection with matching items, or EMPTY if none match.

        Security:
            Predicates execute arbitrary code. Use only trusted sources.
        """
        matches = tuple(
            item for item in self._items if isinstance(item, type_) and predicate(item)
        )
        if not matches:
            return MetadataCollection.EMPTY
        return MetadataCollection(_items=matches)

    def first(self, predicate: "Callable[[object], bool]") -> object | None:
        """Return first item for which predicate returns True.

        Args:
            predicate: Callable taking an item, returning True if it matches.

        Returns:
            First matching item, or None if no match.

        Security:
            Predicates execute arbitrary code. Use only trusted sources.
        """
        for item in self._items:
            if predicate(item):
                return item
        return None

    def first_of_type(
        self, type_: type[T], predicate: "Callable[[T], bool] | None" = None
    ) -> T | None:
        """Return first item of type matching optional predicate.

        Args:
            type_: Type to search for.
            predicate: Optional callable to filter typed items.

        Returns:
            First matching item, or None if no match.

        Security:
            Predicates execute arbitrary code. Use only trusted sources.
        """
        for item in self._items:
            if isinstance(item, type_) and (predicate is None or predicate(item)):
                return item
        return None

    def any(self, predicate: "Callable[[object], bool]") -> bool:
        """Return True if predicate returns True for any item.

        Args:
            predicate: Callable taking an item, returning bool.

        Returns:
            True if any item satisfies predicate, False otherwise.

        Security:
            Predicates execute arbitrary code. Use only trusted sources.
        """
        return builtins.any(predicate(item) for item in self._items)

    def find_protocol(self, protocol: type) -> "MetadataCollection":
        """Return items that satisfy the given protocol.

        Args:
            protocol: A @runtime_checkable Protocol type.

        Returns:
            New MetadataCollection with matching items, or EMPTY if none match.

        Raises:
            TypeError: If protocol is not a Protocol.
            ProtocolNotRuntimeCheckableError: If protocol lacks @runtime_checkable.

        Security:
            Protocol types may have custom __subclasshook__. Use trusted sources.
        """
        _ensure_runtime_checkable(protocol)
        matches = tuple(item for item in self._items if isinstance(item, protocol))
        if not matches:
            return MetadataCollection.EMPTY
        return MetadataCollection(_items=matches)

    def has_protocol(self, protocol: type) -> bool:
        """Return True if any item satisfies the given protocol.

        Args:
            protocol: A @runtime_checkable Protocol type.

        Returns:
            True if any item satisfies the protocol.

        Raises:
            TypeError: If protocol is not a Protocol.
            ProtocolNotRuntimeCheckableError: If protocol lacks @runtime_checkable.

        Security:
            See find_protocol() for security considerations.
        """
        _ensure_runtime_checkable(protocol)
        return builtins.any(isinstance(item, protocol) for item in self._items)

    def count_protocol(self, protocol: type) -> int:
        """Return count of items satisfying the given protocol.

        Args:
            protocol: A @runtime_checkable Protocol type.

        Returns:
            Number of items satisfying the protocol.

        Raises:
            TypeError: If protocol is not a Protocol.
            ProtocolNotRuntimeCheckableError: If protocol lacks @runtime_checkable.

        Security:
            See find_protocol() for security considerations.
        """
        _ensure_runtime_checkable(protocol)
        return sum(1 for item in self._items if isinstance(item, protocol))

    @classmethod
    def of(
        cls,
        items: "Iterable[object]" = (),
        *,
        auto_flatten: bool = True,
    ) -> "MetadataCollection":
        """Create a collection from an iterable.

        This is the primary factory method for creating MetadataCollection
        instances. It handles GroupedMetadata flattening automatically unless
        disabled.

        Args:
            items: Iterable of metadata objects.
            auto_flatten: If True (default), expand GroupedMetadata items
                one level. Set to False to preserve GroupedMetadata as-is.

        Returns:
            New MetadataCollection containing the items, or EMPTY if no items.

        Examples:
            >>> MetadataCollection.of([1, 2, 3])
            MetadataCollection([1, 2, 3])
            >>> MetadataCollection.of([])
            MetadataCollection([])
            >>> MetadataCollection.of([]) is MetadataCollection.EMPTY
            True
        """
        if auto_flatten:
            flattened = _flatten_items(items)
            if not flattened:
                return cls.EMPTY
            return cls(_items=flattened)
        items_tuple = tuple(items)
        if not items_tuple:
            return cls.EMPTY
        return cls(_items=items_tuple)

    @classmethod
    def from_annotated(
        cls,
        annotated_type: object,
        *,
        unwrap_nested: bool = True,
    ) -> "MetadataCollection":
        """Extract metadata from an Annotated type.

        This method inspects a type and extracts any metadata from Annotated
        type hints. Non-Annotated types return an empty collection.

        Args:
            annotated_type: A type, potentially ``Annotated[T, ...]``.
            unwrap_nested: If True (default), recursively unwrap nested
                Annotated types, collecting all metadata. Outer metadata
                comes first, then inner metadata.

        Returns:
            MetadataCollection with extracted metadata, or EMPTY if the type
            is not Annotated or has no metadata.

        Examples:
            >>> from typing import Annotated
            >>> MetadataCollection.from_annotated(Annotated[int, "doc", 42])
            MetadataCollection(['doc', 42])
            >>> MetadataCollection.from_annotated(int)
            MetadataCollection([])
            >>> # Nested Annotated types are unwrapped by default
            >>> Inner = Annotated[int, "inner"]
            >>> Outer = Annotated[Inner, "outer"]
            >>> MetadataCollection.from_annotated(Outer)
            MetadataCollection(['outer', 'inner'])
        """
        # Check if it's an Annotated type
        origin = get_origin(annotated_type)
        if origin is not Annotated:
            return cls.EMPTY

        # Get the base type and metadata
        # get_args returns tuple[Any, ...] but we know it's safe for Annotated
        args: tuple[object, ...] = get_args(annotated_type)
        if len(args) < _MIN_ANNOTATED_ARGS:  # pragma: no cover
            # Defensive: valid Annotated always has >= 2 args
            return cls.EMPTY

        base_type: object = args[0]
        metadata: tuple[object, ...] = args[1:]

        # Collect all metadata items
        all_metadata: list[object] = list(metadata)

        # Recursively unwrap nested Annotated if requested
        # Note: Python auto-flattens nested Annotated at definition time,
        # so this branch handles edge cases from dynamic type construction
        if unwrap_nested:
            nested_origin: object = get_origin(base_type)
            if nested_origin is Annotated:  # pragma: no cover
                nested_collection = cls.from_annotated(base_type, unwrap_nested=True)
                all_metadata.extend(nested_collection)

        # Always flatten GroupedMetadata
        return cls.of(all_metadata, auto_flatten=True)

    def flatten(self) -> "MetadataCollection":
        """Return new collection with GroupedMetadata expanded (single level).

        This method expands any GroupedMetadata items one level, leaving
        nested GroupedMetadata intact. Use flatten_deep() for recursive
        expansion.

        Returns:
            New MetadataCollection with GroupedMetadata expanded one level,
            or self if no GroupedMetadata items exist.

        Examples:
            >>> coll = MetadataCollection(_items=(1, 2, 3))
            >>> coll.flatten()
            MetadataCollection([1, 2, 3])
        """
        flattened = _flatten_items(self._items)
        if flattened == self._items:
            return self
        if not flattened:
            return MetadataCollection.EMPTY
        return MetadataCollection(_items=flattened)

    def flatten_deep(self) -> "MetadataCollection":
        """Return new collection with GroupedMetadata recursively expanded.

        This method repeatedly expands GroupedMetadata items until no more
        GroupedMetadata remains. Use flatten() for single-level expansion.

        Returns:
            New MetadataCollection with all GroupedMetadata fully expanded,
            or self if no GroupedMetadata items exist.

        Examples:
            >>> coll = MetadataCollection(_items=(1, 2, 3))
            >>> coll.flatten_deep()
            MetadataCollection([1, 2, 3])
        """
        current = self._items
        while True:
            # Check if any GroupedMetadata remains
            has_grouped = any(_is_grouped_metadata(item) for item in current)
            if not has_grouped:
                break
            current = _flatten_items(current)

        if current == self._items:
            return self
        if not current:
            return MetadataCollection.EMPTY
        return MetadataCollection(_items=current)

    def exclude(self, *types: type) -> "MetadataCollection":
        """Return items that are NOT instances of any of the given types.

        This is the inverse of find_all() - it excludes rather than includes
        items matching the specified types.

        Args:
            *types: One or more types to exclude.

        Returns:
            New MetadataCollection with non-matching items, or EMPTY if
            all items match. Returns self if no types are provided.

        Examples:
            >>> coll = MetadataCollection(_items=("a", 1, "b", 2))
            >>> list(coll.exclude(int))
            ['a', 'b']
            >>> list(coll.exclude(str, int))
            []
            >>> coll.exclude() is coll
            True
        """
        if not types:
            return self
        matches = tuple(item for item in self._items if not isinstance(item, types))
        if not matches:
            return MetadataCollection.EMPTY
        return MetadataCollection(_items=matches)

    def unique(self) -> "MetadataCollection":
        """Return collection with duplicate items removed.

        Preserves first occurrence order. Uses set-based deduplication
        for hashable items (O(n)), falling back to list-based comparison
        for unhashable items (O(n^2)).

        Returns:
            New MetadataCollection with unique items, or self if already unique.

        Examples:
            >>> coll = MetadataCollection(_items=(1, 2, 1, 3, 2))
            >>> list(coll.unique())
            [1, 2, 3]
            >>> # Unhashable items are handled
            >>> coll = MetadataCollection(_items=([1], [2], [1]))
            >>> list(coll.unique())
            [[1], [2]]
        """
        if not self._items:
            return MetadataCollection.EMPTY

        # Try set-based deduplication (O(n))
        try:
            seen: set[object] = set()
            result: list[object] = []
            for item in self._items:
                if item not in seen:
                    seen.add(item)
                    result.append(item)
        except TypeError:
            # Fall back to list-based comparison for unhashable items (O(n^2))
            result = []
            for item in self._items:
                if item not in result:
                    result.append(item)

        result_tuple = tuple(result)
        if result_tuple == self._items:
            return self
        if not result_tuple:
            return MetadataCollection.EMPTY
        return MetadataCollection(_items=result_tuple)

    def sorted(
        self, *, key: "Callable[[object], SupportsLessThan] | None" = None
    ) -> "MetadataCollection":
        """Return collection with items sorted.

        Uses the provided key function for comparison. If no key is provided,
        uses a default key of (type_name, repr) for stable heterogeneous sorting.

        Args:
            key: Optional callable that extracts a comparison key from each item.
                The key must return a value supporting the < operator.

        Returns:
            New MetadataCollection with sorted items, or EMPTY if empty.

        Security:
            Key functions execute arbitrary code. Use only trusted sources.

        Examples:
            >>> coll = MetadataCollection(_items=(3, 1, 2))
            >>> list(coll.sorted())
            [1, 2, 3]
            >>> coll = MetadataCollection(_items=("b", "a", "c"))
            >>> list(coll.sorted())
            ['a', 'b', 'c']
            >>> # Custom key function
            >>> coll = MetadataCollection(_items=("bb", "a", "ccc"))
            >>> list(coll.sorted(key=len))
            ['a', 'bb', 'ccc']
        """
        if not self._items:
            return MetadataCollection.EMPTY
        sort_key = key if key is not None else _default_sort_key
        sorted_items = tuple(builtins.sorted(self._items, key=sort_key))
        return MetadataCollection(_items=sorted_items)

    def reversed(self) -> "MetadataCollection":
        """Return collection with items in reverse order.

        Returns:
            New MetadataCollection with reversed items, or EMPTY if empty.

        Examples:
            >>> coll = MetadataCollection(_items=(1, 2, 3))
            >>> list(coll.reversed())
            [3, 2, 1]
            >>> MetadataCollection.EMPTY.reversed() is MetadataCollection.EMPTY
            True
        """
        if not self._items:
            return MetadataCollection.EMPTY
        return MetadataCollection(_items=self._items[::-1])

    def map(self, func: "Callable[[object], T]") -> tuple[T, ...]:
        """Apply a function to each item and return results as a tuple.

        This is a terminal operation - it returns a tuple, not a
        MetadataCollection, because the transformed values may not be
        valid metadata items.

        Args:
            func: Callable to apply to each item.

        Returns:
            Tuple containing the results of applying func to each item.

        Security:
            Functions execute arbitrary code. Use only trusted sources.

        Examples:
            >>> coll = MetadataCollection(_items=(1, 2, 3))
            >>> coll.map(lambda x: x * 2)
            (2, 4, 6)
            >>> coll = MetadataCollection(_items=("a", "bb", "ccc"))
            >>> coll.map(len)
            (1, 2, 3)
        """
        # List comprehension is faster than generator expression inside tuple()
        return tuple([func(item) for item in self._items])

    def partition(
        self, predicate: "Callable[[object], bool]"
    ) -> tuple["MetadataCollection", "MetadataCollection"]:
        """Split collection into matching and non-matching items.

        Args:
            predicate: Callable taking an item, returning True if it should
                be in the first partition.

        Returns:
            Tuple of (matching, non_matching) MetadataCollections.

        Security:
            Predicates execute arbitrary code. Use only trusted sources.

        Examples:
            >>> coll = MetadataCollection(_items=(1, 2, 3, 4, 5))
            >>> matching, non_matching = coll.partition(lambda x: x % 2 == 0)
            >>> list(matching)
            [2, 4]
            >>> list(non_matching)
            [1, 3, 5]
        """
        matching: list[object] = []
        non_matching: list[object] = []
        for item in self._items:
            if predicate(item):
                matching.append(item)
            else:
                non_matching.append(item)

        matching_coll = (
            MetadataCollection(_items=tuple(matching))
            if matching
            else MetadataCollection.EMPTY
        )
        non_matching_coll = (
            MetadataCollection(_items=tuple(non_matching))
            if non_matching
            else MetadataCollection.EMPTY
        )
        return (matching_coll, non_matching_coll)

    def types(self) -> frozenset[type]:
        """Return the set of unique types in the collection.

        Returns:
            Frozenset containing the type of each unique item type.

        Examples:
            >>> coll = MetadataCollection(_items=("a", 1, "b", 2.0))
            >>> sorted(t.__name__ for t in coll.types())
            ['float', 'int', 'str']
        """
        return frozenset(type(item) for item in self._items)

    def by_type(self) -> "Mapping[type, tuple[object, ...]]":
        """Group items by their type.

        Returns:
            Immutable mapping from type to tuple of items of that type.
            Order within each group matches original insertion order.

        Examples:
            >>> coll = MetadataCollection(_items=("a", 1, "b", 2))
            >>> grouped = coll.by_type()
            >>> list(grouped[str])
            ['a', 'b']
            >>> list(grouped[int])
            [1, 2]
        """
        groups: dict[type, list[object]] = {}
        for item in self._items:
            item_type = type(item)
            if item_type not in groups:
                groups[item_type] = []
            groups[item_type].append(item)
        # Convert lists to tuples for immutability
        result: dict[type, tuple[object, ...]] = {
            k: tuple(v) for k, v in groups.items()
        }
        return MappingProxyType(result)


# Initialize the EMPTY singleton after class definition
# This is protected by Python's import lock, ensuring thread safety
MetadataCollection.EMPTY = MetadataCollection()


__all__ = [
    "MetadataCollection",
    "MetadataNotFoundError",
    "ProtocolNotRuntimeCheckableError",
]
