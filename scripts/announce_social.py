#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Draft social media announcements for Reddit and Bluesky."""

import sys

REPO_OWNER = "tbhb"
REPO_NAME = "typing-graph"
EXPECTED_ARGS = 2


def main() -> int:
    """Draft social media announcements for Reddit and Bluesky."""
    if len(sys.argv) != EXPECTED_ARGS:
        print("Usage: announce_social.py <version>", file=sys.stderr)
        return 1

    version = sys.argv[1]
    sep = "=" * 78
    sep_thin = "-" * 78

    # Reddit section
    print(f"""
{sep}
SOCIAL MEDIA ANNOUNCEMENTS - typing-graph v{version}
{sep}

REDDIT (r/python)
{sep_thin}
Post URL: https://www.reddit.com/r/Python/submit
Flair: Use "News" or "Show Python"

Title: typing-graph v{version} - Inspect and query metadata from type annotations

Body:
{sep_thin}
I just released **typing-graph v{version}**, a Python library for inspecting
and querying metadata from type annotations.

**What it does:**
- Recursively unwraps `Annotated` types and PEP 695 type aliases
- Builds a lazy, cached graph of metadata nodes
- Separates container-level metadata from element-level metadata

**Installation:**
```
pip install typing-graph=={version}
```

**Links:**
- [PyPI](https://pypi.org/project/typing-graph/{version}/)
- [GitHub](https://github.com/{REPO_OWNER}/{REPO_NAME})

Happy to answer any questions!
{sep_thin}

BLUESKY
{sep_thin}
Character limit: 300

Post (299 chars max):
{sep_thin}
typing-graph v{version} released!

A Python library for inspecting metadata from type annotations.
Unwraps Annotated types & PEP 695 aliases into a lazy, cached graph.

pip install typing-graph

pypi.org/project/typing-graph
github.com/{REPO_OWNER}/{REPO_NAME}

#Python #TypeHints #OpenSource
{sep_thin}

{sep}
Tips:
- Reddit: Post during US business hours for best visibility
- Bluesky: Include relevant hashtags (#Python, #TypeHints, #OpenSource)
- Both: Engage with comments/replies promptly
{sep}
""")

    return 0


if __name__ == "__main__":
    sys.exit(main())
