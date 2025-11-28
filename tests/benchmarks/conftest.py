from collections.abc import Callable, Generator
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Annotated,
    Generic,
    Literal,
    NamedTuple,
    NewType,
    Protocol,
    TypedDict,
    TypeVar,
    runtime_checkable,
)

import pytest

from typing_graph import cache_clear

_THIS_DIR = Path(__file__).parent


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Add 'benchmark' marker to all tests in this directory."""
    for item in items:
        if Path(item.fspath).is_relative_to(_THIS_DIR):
            item.add_marker(pytest.mark.benchmark)


if TYPE_CHECKING:
    from typing_graph import TypeNode


@pytest.fixture(autouse=True)
def cache_clear_between_benchmarks() -> Generator[None, None, None]:
    cache_clear()
    yield
    cache_clear()


def build_nested_list(depth: int) -> type:
    result: type = int
    for _ in range(depth):
        result = list[result]
    return result


def build_nested_dict(depth: int) -> type:
    result: type = int
    for _ in range(depth):
        result = dict[str, result]
    return result


def build_union(arity: int) -> type:
    types = [int, str, float, bool, bytes, list, dict, set, tuple, type(None)]
    if arity > len(types):
        msg = f"Union arity must be <= {len(types)}"
        raise ValueError(msg)
    result = types[0]
    for t in types[1:arity]:
        result = result | t
    return result


def build_annotated(num_metadata: int) -> object:
    metadata = tuple(f"meta_{i}" for i in range(num_metadata))
    return Annotated[(int, *metadata)]


@dataclass(slots=True, frozen=True)
class SimpleDataclass:
    name: str
    value: int
    enabled: bool = True


@dataclass(slots=True, frozen=True)
class LargeDataclass:
    field_01: int
    field_02: str
    field_03: float
    field_04: bool
    field_05: bytes
    field_06: list[int]
    field_07: dict[str, int]
    field_08: set[str]
    field_09: tuple[int, str]
    field_10: int | None
    field_11: Annotated[int, "description"]
    field_12: list[dict[str, list[int]]]
    field_13: Callable[[int, str], bool]
    field_14: Literal["a", "b", "c"]
    field_15: type[int]
    optional_field: str | None = None
    default_field: int = 42


class SampleTypedDict(TypedDict):
    name: str
    value: int
    items: list[str]


class SampleNamedTuple(NamedTuple):
    x: int
    y: int
    label: str = "point"


@runtime_checkable
class SampleProtocol(Protocol):
    name: str

    def process(self, data: bytes) -> str: ...

    def validate(self, value: int) -> bool: ...


class SampleEnum(Enum):
    ALPHA = 1
    BETA = 2
    GAMMA = 3


T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


class GenericContainer(Generic[T]):
    value: T

    def __init__(self, value: T) -> None:
        self.value = value

    def get(self) -> T:
        return self.value

    def set(self, value: T) -> None:
        self.value = value


@dataclass(slots=True, frozen=True)
class NestedDataclass:
    simple: SimpleDataclass
    items: list[SimpleDataclass]
    mapping: dict[str, SimpleDataclass]
    optional: SimpleDataclass | None = None


UserId = NewType("UserId", int)
Username = NewType("Username", str)


# Complex type aliases for benchmarking
ComplexMapping = dict[str, list[tuple[int, str] | None]]
NestedGeneric = list[dict[str, set[frozenset[int]]]]
CallableType = Callable[[int, str, list[float]], dict[str, bool] | None]


@pytest.fixture
def simple_dataclass_type() -> type[SimpleDataclass]:
    return SimpleDataclass


@pytest.fixture
def large_dataclass_type() -> type[LargeDataclass]:
    return LargeDataclass


@pytest.fixture
def nested_dataclass_type() -> type[NestedDataclass]:
    return NestedDataclass


@pytest.fixture
def sample_typed_dict_type() -> type[SampleTypedDict]:
    return SampleTypedDict


@pytest.fixture
def sample_named_tuple_type() -> type[SampleNamedTuple]:
    return SampleNamedTuple


@pytest.fixture
def sample_protocol_type() -> type:
    return SampleProtocol


@pytest.fixture
def sample_enum_type() -> type[SampleEnum]:
    return SampleEnum


@pytest.fixture
def generic_container_type() -> type:
    return GenericContainer


def count_nodes(node: "TypeNode", visited: set[int] | None = None) -> int:
    if visited is None:
        visited = set()

    node_id = id(node)
    if node_id in visited:
        return 0

    visited.add(node_id)
    count = 1
    for child in node.children():
        count += count_nodes(child, visited)

    return count


def max_depth(node: "TypeNode", visited: set[int] | None = None) -> int:
    if visited is None:
        visited = set()

    node_id = id(node)
    if node_id in visited:
        return 0

    visited.add(node_id)
    if not node.children():
        return 1

    return 1 + max(max_depth(child, visited.copy()) for child in node.children())
