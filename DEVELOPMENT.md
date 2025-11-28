# Development guide

This guide covers setting up a development environment and the workflows used to develop typing-graph.

## Prerequisites

- Python 3.10 or later
- [uv](https://github.com/astral-sh/uv) - Python package manager
- [just](https://github.com/casey/just) - Command runner
- [Node.js 24](https://nodejs.org/en/) - Node.js runtime (for some linters)
- [pnpm](https://pnpm.io/) - Node.js package manager (for some linters)

## Getting started

Clone the repository and install dependencies:

```bash
git clone https://github.com/tbhb/typing-graph.git
cd typing-graph
just install
just prek-install
```

This installs both Python dependencies (via uv) and Node.js dependencies (via pnpm).

## Common commands

The project uses `just` as a command runner. Run `just --list` to see all available commands.

### Development workflow

```bash
just install          # Install all dependencies
just test             # Run the test suite
just lint             # Run all linters
just format           # Format code
just clean            # Clean build artifacts
just prek             # Run pre-commit hooks on staged files
just prek-all         # Run pre-commit hooks on all files
just prek-install     # Install pre-commit hooks
```

### Targeted commands

```bash
just lint-python      # Python linting only (ruff, basedpyright)
just lint-markdown    # Markdown linting only
just lint-spelling    # Spell checking only
just test <args>      # Pass arguments to pytest
```

### Running Python

Always use `just run-python` for Python execution:

```bash
just run-python -c "from typing_graph import inspect_type; print(inspect_type(int))"
just run-python script.py           # Run a script
just run-python 3.14 script.py      # Run with specific Python version
just run ruff check .               # Run tools with version support
```

## Code quality

All code changes must pass these quality gates:

1. **Type checking** - `just run basedpyright` with zero errors
2. **Linting** - `just run ruff check .` with no violations
3. **Tests** - All tests passing with >95% branch coverage
4. **Documentation** - Google-style docstrings for public APIs

### Type checking

The project uses [basedpyright](https://docs.basedpyright.com/) for type checking with strict settings. Run type checking with:

```bash
just run basedpyright
```

Important notes:

- Never use `from __future__ import annotations` - this project uses runtime type inspection
- Use `TYPE_CHECKING` blocks for import-only type hints
- Prefer `typing_extensions` for modern typing features on older Python versions

### Linting

The project uses [ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
just run ruff check .     # Check for issues
just run ruff format .    # Format code
```

More linters:

- [codespell](https://github.com/codespell-project/codespell) - Spell checking
- [yamllint](https://github.com/adrienverge/yamllint) - YAML linting
- [markdownlint](https://github.com/DavidAnson/markdownlint) - Markdown linting

### Testing

See [TESTING.md](TESTING.md) for detailed testing documentation.

```bash
just test                    # Run all tests
just test -k "test_name"     # Run specific tests
```

## Project structure

```text
typing-graph/
├── src/typing_graph/        # Source code
│   ├── __init__.py          # Public API exports
│   ├── _types.py            # Core type definitions
│   ├── _node.py             # Type node implementations
│   └── ...                  # Other private modules
├── tests/                   # Test suite
│   ├── unit/                # Unit tests
│   └── properties/          # Property-based tests (Hypothesis)
├── .github/workflows/       # CI/CD configuration
└── docs/                    # Documentation (if present)
```

### Code organization

- Private modules use leading underscores (`_module.py`)
- The `__init__.py` file exports the public API
- Immutable dataclasses: `@dataclass(slots=True, frozen=True)`
- Import order: stdlib, third-party, local

### Naming conventions

- Classes: `PascalCase`
- Functions and variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private members: `_leading_underscore`

## Git workflow

The project uses GitHub Flow with branch protection on `main`.

### Creating a feature branch

```bash
git checkout -b feat/my-feature
# Make changes
git commit -m "feat(module): add functionality"
git push -u origin feat/my-feature
gh pr create --title "feat(module): add functionality"
```

### Commit messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Test changes
- `build`: Build system changes
- `ci`: CI/CD changes
- `chore`: Maintenance tasks
- `revert`: Revert a previous commit

### Pre-commit hooks

Never bypass pre-commit hooks. If a hook fails, fix the issue before committing:

```bash
just prek        # Run hooks on staged files
just prek-all    # Run hooks on all files
```

## CI/CD

GitHub Actions runs on all pull requests and pushes to `main`:

1. **Lint** - Runs all linters (codespell, yamllint, ruff, basedpyright, markdownlint, actionlint)
2. **Test** - Runs tests on Python 3.10-3.14 including free-threaded builds (after lint passes)
3. **Benchmark** - Runs benchmarks and uploads results as artifacts (after tests pass)

See `.github/workflows/ci.yml` for the full configuration.

## Dependencies

### Runtime dependencies

- [typing-inspection](https://typing-inspection.pydantic.dev/) - Type introspection from Pydantic
- [annotated-types](https://github.com/annotated-types/annotated-types) - Metadata types (optional)
- [typing-extensions](https://github.com/python/typing_extensions) - Modern typing features

### Development dependencies

- pytest, pytest-cov, pytest-mock, pytest-benchmark - Testing
- hypothesis - Property-based testing
- cosmic-ray - Mutation testing
- py-spy - Profiling
- ruff - Linting and formatting
- basedpyright - Type checking
- codespell, yamllint - More linting

## Troubleshooting

### Common issues

**Import errors:**
Run `just install` to ensure the project has all dependencies.

**Test failures:**
Run `just test -v` for verbose output to identify the failing test.

### Getting help

- Check existing [GitHub issues](https://github.com/tbhb/typing-graph/issues)
- Open a new issue with a minimal reproducible example
