#!/usr/bin/env python
# pyright: reportAny=false
r"""Profiling script for MetadataCollection critical paths.

This script exercises MetadataCollection methods that showed performance gaps
during baseline benchmarking, generating workloads suitable for profiling.

Usage:
    # Run with cProfile (no root required):
    just run-python scripts/profile_metadata.py <profile> --cprofile

    # Generate flame graph with py-spy (requires sudo on macOS):
    sudo py-spy record -o flamegraph.svg -- \
        just run-python scripts/profile_metadata.py <profile>

    # Save cProfile output to file:
    just run-python scripts/profile_metadata.py <profile> --cprofile \
        --output profile.prof

Available profiles:
    find_protocol   - Protocol matching operations (HIGH: 12.8x gap)
    equality        - __eq__ comparisons (HIGH: 4.2x gap)
    map             - map() transformations (MEDIUM: 2.2x gap)
    is_hashable     - is_hashable property (MEDIUM: 2.1x gap)
    sequence        - Sequence protocol operations (LOW: 1.3-1.7x gap)
    all             - Run all profiles sequentially
"""

import argparse
import cProfile
import pstats
import sys
from dataclasses import dataclass
from io import StringIO
from typing import TYPE_CHECKING, Protocol, runtime_checkable
from typing_extensions import override

if TYPE_CHECKING:
    from collections.abc import Callable

# Add src to path for development
sys.path.insert(0, "src")

from typing_graph import MetadataCollection


# Marker classes for profiling
@dataclass(slots=True, frozen=True)
class ProfileMarker:
    """Basic marker for profiling."""

    value: int


class NonValidator:
    """Class that does not implement SupportsValidate."""


@runtime_checkable
class SupportsValidate(Protocol):
    """Protocol for types that support validation."""

    def validate(self) -> bool:
        """Validate the object."""
        ...


class ValidatorImpl:
    """Implementation of SupportsValidate protocol."""

    def validate(self) -> bool:
        """Return True to indicate valid state."""
        return True


# Error message constant for UnhashableMarker
_UNHASHABLE_MSG = "unhashable type: 'UnhashableMarker'"


class UnhashableMarker:
    """Unhashable marker for testing is_hashable fallback path.

    Args:
        value: Integer value for the marker.
    """

    value: int

    def __init__(self, value: int) -> None:
        """Initialize marker with value."""
        self.value = value

    @override
    def __hash__(self) -> int:
        """Raise TypeError to simulate unhashable type."""
        raise TypeError(_UNHASHABLE_MSG)

    @override
    def __eq__(self, other: object) -> bool:
        """Compare by value equality."""
        if not isinstance(other, UnhashableMarker):
            return NotImplemented
        return self.value == other.value


# Profile iteration counts - high enough for statistically significant sampling
_DEFAULT_ITERATIONS = 50_000
# Use a mutable container to avoid global statement
_config: dict[str, int] = {"iterations": _DEFAULT_ITERATIONS}


def get_iterations() -> int:
    """Get the current iteration count."""
    return _config["iterations"]


def set_iterations(value: int) -> None:
    """Set the iteration count."""
    _config["iterations"] = value


def profile_find_protocol() -> None:
    """Profile find_protocol() - the worst performer (12.8x gap).

    This exercises:
    - _ensure_runtime_checkable() validation
    - isinstance() checks against Protocol types
    - Collection creation for results
    """
    # Create collection with ~30% validators (same as benchmark)
    items: list[object] = [ValidatorImpl() for _ in range(30)]
    items.extend(NonValidator() for _ in range(70))
    collection = MetadataCollection.of(items)

    # Warm up
    for _ in range(100):
        _ = collection.find_protocol(SupportsValidate)

    # Main profiling loop
    iterations = get_iterations()
    print(f"  Running find_protocol x{iterations}...")
    for _ in range(iterations):
        _ = collection.find_protocol(SupportsValidate)


def profile_equality() -> None:
    """Profile __eq__() - second worst performer (4.2x gap).

    This exercises:
    - isinstance() type check
    - Tuple equality comparison
    - Different length early exit (should be fast but isn't)
    """
    # Same collections - tests element-by-element comparison
    items_same = [ProfileMarker(value=i) for i in range(100)]
    same1 = MetadataCollection.of(items_same)
    same2 = MetadataCollection.of(items_same)

    # Different length collections - tests early exit path
    items_diff1 = [ProfileMarker(value=i) for i in range(100)]
    items_diff2 = [ProfileMarker(value=i) for i in range(50)]
    diff1 = MetadataCollection.of(items_diff1)
    diff2 = MetadataCollection.of(items_diff2)

    # Warm up
    for _ in range(100):
        _ = same1 == same2
        _ = diff1 == diff2

    # Main profiling loop - mix of same and different
    # Using explicit if/else for clear profiling separation (not ternary)
    iterations = get_iterations()
    print(f"  Running equality x{iterations}...")
    for i in range(iterations):
        if i % 2 == 0:  # noqa: SIM108
            _ = same1 == same2  # Same length, element-by-element
        else:
            _ = diff1 == diff2  # Different length, should early exit


def profile_map() -> None:
    """Profile map() - 2.2x gap.

    This exercises:
    - Generator expression overhead
    - tuple() construction from generator
    - Function call overhead
    """
    items = [ProfileMarker(value=i) for i in range(100)]
    collection = MetadataCollection.of(items)

    def transform(m: object) -> object:
        if isinstance(m, ProfileMarker):
            return ProfileMarker(value=m.value * 2)
        return m

    # Warm up
    for _ in range(100):
        _ = collection.map(transform)

    # Main profiling loop
    iterations = get_iterations()
    print(f"  Running map x{iterations}...")
    for _ in range(iterations):
        _ = collection.map(transform)


