"""Configuration for documentation example tests."""

import pytest  # noqa: TC002


def pytest_configure(config: pytest.Config) -> None:
    """Register the docexamples marker."""
    config.addinivalue_line(
        "markers", "docexamples: mark test as a documentation example test"
    )
