# Testing guide

This guide covers the testing strategy, tools, and practices used in typing-graph.

## Overview

typing-graph uses a comprehensive testing approach combining:

- **Unit tests** - Isolated tests for individual components
- **Integration tests** - Tests verifying component interactions
- **Property-based tests** - Hypothesis-driven tests for invariants
- **Benchmarks** - Performance regression testing with pytest-benchmark
- **Mutation testing** - Verify test quality with cosmic-ray

## Running tests

### Basic commands

```bash
just test                    # Run all tests
just test -v                 # Verbose output
just test -k "test_name"     # Run specific tests by name
just test tests/unit/        # Run only unit tests
just test tests/properties/  # Run only property tests
just test-coverage           # Run with coverage report
```

### Direct pytest usage

```bash
uv run pytest                           # Run all tests
uv run pytest -x                        # Stop on first failure
uv run pytest --tb=short                # Shorter tracebacks
uv run pytest -v --tb=long              # Verbose with full tracebacks
uv run pytest --cov=typing_graph        # With coverage
```

## Test organization

Tests are organized under `tests/`:

```text
tests/
├── unit/                    # Unit tests
│   ├── test_types.py        # Tests for _types.py
│   ├── test_node.py         # Tests for _node.py
│   └── ...
├── integration/             # Integration tests
│   ├── test_inspect_class.py
│   └── ...
├── properties/              # Property-based tests
│   ├── test_graph.py        # Graph invariant tests
│   └── ...
├── benchmarks/              # Performance benchmarks
│   ├── test_inspect_perf.py
│   └── ...
└── conftest.py              # Shared fixtures
```

### Naming conventions

- Test files: `test_<module>.py` (matching the source module)
- Test functions: `test_<scenario>_<expected_result>`
- No docstrings in tests - names should be self-explanatory

Examples:

```python
def test_inspect_type_returns_concrete_type_for_int():
    ...

def test_union_type_contains_all_variants():
    ...

def test_forward_ref_raises_on_undefined_name():
    ...
```

## Unit tests

Unit tests focus on isolated behavior of individual functions and classes.

### Structure

```python
import pytest
from typing_graph import inspect_type, ConcreteType


class TestInspectType:
    def test_returns_concrete_type_for_builtin_int(self):
        result = inspect_type(int)
        assert isinstance(result, ConcreteType)
        assert result.cls is int

    def test_returns_concrete_type_for_builtin_str(self):
        result = inspect_type(str)
        assert isinstance(result, ConcreteType)
        assert result.cls is str
```

### Best practices

- One assertion per test when possible
- Use descriptive test names
- Group related tests in classes
- Use fixtures for common setup
- Avoid testing implementation details

## Integration tests

Integration tests verify that components work together correctly. These tests exercise the public API with realistic scenarios.

### When to use

- Testing end-to-end inspection workflows
- Verifying cache behavior across multiple calls
- Testing interactions between type nodes
- Validating complex type hierarchies (nested generics, forward references)

### Example

```python
from dataclasses import dataclass
from typing import Annotated
from typing_graph import inspect_class, inspect_type, DataclassType


class TestDataclassInspection:
    def test_inspect_dataclass_with_annotated_fields(self):
        @dataclass(frozen=True, slots=True)
        class User:
            name: Annotated[str, "username"]
            age: Annotated[int, "years"]

        result = inspect_class(User)

        assert isinstance(result, DataclassType)
        assert result.frozen is True
        assert len(result.fields) == 2

        # Verify metadata hoisting works correctly
        name_field = result.fields["name"]
        assert name_field.type_node.metadata == ("username",)
```

### Best practices

- Use realistic type definitions that mirror production usage
- Test cache invalidation and reuse scenarios
- Verify error messages are helpful for common mistakes
- Test with both simple and complex type hierarchies

## Property-based tests

