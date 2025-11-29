#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Bump version in pyproject.toml and CITATION.cff following PEP 440."""

import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

# PEP 440 version pattern
_VERSION_RE = (
    r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
    r"(?P<pre>(?:a|b|rc)(?P<pre_num>\d+))?"
    r"(?:\.dev(?P<dev>\d+))?"
    r"(?:\.post(?P<post>\d+))?$"
)
VERSION_PATTERN = re.compile(_VERSION_RE)

EXPECTED_ARGS = 2


@dataclass(slots=True, frozen=True)
class Version:
    """Parsed PEP 440 version."""

    major: int
    minor: int
    patch: int
    pre_type: str | None
    pre_num: int
    dev: int
    post: int


def parse_version(version: str) -> Version:
    """Parse a PEP 440 version string."""
    match = VERSION_PATTERN.match(version)
    if not match:
        msg = f"Cannot parse version '{version}'"
        raise ValueError(msg)

    pre = match.group("pre")
    return Version(
        major=int(match.group("major")),
        minor=int(match.group("minor")),
        patch=int(match.group("patch")),
        pre_type=pre[0] if pre else None,
        pre_num=int(match.group("pre_num")) if match.group("pre_num") else 0,
        dev=int(match.group("dev")) if match.group("dev") else 0,
        post=int(match.group("post")) if match.group("post") else 0,
    )


def bump_version(current: str, bump_type: str) -> str:  # noqa: PLR0911
    """Calculate the new version based on bump type."""
    v = parse_version(current)

    match bump_type:
        case "major":
            return f"{v.major + 1}.0.0"
        case "minor":
            return f"{v.major}.{v.minor + 1}.0"
        case "patch":
            return f"{v.major}.{v.minor}.{v.patch + 1}"
        case "dev":
            return f"{v.major}.{v.minor}.{v.patch}.dev{v.dev + 1}"
        case "alpha" | "a":
            if v.pre_type == "a":
                return f"{v.major}.{v.minor}.{v.patch}a{v.pre_num + 1}"
            return f"{v.major}.{v.minor}.{v.patch}a1"
        case "beta" | "b":
            if v.pre_type == "b":
                return f"{v.major}.{v.minor}.{v.patch}b{v.pre_num + 1}"
            return f"{v.major}.{v.minor}.{v.patch}b1"
        case "rc":
            if v.pre_type == "r":  # 'rc' starts with 'r'
                return f"{v.major}.{v.minor}.{v.patch}rc{v.pre_num + 1}"
            return f"{v.major}.{v.minor}.{v.patch}rc1"
        case "post":
            return f"{v.major}.{v.minor}.{v.patch}.post{v.post + 1}"
        case _:
            msg = (
                f"Unknown bump type '{bump_type}'. "
                "Use: major, minor, patch, dev, alpha, beta, rc, post"
            )
            raise ValueError(msg)


def update_citation_cff(new_version: str) -> bool:
    """Update version and date-released in CITATION.cff if it exists."""
    citation_path = Path("CITATION.cff")

    if not citation_path.exists():
        print("Warning: CITATION.cff not found, skipping", file=sys.stderr)
        return False

    content = citation_path.read_text()
    today = datetime.now(tz=timezone.utc).date().isoformat()

    # Update version field
    new_content = re.sub(
        r'^version:\s*["\']?[^"\'\n]+["\']?',
        f'version: "{new_version}"',
        content,
        count=1,
        flags=re.MULTILINE,
    )

    # Update date-released field
    new_content = re.sub(
        r'^date-released:\s*["\']?[^"\'\n]+["\']?',
        f'date-released: "{today}"',
        new_content,
        count=1,
        flags=re.MULTILINE,
    )

    _ = citation_path.write_text(new_content)
    return True


def main() -> int:
    """Bump version in pyproject.toml and CITATION.cff."""
    if len(sys.argv) != EXPECTED_ARGS:
        print("Usage: version_bump.py <type>", file=sys.stderr)
        print("Types: major, minor, patch, dev, alpha, beta, rc, post", file=sys.stderr)
        return 1

    bump_type = sys.argv[1]
    pyproject_path = Path("pyproject.toml")

    if not pyproject_path.exists():
        print("Error: pyproject.toml not found", file=sys.stderr)
        return 1

    content = pyproject_path.read_text()

    # Find current version
    version_match = re.search(r'^version = "([^"]+)"', content, re.MULTILINE)
    if not version_match:
        print("Error: Could not find version in pyproject.toml", file=sys.stderr)
        return 1

    current = version_match.group(1)
    print(f"Current version: {current}")

    try:
        new = bump_version(current, bump_type)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"New version: {new}")

    # Update pyproject.toml
    new_content = re.sub(
        r'^version = "[^"]+"',
        f'version = "{new}"',
        content,
        count=1,
        flags=re.MULTILINE,
    )
    _ = pyproject_path.write_text(new_content)
    print("\u2713 Updated pyproject.toml")

    # Update CITATION.cff
    if update_citation_cff(new):
        print("\u2713 Updated CITATION.cff")

    return 0


if __name__ == "__main__":
    sys.exit(main())
