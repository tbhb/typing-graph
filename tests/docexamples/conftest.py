"""Configuration for documentation example tests."""

import re
import sys

import pytest  # noqa: TC002

# Regex patterns for version-specific examples
# Matches: # Python 3.12+, # Python 3.14+, etc.
_VERSION_MIN_PATTERN = re.compile(r"# Python (\d+)\.(\d+)\+")
# Matches: # Python < 3.14, # Python < 3.12, etc.
_VERSION_MAX_PATTERN = re.compile(r"# Python < (\d+)\.(\d+)")


def check_version_skip(source: str) -> str | None:
    """Check if example source contains version-specific comments.

    Parses natural language version comments and returns a skip reason
    if the current Python version doesn't match the requirement.

    Supported patterns:
        - ``# Python 3.12+`` - requires Python 3.12 or later
        - ``# Python < 3.14`` - requires Python earlier than 3.14

    Args:
        source: The example source code to check.

    Returns:
        A skip reason string if the example should be skipped, None otherwise.
    """
    # Check for minimum version requirement (e.g., # Python 3.12+)
    min_match = _VERSION_MIN_PATTERN.search(source)
    if min_match:
        major, minor = int(min_match.group(1)), int(min_match.group(2))
        if sys.version_info < (major, minor):
            return f"Example requires Python {major}.{minor}+"

    # Check for maximum version requirement (e.g., # Python < 3.14)
    max_match = _VERSION_MAX_PATTERN.search(source)
    if max_match:
        major, minor = int(max_match.group(1)), int(max_match.group(2))
        if sys.version_info >= (major, minor):
            return f"Example only applies to Python < {major}.{minor}"

    return None


def pytest_configure(config: pytest.Config) -> None:
    """Register the docexamples marker."""
    config.addinivalue_line(
        "markers", "docexamples: mark test as a documentation example test"
    )
