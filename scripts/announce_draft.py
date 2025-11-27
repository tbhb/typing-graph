#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Draft release announcement for GitHub Discussions."""

import sys
from pathlib import Path

REPO_OWNER = "tbhb"
REPO_NAME = "typing-graph"
EXPECTED_ARGS = 2


def extract_changelog_section(version: str) -> str:
    """Extract changelog section for a specific version."""
    changelog_path = Path("CHANGELOG.md")
    if not changelog_path.exists():
        return "See the changelog for details."

    content = changelog_path.read_text()
    lines = content.split("\n")

    found = False
    section_lines: list[str] = []

    for line in lines:
        if line.startswith("## ["):
            if found:
                break
            if f"[{version}]" in line or "[Unreleased]" in line:
                found = True
                continue
        if found and not line.startswith("## ["):
            section_lines.append(line)

    # Remove leading/trailing empty lines
    while section_lines and not section_lines[0].strip():
        _ = section_lines.pop(0)
    while section_lines and not section_lines[-1].strip():
        _ = section_lines.pop()

    if section_lines:
        return "\n".join(section_lines)
    return "See the changelog for details."


def main() -> int:
    """Draft release announcement for GitHub Discussions."""
    if len(sys.argv) != EXPECTED_ARGS:
        print("Usage: announce_draft.py <version>", file=sys.stderr)
        return 1

    version = sys.argv[1]
    changelog_section = extract_changelog_section(version)

    print(f"""
{"=" * 78}
RELEASE ANNOUNCEMENT DRAFT - typing-graph v{version}
{"=" * 78}

Title: typing-graph v{version} released

{"-" * 78}

We're excited to announce the release of **typing-graph v{version}**!

## What's new

{changelog_section}

## Installation

```bash
pip install typing-graph=={version}
```

## Links

- [PyPI](https://pypi.org/project/typing-graph/{version}/)
- [GitHub Release](https://github.com/{REPO_OWNER}/{REPO_NAME}/releases/tag/v{version})
- [Changelog](https://github.com/{REPO_OWNER}/{REPO_NAME}/blob/main/CHANGELOG.md)
- [Documentation](https://github.com/{REPO_OWNER}/{REPO_NAME}#readme)

---
Thank you to everyone who contributed to this release!

{"=" * 78}
To post this announcement, run: just release-announce {version}
{"=" * 78}
""")

    return 0


if __name__ == "__main__":
    sys.exit(main())