Property-based tests use [Hypothesis](https://hypothesis.readthedocs.io/) to generate test cases automatically.

### When to use

- Testing invariants that should hold for all inputs
- Type inspection operations
- Metadata operations
- Graph traversal

### Example

```python
from hypothesis import given, strategies as st
from typing_graph import inspect_type


@given(st.sampled_from([int, str, float, bool, bytes]))
def test_inspect_builtin_types_returns_concrete_type(typ):
    result = inspect_type(typ)
    assert isinstance(result, ConcreteType)
    assert result.cls is typ


@given(st.lists(st.integers()))
def test_list_type_has_single_element_type(elements):
    # Property: list[int] inspection should show int as element type
    result = inspect_type(list[int])
    assert len(result.args) == 1
```

### Custom strategies

Define custom strategies in `tests/conftest.py` or dedicated strategy modules:

```python
from hypothesis import strategies as st

# Strategy for generating type annotations
simple_types = st.sampled_from([int, str, float, bool, bytes, None])

generic_types = st.sampled_from([list, dict, set, tuple, frozenset])

@st.composite
def subscripted_generics(draw):
    origin = draw(generic_types)
    if origin is dict:
        return origin[draw(simple_types), draw(simple_types)]
    return origin[draw(simple_types)]
```

### Hypothesis settings

Configure Hypothesis in `pyproject.toml` or `conftest.py`:

```python
from hypothesis import settings, Phase

settings.register_profile("ci", max_examples=1000)
settings.register_profile("dev", max_examples=100)
settings.register_profile("debug", max_examples=10, phases=[Phase.generate])
```

Run with a specific profile:

```bash
uv run pytest --hypothesis-profile=ci
```

## Benchmarks

Benchmarks use [pytest-benchmark](https://pytest-benchmark.readthedocs.io/) to track performance and detect regressions.

### Running benchmarks

Using `just` recipes:

```bash
just benchmark                          # Run all benchmarks
just benchmark-save baseline            # Save results to .benchmarks/baseline.json
just benchmark-ci baseline              # Run with CI-optimized settings
just benchmark-compare baseline         # Compare against saved baseline
just benchmark-check baseline           # Fail if >15% regression vs baseline (median)
```

Using `uv run` directly:

```bash
uv run pytest tests/benchmarks/ --benchmark-only
uv run pytest tests/benchmarks/ --benchmark-json=.benchmarks/results.json
uv run pytest tests/benchmarks/ --benchmark-compare=.benchmarks/baseline.json
```

### CI variance handling

GitHub Actions runners are shared infrastructure with significant variance (10-30%) due to noisy neighbors, CPU throttling, and variable hardware. The benchmark configuration accounts for this:

| Setting | Value | Why |
|---------|-------|-----|
| `--benchmark-warmup=on` | Enabled | Primes CPU caches; reduces cold-start variance |
| `--benchmark-warmup-iterations=1000` | 1000 | Sufficient iterations to stabilize |
| `--benchmark-min-rounds=20` | 20 | More samples improve statistical significance |
| `--benchmark-max-time=2.0` | 2 seconds | Allow more time for stable measurements |
| `--benchmark-disable-gc` | Enabled | Removes garbage collection jitter |
| `--benchmark-timer=time.process_time` | CPU time | Excludes I/O wait (CI only) |

### Regression thresholds

- **Local development**: Use `benchmark-check` with median:15%
- **CI (PRs)**: Compares against baseline from main branch with median:15%
- **Why median**: Median is robust to outliers - a single spike from a noisy neighbor won't cause false failures

The 15% threshold balances detection sensitivity with false positive avoidance on shared CI infrastructure. Tighter thresholds (5%) are appropriate for dedicated/self-hosted runners.

### Writing benchmarks

```python
import pytest
from typing_graph import inspect_type


def test_inspect_simple_type_performance(benchmark):
    result = benchmark(inspect_type, int)
    assert result is not None


def test_inspect_nested_generic_performance(benchmark):
    complex_type = dict[str, list[tuple[int, str, float]]]
    result = benchmark(inspect_type, complex_type)
    assert result is not None


@pytest.mark.benchmark(group="cache")
def test_cached_inspection_performance(benchmark):
    # First call populates cache
    inspect_type(list[int])

    # Benchmark cached retrieval
    result = benchmark(inspect_type, list[int])
    assert result is not None
```

### Benchmark groups

Use groups to organize related benchmarks:

```python
@pytest.mark.benchmark(group="inspect_type")
def test_inspect_builtin(benchmark):
    benchmark(inspect_type, int)


@pytest.mark.benchmark(group="inspect_type")
def test_inspect_generic(benchmark):
    benchmark(inspect_type, list[int])
```

### Comparing results

```bash
# Save a baseline
just benchmark-save main

# Compare feature branch against baseline
just benchmark-compare main

# Fail CI if performance regresses more than 15% (median)
just benchmark-check main
```

### Regression detection

Use `benchmark-check` to fail if any benchmark regresses more than 15% (median) compared to a baseline:

```bash
just benchmark-check baseline
```

This is useful in CI to catch performance regressions before merging. The 15% median threshold is chosen to balance detection sensitivity with false positive avoidance on shared CI infrastructure.

## Mutation testing

Mutation testing verifies that tests catch bugs by introducing small changes (mutations) to the code.

### Running mutation tests

Using `just` recipes:

```bash
just mutation-init      # Initialize session (baseline + generate mutants)
just mutation-run       # Execute mutation testing
just mutation-results   # View results summary
just mutation-html      # Generate HTML report
just mutation-clean     # Clean session files
```

Using `uv run` directly:

```bash
uv run cosmic-ray baseline cosmic-ray.toml  # Verify tests pass
uv run cosmic-ray init cosmic-ray.toml session.sqlite  # Generate mutants
uv run cosmic-ray exec cosmic-ray.toml session.sqlite  # Run mutations
uv run cr-report session.sqlite             # View results
uv run cr-html session.sqlite > report.html # HTML report
```

### Interpreting results

- **Killed** - Test suite caught the mutation (good)
- **Survived** - Tests didn't catch the mutation (needs investigation)
- **Incompetent** - Mutation caused timeout or crash

### Handling survivors

When mutations survive:

1. Examine surviving mutants in the report
2. Determine if it's a meaningful change
3. Add a test that catches the mutation
4. Re-run mutation testing to verify

## Coverage

### Running coverage

```bash
just test-coverage                      # Via just
uv run pytest --cov=typing_graph --cov-report=html  # Direct
```

### Coverage requirements

- Maintain >95% branch coverage
- Focus on meaningful coverage, not just hitting lines
- Use mutation testing to verify coverage quality

### Viewing reports

```bash
uv run coverage html                    # Generate HTML report
open htmlcov/index.html                 # View in browser
```

## Fixtures

Common fixtures are defined in `tests/conftest.py`:

```python
import pytest
from typing_graph import InspectConfig


@pytest.fixture
def default_config():
    return InspectConfig()


@pytest.fixture
def strict_config():
    return InspectConfig(eval_mode=EvalMode.EAGER, max_depth=10)
```

### Fixture scope

- `function` (default) - Created for each test
- `class` - Shared within a test class
- `module` - Shared within a test module
- `session` - Shared across all tests

Use the narrowest appropriate scope to avoid test interdependencies.

## Debugging tests

### Verbose output

```bash
uv run pytest -v --tb=long              # Full tracebacks
uv run pytest -s                        # Show print statements
uv run pytest --pdb                     # Drop into debugger on failure
```

### Running single tests

```bash
uv run pytest tests/unit/test_types.py::TestConcreteType::test_specific_case
uv run pytest -k "concrete and not union"  # Pattern matching
```

### Hypothesis debugging

```bash
# Shrink to minimal failing example
uv run pytest --hypothesis-seed=<seed>

# Show all generated examples
uv run pytest --hypothesis-verbosity=verbose
```

## CI integration

Tests run automatically in GitHub Actions on pushes to `main` and pull requests.

### Pipeline stages

1. **Lint** - All linters must pass (codespell, yamllint, ruff, basedpyright, markdownlint, actionlint)
2. **Test** - Runs on multiple Python versions after lint passes
3. **Benchmark** - Runs after tests pass, uploads results as artifacts

### Python version matrix

Tests run on all supported Python versions, including free-threaded builds:

- Python 3.10, 3.11, 3.12, 3.13, 3.14
- Python 3.13t, 3.14t (free-threaded)

### Benchmark artifacts

Benchmark results are saved per Python version and uploaded as CI artifacts for comparison.

See `.github/workflows/ci.yml` for the full configuration.

## Troubleshooting

### Flaky tests

- Check for shared state between tests
- Ensure fixtures have appropriate scope
- Use `pytest-randomly` to detect order dependencies

### Slow tests

- Profile with `pytest --durations=10`
- Consider using `pytest.mark.slow` for expensive tests
- Run fast tests first: `pytest --fast-first`

### Hypothesis issues

- Increase `max_examples` if tests pass locally but fail in CI
- Use `@settings(suppress_health_check=[...])` for expensive strategies
- Check for unbounded strategies that generate huge examples