def profile_is_hashable() -> None:
    """Profile is_hashable property - 2.1x gap.

    This exercises:
    - Try/except overhead for positive case
    - hash() on tuple
    - Early exit for unhashable items
    """
    # Positive case: all hashable items
    hashable_items = [ProfileMarker(value=i) for i in range(100)]
    hashable_coll = MetadataCollection.of(hashable_items)

    # Negative case: unhashable at start for early exit
    unhashable_items: list[object] = [UnhashableMarker(value=0)]
    unhashable_items.extend(ProfileMarker(value=i) for i in range(99))
    unhashable_coll = MetadataCollection.of(unhashable_items)

    # Warm up
    for _ in range(100):
        _ = hashable_coll.is_hashable
        _ = unhashable_coll.is_hashable

    # Main profiling loop - mix of positive and negative
    # Using explicit if/else for clear profiling separation (not ternary)
    iterations = get_iterations()
    print(f"  Running is_hashable x{iterations}...")
    for i in range(iterations):
        if i % 2 == 0:  # noqa: SIM108
            _ = hashable_coll.is_hashable
        else:
            _ = unhashable_coll.is_hashable


def profile_sequence() -> None:
    """Profile sequence protocol methods - 1.3-1.7x gaps.

    This exercises:
    - __len__() - tuple length
    - __bool__() - bool(tuple)
    - is_empty property - not tuple
    """
    items = [ProfileMarker(value=i) for i in range(1000)]
    collection = MetadataCollection.of(items)

    # Warm up
    for _ in range(100):
        _ = len(collection)
        _ = bool(collection)
        _ = collection.is_empty

    # Main profiling loop
    iterations = get_iterations()
    print(f"  Running sequence protocol x{iterations}...")
    for _ in range(iterations):
        _ = len(collection)
        _ = bool(collection)
        _ = collection.is_empty


PROFILES: dict[str, "Callable[[], None]"] = {
    "find_protocol": profile_find_protocol,
    "equality": profile_equality,
    "map": profile_map,
    "is_hashable": profile_is_hashable,
    "sequence": profile_sequence,
}


def run_with_cprofile(
    func: "Callable[[], None]",
    name: str,
    output_file: str | None = None,
    top_n: int = 30,
) -> str:
    """Run a function with cProfile and return formatted results.

    Args:
        func: The function to profile.
        name: Name of the profile for output.
        output_file: Optional file path to save .prof output.
        top_n: Number of top functions to show.

    Returns:
        Formatted profiling results as a string.
    """
    profiler = cProfile.Profile()
    profiler.enable()
    func()
    profiler.disable()

    # Save to file if requested
    if output_file:
        profiler.dump_stats(output_file)
        print(f"  Profile saved to: {output_file}")

    # Generate text output
    output = StringIO()
    stats = pstats.Stats(profiler, stream=output)
    _ = stats.strip_dirs()

    _ = output.write(f"\n{'=' * 70}\n")
    _ = output.write(f"Profile: {name}\n")
    _ = output.write(f"{'=' * 70}\n\n")

    # Sort by cumulative time
    _ = output.write("Top functions by cumulative time:\n")
    _ = output.write("-" * 70 + "\n")
    _ = stats.sort_stats("cumulative")
    _ = stats.print_stats(top_n)

    # Sort by total time (self time)
    _ = output.write("\nTop functions by self time:\n")
    _ = output.write("-" * 70 + "\n")
    _ = stats.sort_stats("tottime")
    _ = stats.print_stats(top_n)

    return output.getvalue()


def main() -> int:
    """Run the specified profiling workload."""
    parser = argparse.ArgumentParser(
        description="Profile MetadataCollection critical paths",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    _ = parser.add_argument(
        "profile",
        choices=[*PROFILES.keys(), "all"],
        help="Profile to run",
    )
    _ = parser.add_argument(
        "--iterations",
        type=int,
        default=_DEFAULT_ITERATIONS,
        help=f"Number of iterations (default: {_DEFAULT_ITERATIONS})",
    )
    _ = parser.add_argument(
        "--cprofile",
        action="store_true",
        help="Run with cProfile and show detailed statistics",
    )
    _ = parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file for cProfile results (.prof format)",
    )
    _ = parser.add_argument(
        "--top",
        type=int,
        default=30,
        help="Number of top functions to show (default: 30)",
    )

    args = parser.parse_args()

    # Extract typed values from args (argparse returns Any)
    profile_name: str = args.profile
    iterations: int = args.iterations
    use_cprofile: bool = args.cprofile
    output_file: str | None = args.output
    top_n: int = args.top

    # Update iterations if specified
    if iterations != _DEFAULT_ITERATIONS:
        set_iterations(iterations)

    if use_cprofile:
        # Run with cProfile
        if profile_name == "all":
            for name, func in PROFILES.items():
                output_path = None
                if output_file:
                    output_path = f"{output_file.rsplit('.', 1)[0]}_{name}.prof"
                result = run_with_cprofile(func, name, output_path, top_n)
                print(result)
        else:
            result = run_with_cprofile(
                PROFILES[profile_name], profile_name, output_file, top_n
            )
            print(result)
    elif profile_name == "all":
        # Standard run (for py-spy or timing) - all profiles
        for name, func in PROFILES.items():
            print(f"Profile: {name}")
            func()
            print()
    else:
        # Standard run (for py-spy or timing) - single profile
        print(f"Profile: {profile_name}")
        PROFILES[profile_name]()

    print("Profiling complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
