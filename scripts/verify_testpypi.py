#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Verify typing-graph installation from TestPyPI in an isolated environment."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED_ARGS = 2


def main() -> int:
    """Verify package installation from TestPyPI."""
    if len(sys.argv) != EXPECTED_ARGS:
        print("Usage: verify_testpypi.py <version>", file=sys.stderr)
        return 1

    version = sys.argv[1]

    with tempfile.TemporaryDirectory() as tmpdir:
        venv_path = Path(tmpdir) / "venv"
        print(f"Creating isolated environment in {tmpdir}...")

        # Create venv
        _ = subprocess.run(  # noqa: S603
            ["uv", "venv", str(venv_path)],  # noqa: S607
            check=True,
        )

        # Install from TestPyPI
        # Use unsafe-best-match to allow TestPyPI version even when PyPI has the package
        env = {**os.environ, "VIRTUAL_ENV": str(venv_path)}
        _ = subprocess.run(  # noqa: S603
            [  # noqa: S607
                "uv",
                "pip",
                "install",
                "--index-url",
                "https://test.pypi.org/simple/",
                "--extra-index-url",
                "https://pypi.org/simple/",
                "--index-strategy",
                "unsafe-best-match",
                f"typing-graph=={version}",
            ],
            env=env,
            check=True,
        )

        # Verify installation
        python_path = venv_path / "bin" / "python"
        print("Verifying installation...")

        version_check = (
            "import typing_graph; "
            "print(f'Installed: typing-graph {typing_graph.__version__}')"
        )
        _ = subprocess.run(  # noqa: S603
            [str(python_path), "-c", version_check],
            check=True,
        )

        _ = subprocess.run(  # noqa: S603
            [
                str(python_path),
                "-c",
                "from typing_graph import inspect_type; print(inspect_type(int))",
            ],
            check=True,
        )

        print("\u2713 Verification passed")
        return 0


if __name__ == "__main__":
    sys.exit(main())
