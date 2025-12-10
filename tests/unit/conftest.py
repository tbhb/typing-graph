from pathlib import Path

import pytest

from typing_graph._node import (
    AnyNode,
    ConcreteNode,
    NeverNode,
    ParamSpecNode,
    TypeVarNode,
    TypeVarTupleNode,
)

_THIS_DIR = Path(__file__).parent


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Add 'unit' marker to all tests in this directory."""
    for item in items:
        if Path(item.fspath).is_relative_to(_THIS_DIR):
            item.add_marker(pytest.mark.unit)


@pytest.fixture
def int_node() -> ConcreteNode:
    return ConcreteNode(cls=int)


@pytest.fixture
def str_node() -> ConcreteNode:
    return ConcreteNode(cls=str)


@pytest.fixture
def float_node() -> ConcreteNode:
    return ConcreteNode(cls=float)


@pytest.fixture
def bool_node() -> ConcreteNode:
    return ConcreteNode(cls=bool)


@pytest.fixture
def any_node() -> AnyNode:
    return AnyNode()


@pytest.fixture
def never_node() -> NeverNode:
    return NeverNode()


@pytest.fixture
def typevar_t(int_node: ConcreteNode) -> TypeVarNode:
    return TypeVarNode(name="T", bound=int_node)


@pytest.fixture
def paramspec_p() -> ParamSpecNode:
    return ParamSpecNode(name="P")


@pytest.fixture
def typevartuple_ts() -> TypeVarTupleNode:
    return TypeVarTupleNode(name="Ts")
