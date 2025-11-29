"""Metadata collection for type annotations.

This module provides the MetadataCollection class for storing and querying
metadata extracted from Annotated type annotations.
"""

from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    Annotated,
    ClassVar,
    Protocol,
    final,
    get_args,
    get_origin,
    overload,
)
from typing_extensions import Self, override

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

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
            # Ignore: duck-typed detection can't be tracked by type system
            result.extend(item)  # pyright: ignore[reportArgumentType]
        else:
            result.append(item)
    return tuple(result)


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
        return len(self._items) > 0

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


# Initialize the EMPTY singleton after class definition
# This is protected by Python's import lock, ensuring thread safety
MetadataCollection.EMPTY = MetadataCollection()


__all__ = [
    "MetadataCollection",
    "MetadataNotFoundError",
    "ProtocolNotRuntimeCheckableError",
    "SupportsLessThan",
]
