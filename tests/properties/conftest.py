from pathlib import Path

import pytest
from hypothesis import HealthCheck, Phase, Verbosity, settings

from typing_graph import cache_clear

_THIS_DIR = Path(__file__).parent


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Add 'property' marker to all tests in this directory."""
    for item in items:
        if Path(item.fspath).is_relative_to(_THIS_DIR):
            item.add_marker(pytest.mark.property)


settings.register_profile(
    "ci",
    max_examples=150,
    deadline=None,
    database=None,  # Avoid parallel access issues with pytest-xdist
    phases=[Phase.explicit, Phase.reuse, Phase.generate],  # No shrink for speed
    suppress_health_check=[HealthCheck.too_slow],
)

settings.register_profile(
    "dev",
    max_examples=50,
    deadline=1000,  # 1 second per example
    phases=[Phase.explicit, Phase.reuse, Phase.generate],
)

settings.register_profile(
    "thorough",  # For nightly/scheduled runs
    max_examples=500,
    deadline=None,
    phases=[Phase.explicit, Phase.reuse, Phase.generate, Phase.shrink],
)

settings.register_profile(
    "debug",
    max_examples=10,
    verbosity=Verbosity.verbose,
    deadline=None,
)

# Default to dev profile
settings.load_profile("dev")


@pytest.fixture(autouse=True)
def cache_clear_between_tests():
    """Clear type cache before and after each test."""

    cache_clear()
    yield
    cache_clear()
