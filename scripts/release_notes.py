#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Extract and convert changelog sections to GitHub Flavored Markdown release notes.

This script extracts a version's changelog section from CHANGELOG.md and converts
it to GitHub release notes format with highlights, categorized changes, and
upgrade notes.

Usage:
    release_notes.py <version> [--previous <prev>] [--output <file>]
    release_notes.py --help

Arguments:
    version     Version to extract (e.g., 0.4.0, 1.0.0)

Options:
    --previous  Previous version for compare link (auto-detected if not provided)
    --output    Output file path (prints to stdout if not provided)
    --draft     Generate draft release notes (includes [DRAFT] marker)
"""

import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class ChangelogSection:
    """A section from the changelog (Added, Changed, Fixed, etc.)."""

    heading: str
    content: str


@dataclass(slots=True, frozen=True)
class VersionChangelog:
    """Parsed changelog for a specific version."""

    version: str
    date: str | None
    sections: list[ChangelogSection]
    raw_content: str


# Keep a Changelog section headings we recognize
SECTION_HEADINGS = frozenset(
    {
        "Added",
        "Changed",
        "Deprecated",
        "Removed",
        "Fixed",
        "Security",
    }
)

# Pattern to match version headers: ## [X.Y.Z] or ## [Unreleased]
VERSION_HEADER_RE = re.compile(
    r"^##\s+\[(?P<version>[^\]]+)\](?:\s*-\s*(?P<date>\d{4}-\d{2}-\d{2}))?",
    re.MULTILINE,
)

# Pattern to match section headers: ### Added, ### Changed, etc.
SECTION_HEADER_RE = re.compile(r"^###\s+(\w+)\s*$", re.MULTILINE)

# Pattern to match feature subsections: #### Feature name
FEATURE_HEADER_RE = re.compile(r"^####\s+(.+)$", re.MULTILINE)

# Pattern to match PR/issue links like (#123) or [#123]
PR_LINK_RE = re.compile(r"\[#(\d+)\]\([^)]+\)|\(#(\d+)\)")

# GitHub repository for links
REPO_URL = "https://github.com/tbhb/typing-graph"


def read_changelog(path: Path | None = None) -> str:
    """Read the changelog file content."""
    if path is None:
        path = Path("CHANGELOG.md")

    if not path.exists():
        msg = f"Changelog file not found: {path}"
        raise FileNotFoundError(msg)

    return path.read_text(encoding="utf-8")


def find_version_section(content: str, version: str) -> tuple[int, int] | None:
    """Find the start and end positions of a version section.

    Returns:
        Tuple of (start, end) positions, or None if version not found.
    """
    # Find all version headers
    matches = list(VERSION_HEADER_RE.finditer(content))
    if not matches:
        return None

    # Find the target version
    target_start = None
    target_end = None

    for i, match in enumerate(matches):
        if match.group("version") == version:
            target_start = match.end()
            # End is either next version header or end of file
            if i + 1 < len(matches):
                target_end = matches[i + 1].start()
            else:
                target_end = len(content)
            return (target_start, target_end)

    return None


def extract_version_changelog(content: str, version: str) -> VersionChangelog | None:
    """Extract the changelog content for a specific version."""
    positions = find_version_section(content, version)
    if positions is None:
        return None

    start, end = positions
    raw_content = content[start:end].strip()

    # Get the version header to extract date
    for match in VERSION_HEADER_RE.finditer(content):
        if match.group("version") == version:
            date = match.group("date")
            break
    else:
        date = None

    # Parse sections
    sections = parse_sections(raw_content)

    return VersionChangelog(
        version=version,
        date=date,
        sections=sections,
        raw_content=raw_content,
    )


def parse_sections(content: str) -> list[ChangelogSection]:
    """Parse changelog content into sections."""
    sections: list[ChangelogSection] = []

    # Split by section headers
    parts = SECTION_HEADER_RE.split(content)

    # parts[0] is content before first section header (usually empty)
    # Then alternating: heading, content, heading, content, ...
    i = 1
    while i < len(parts):
        heading = parts[i].strip()
        section_content = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if heading in SECTION_HEADINGS and section_content:
            sections.append(ChangelogSection(heading=heading, content=section_content))
        i += 2

    return sections


def find_previous_version(content: str, current_version: str) -> str | None:
    """Find the version before the current one in the changelog."""
    matches = list(VERSION_HEADER_RE.finditer(content))

    for i, match in enumerate(matches):
        # Return next version (which is the previous release)
        if match.group("version") == current_version and i + 1 < len(matches):
            return matches[i + 1].group("version")
    return None


def extract_highlights(sections: list[ChangelogSection]) -> list[str]:
    """Extract notable features to highlight.

    Features with #### subheadings in Added section become highlights.
    """
    highlights: list[str] = []

    for section in sections:
        if section.heading != "Added":
            continue

        # Find feature subheadings
        for match in FEATURE_HEADER_RE.finditer(section.content):
            feature_name = match.group(1).strip()
            # Clean up feature name (remove backticks, etc.)
            feature_name = feature_name.replace("`", "")
            highlights.append(feature_name)

    return highlights


def convert_pr_links(text: str) -> str:
    """Convert PR/issue links to GitHub auto-linking format.

    Converts [#123](url) and (#123) to just #123.
    """

    def replace_link(match: re.Match[str]) -> str:
        # Group 1 is from [#N](url), group 2 is from (#N)
        num = match.group(1) or match.group(2)
        return f"#{num}"

    return PR_LINK_RE.sub(replace_link, text)


def format_section_content(content: str) -> str:
    """Format a section's content for GitHub release notes.

    - Converts PR links to auto-linking format
    - Removes feature subheadings (promoted to highlights)
    - Cleans up formatting
    """
    # Convert PR links
    result = convert_pr_links(content)

    # Remove feature subheadings (#### lines) - they go to highlights
    result = FEATURE_HEADER_RE.sub("", result)

    # Clean up multiple blank lines
    result = re.sub(r"\n{3,}", "\n\n", result)

    return result.strip()


def extract_breaking_changes(sections: list[ChangelogSection]) -> list[str]:
    """Extract breaking changes from Changed and Removed sections.

    Scans the Changed and Removed sections for items that mention breaking changes.
    An item is considered a breaking change if:
    - It contains the word "breaking" (case-insensitive)
    - It is formatted as a list item (starts with "- ")

    Args:
        sections: List of changelog sections to search through.

    Returns:
        List of breaking change descriptions with leading "- " stripped.
        Empty list if no breaking changes found.

    Example changelog format detected:
        ### Changed
        - **Breaking**: Renamed `old_api()` to `new_api()`
        - Non-breaking change description

        ### Removed
        - **Breaking**: Removed deprecated `legacy_func()`
    """
    breaking: list[str] = []

    for section in sections:
        if section.heading not in ("Changed", "Removed"):
            continue

        # Look for "Breaking" in the content
        if "breaking" in section.content.lower():
            # Extract lines mentioning breaking changes
            breaking.extend(
                line.strip().lstrip("- ")
                for line in section.content.split("\n")
                if "breaking" in line.lower() and line.strip().startswith("-")
            )

    return breaking


def generate_release_notes(
    changelog: VersionChangelog,
    previous_version: str | None = None,
    *,
    draft: bool = False,
) -> str:
    """Generate GitHub release notes from parsed changelog."""
    lines: list[str] = []

    # Draft marker
    if draft:
        lines.append("> [!NOTE]")
        lines.append("> This is a draft release. Review and edit before publishing.")
        lines.append("")

    # Highlights section
    highlights = extract_highlights(changelog.sections)
    if highlights:
        lines.append("## Highlights")
        lines.append("")
        lines.extend(f"- **{highlight}**" for highlight in highlights)
        lines.append("")

    # What's changed section
    lines.append("## What's changed")
    lines.append("")

    for section in changelog.sections:
        formatted_content = format_section_content(section.content)
        if not formatted_content:
            continue

        lines.append(f"### {section.heading}")
        lines.append("")
        lines.append(formatted_content)
        lines.append("")

    # Upgrade notes (breaking changes)
    breaking = extract_breaking_changes(changelog.sections)
    if breaking:
        lines.append("## Upgrade notes")
        lines.append("")
        lines.extend(f"- {change}" for change in breaking)
        lines.append("")

    # Full changelog link
    if previous_version:
        lines.append("## Full changelog")
        lines.append("")
        compare_url = f"{REPO_URL}/compare/v{previous_version}...v{changelog.version}"
        lines.append(compare_url)
        lines.append("")

    return "\n".join(lines)


def parse_args(argv: list[str]) -> dict[str, str | bool | None]:
    """Parse command line arguments."""
    args: dict[str, str | bool | None] = {
        "version": None,
        "previous": None,
        "output": None,
        "draft": False,
    }

    i = 0
    while i < len(argv):
        arg = argv[i]

        if arg in {"--help", "-h"}:
            print(__doc__)
            sys.exit(0)
        elif arg == "--previous":
            if i + 1 >= len(argv):
                print(f"Error: {arg} requires a value", file=sys.stderr)
                sys.exit(1)
            args["previous"] = argv[i + 1]
            i += 2
        elif arg == "--output":
            if i + 1 >= len(argv):
                print(f"Error: {arg} requires a value", file=sys.stderr)
                sys.exit(1)
            args["output"] = argv[i + 1]
            i += 2
        elif arg == "--draft":
            args["draft"] = True
            i += 1
        elif not arg.startswith("-"):
            if args["version"] is None:
                args["version"] = arg
            else:
                print(f"Error: Unexpected argument: {arg}", file=sys.stderr)
                sys.exit(1)
            i += 1
        else:
            print(f"Error: Unknown option: {arg}", file=sys.stderr)
            sys.exit(1)

    return args


def main() -> int:
    """Extract and convert changelog to GitHub release notes."""
    args = parse_args(sys.argv[1:])

    version = args["version"]
    if not version:
        print("Error: Version argument required", file=sys.stderr)
        print(f"Usage: {sys.argv[0]} <version> [--previous <prev>] [--output <file>]")
        return 1

    # Ensure version is a string
    version = str(version)

    # Read changelog
    try:
        content = read_changelog()
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Extract version changelog
    changelog = extract_version_changelog(content, version)
    if changelog is None:
        print(f"Error: Version {version} not found in changelog", file=sys.stderr)
        return 1

    # Determine previous version
    previous = args["previous"]
    if previous is None:
        previous = find_previous_version(content, version)

    # Ensure previous is a string or None
    if previous is not None:
        previous = str(previous)

    # Generate release notes
    draft = bool(args["draft"])
    notes = generate_release_notes(changelog, previous, draft=draft)

    # Output
    output_path = args["output"]
    if output_path:
        output_path = str(output_path)
        _ = Path(output_path).write_text(notes, encoding="utf-8")
        print(f"Release notes written to: {output_path}")
    else:
        print(notes)

    return 0


if __name__ == "__main__":
    sys.exit(main())
