#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Post release announcement to GitHub Discussions."""

import json
import subprocess
import sys
from pathlib import Path
from typing import cast

REPO_OWNER = "tbhb"
REPO_NAME = "typing-graph"
EXPECTED_ARGS = 2


def run_gh_graphql(query: str, **variables: str) -> dict[str, object]:
    """Run a GitHub GraphQL query."""
    cmd = ["gh", "api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        cmd.extend(["-f", f"{key}={value}"])

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)  # noqa: S603
    return cast("dict[str, object]", json.loads(result.stdout))


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


def get_discussion_category_id() -> str | None:
    """Get the Announcements category ID from GitHub Discussions."""
    query = """
    query($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        discussionCategories(first: 10) {
          nodes { id name }
        }
      }
    }
    """
    try:
        result = run_gh_graphql(query, owner=REPO_OWNER, name=REPO_NAME)
        data = cast("dict[str, object]", result["data"])
        repo = cast("dict[str, object]", data["repository"])
        disc_cats = cast("dict[str, object]", repo["discussionCategories"])
        categories = cast("list[dict[str, str]]", disc_cats["nodes"])
        for cat in categories:
            if cat["name"] == "Announcements":
                return cat["id"]
    except (subprocess.CalledProcessError, KeyError, TypeError):
        pass
    return None


def get_repository_id() -> str | None:
    """Get the repository ID."""
    query = """
    query($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) { id }
    }
    """
    try:
        result = run_gh_graphql(query, owner=REPO_OWNER, name=REPO_NAME)
        data = cast("dict[str, object]", result["data"])
        repo = cast("dict[str, str]", data["repository"])
        return repo["id"]
    except (subprocess.CalledProcessError, KeyError, TypeError):
        return None


def create_discussion(repo_id: str, category_id: str, title: str, body: str) -> str:
    """Create a discussion and return its URL."""
    query = """
    mutation($repoId: ID!, $categoryId: ID!, $title: String!, $body: String!) {
      createDiscussion(input: {
        repositoryId: $repoId,
        categoryId: $categoryId,
        title: $title,
        body: $body
      }) {
        discussion { url }
      }
    }
    """
    result = run_gh_graphql(
        query, repoId=repo_id, categoryId=category_id, title=title, body=body
    )
    data = cast("dict[str, object]", result["data"])
    create_disc = cast("dict[str, object]", data["createDiscussion"])
    discussion = cast("dict[str, str]", create_disc["discussion"])
    return discussion["url"]


def main() -> int:
    """Post release announcement to GitHub Discussions."""
    if len(sys.argv) != EXPECTED_ARGS:
        print("Usage: announce_post.py <version>", file=sys.stderr)
        return 1

    version = sys.argv[1]
    print(f"Creating release announcement for v{version}...")

    # Get category ID
    category_id = get_discussion_category_id()
    if not category_id:
        print(
            "Error: Could not find 'Announcements' category in Discussions.",
            file=sys.stderr,
        )
        print(
            f"Ensure Discussions are enabled: https://github.com/{REPO_OWNER}/{REPO_NAME}/settings",
            file=sys.stderr,
        )
        print(
            f"Create category: https://github.com/{REPO_OWNER}/{REPO_NAME}/discussions/categories",
            file=sys.stderr,
        )
        return 1

    # Get repository ID
    repo_id = get_repository_id()
    if not repo_id:
        print("Error: Could not get repository ID.", file=sys.stderr)
        return 1

    # Extract changelog
    changelog_section = extract_changelog_section(version)

    # Build announcement body
    body = f"""We're excited to announce the release of **typing-graph v{version}**!

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
Thank you to everyone who contributed to this release!"""

    # Create discussion
    try:
        url = create_discussion(
            repo_id, category_id, f"typing-graph v{version} released", body
        )
        print(f"\u2713 Announcement created: {url}")
    except subprocess.CalledProcessError as e:
        stderr_output = cast("str | None", e.stderr)
        stderr = stderr_output if stderr_output else "unknown error"
        print(f"Error creating discussion: {stderr}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
