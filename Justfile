set unstable
set positional-arguments

uv := "uv run --frozen"
uv311 := "UV_PROJECT_ENVIRONMENT=.venv-3.11 uv run --frozen --python 3.11"
uv312 := "UV_PROJECT_ENVIRONMENT=.venv-3.12 uv run --frozen --python 3.12"
uv313 := "UV_PROJECT_ENVIRONMENT=.venv-3.13 uv run --frozen --python 3.13"
uv313t := "UV_PROJECT_ENVIRONMENT=.venv-3.13t uv run --frozen --python 3.13t"
uv314 := "UV_PROJECT_ENVIRONMENT=.venv-3.14 uv run --frozen --python 3.14"
uv314t := "UV_PROJECT_ENVIRONMENT=.venv-3.14t uv run --frozen --python 3.14t"
uv_release := "uv run --frozen --group release"
pnpm := "pnpm exec"

# List available recipes
default:
  @just --list

# Clean build artifacts
clean:
  rm -rf build/
  rm -rf dist/
  rm -rf site/
  find . -type d -name __pycache__ -exec rm -rf {} +
  find . -type d -name .pytest_cache -exec rm -rf {} +
  find . -type d -name .ruff_cache -exec rm -rf {} +

# Install all dependencies (Python + Node.js)
install:
  uv sync --frozen
  pnpm install --frozen-lockfile

# Install only Node.js dependencies
install-node:
  pnpm install --frozen-lockfile

# Install only Python dependencies
install-python:
  uv sync --frozen

# Run command with optional Python version (first arg: 3.14, 3.14t, or "all")
run *args:
  ./scripts/uv-run "$@"

# Run Python with optional version (first arg: 3.14, 3.14t, or "all")
run-python *args:
  ./scripts/uv-run-python "$@"

# Format code
format:
  {{uv}} codespell -w
  {{uv}} ruff format .

fix:
  {{uv}} ruff format .
  {{uv}} ruff check --fix .

fix-unsafe:
  {{uv}} ruff format .
  {{uv}} ruff check --fix --unsafe-fixes .

# Lint code
lint:
  {{uv}} codespell
  {{uv}} yamllint --strict .
  {{uv}} ruff check .
  {{uv}} basedpyright
  {{pnpm}} markdownlint-cli2 "**/*.md"

lint-ci: install
  {{uv}} codespell
  {{uv}} yamllint --strict .
  {{uv}} ruff check .
  {{uv}} basedpyright
  {{pnpm}} markdownlint-cli2 "**/*.md"

# Lint Markdown files
lint-markdown: install-node
  {{pnpm}} markdownlint-cli2 "**/*.md"

# Lint Python code
lint-python:
  {{uv}} ruff check .
  {{uv}} ruff format --check .
  {{uv}} basedpyright

# Lint documentation
lint-docs:
  uv run --frozen yamllint --strict mkdocs.yml
  pnpm exec markdownlint-cli2 "docs/**/*.md"
  uv run --frozen --group docs djlint docs/.overrides
  pnpm exec biome check docs/

# Run Vale linter
lint-prose:
  vale docs/ CODE_OF_CONDUCT.md CONTRIBUTING.md DEVELOPMENT.md README.md RELEASING.md SECURITY.md TESTING.md

# Check spelling
lint-spelling:
  {{uv}} codespell

# Run tests (optionally specify Python version as first arg: 3.14, 3.14t, or "all")
test *args:
  ./scripts/uv-run-pytest "$@"

# Run only failed tests from last run
test-failed *args: (test args "--lf")

# Run documentation example tests
test-docs *args:
  ./scripts/uv-run-pytest "$@" tests/docexamples --no-cov

# Run benchmarks
benchmark *args: install
  {{uv}} pytest tests/benchmarks/ --benchmark-only "$@"

# Run benchmarks and save results to JSON (local development)
benchmark-save name="results": install
  mkdir -p .benchmarks
  {{uv}} pytest tests/benchmarks/ --benchmark-only \
    --benchmark-warmup=on \
    --benchmark-warmup-iterations=1000 \
    --benchmark-min-rounds=20 \
    --benchmark-max-time=2.0 \
    --benchmark-disable-gc \
    --benchmark-json=.benchmarks/{{name}}.json

# Run benchmarks for CI (variance-resistant settings)
benchmark-ci name: install-python
  mkdir -p .benchmarks
  {{uv}} pytest tests/benchmarks/ --benchmark-only \
    --benchmark-warmup=on \
    --benchmark-warmup-iterations=1000 \
    --benchmark-min-rounds=20 \
    --benchmark-max-time=2.0 \
    --benchmark-disable-gc \
    --benchmark-timer=time.process_time \
    --benchmark-json=.benchmarks/{{name}}.json

# Compare benchmarks against a baseline
benchmark-compare baseline="baseline": install
  {{uv}} pytest tests/benchmarks/ \
    --benchmark-compare=.benchmarks/{{baseline}}.json \
    --benchmark-columns=min,max,mean,median,stddev,iqr

# Run benchmarks with comparison and fail on regression (>15% slower median)
benchmark-check baseline="baseline": install
  {{uv}} pytest tests/benchmarks/ \
    --benchmark-compare=.benchmarks/{{baseline}}.json \
    --benchmark-compare-fail=median:15%

# Update documentation examples (refresh output blocks)
update-docs *args:
  {{uv}} pytest tests/docexamples/ --update-examples "$@"

# Initialize mutation testing session
mutation-init:
  {{uv}} cosmic-ray baseline cosmic-ray.toml
  {{uv}} cosmic-ray init cosmic-ray.toml session.sqlite

# Run mutation testing
mutation-run:
  {{uv}} cosmic-ray exec cosmic-ray.toml session.sqlite

# Show mutation testing results
mutation-results:
  {{uv}} cr-report session.sqlite

# Generate HTML report for mutation testing
mutation-html:
  {{uv}} cr-html session.sqlite > mutation-report.html

# Clean mutation testing artifacts
mutation-clean:
  rm -f session.sqlite *-session.sqlite mutation-report.html

# Build the latest documentation
build-docs: clean
  MKDOCS_ENV=latest uv run --group docs mkdocs build
  uv pip freeze > requirements.txt

# Build the documentation for PR preview
[script]
build-docs-pr number: clean
  rm -f mkdocs.pr.yml
  cat << EOF >> mkdocs.pr.yml
  INHERIT: ./mkdocs.yml
  site_name: typing-graph Documentation (PR-{{number}})
  site_url: https://{{number}}-typing-graph-docs-pr.tbhb.workers.dev/
  EOF
  uv run --group docs mkdocs build
  echo "User-Agent: *\nDisallow: /" > site/robots.txt
  uv pip freeze > requirements.txt

# Deploy latest documentation
deploy-docs: build-docs
  pnpm exec wrangler deploy --env latest

# Deploy documentation preview
deploy-docs-pr number: (build-docs-pr number)
  pnpm exec wrangler versions upload --env pr --preview-alias pr-{{number}}

# Develop the documentation site locally
dev-docs:
  uv run --isolated --group docs mkdocs serve --livereload --dev-addr 127.0.0.1:8000

# Sync Vale styles and dictionaries
vale-sync:
  vale sync

# Run pre-commit hooks on changed files
prek:
  {{uv}} prek

# Run pre-commit hooks on all files
prek-all:
  {{uv}} prek run --all-files

# Install pre-commit hooks
prek-install:
  {{uv}} prek install

# Convert Mermaid diagrams
mermaid *args:
  {{pnpm}} mmdc "$@"

# === Release Management ===

# Check release readiness (lint, test, coverage)
release-check:
  @echo "Checking release readiness..."
  just lint
  just test
  @echo ""
  @echo "✓ All quality gates passed!"
  @echo ""
  @echo "Manual checks required:"
  @echo "  - [ ] CHANGELOG.md updated"
  @echo "  - [ ] Version in pyproject.toml is correct"

# Build distribution packages
build:
  rm -rf dist/
  uv build --no-sources
  @echo ""
  @echo "Built packages:"
  @ls -la dist/

# Build distribution packages with SBOM
build-release:
  rm -rf dist/
  uv build --no-sources
  {{uv_release}} cyclonedx-py environment --of json -o dist/sbom.cdx.json
  @echo ""
  @echo "Built packages:"
  @ls -la dist/

# Generate SBOM for current environment
sbom output="sbom.cdx.json":
  {{uv_release}} cyclonedx-py environment --of json -o {{output}}

# Publish to TestPyPI (requires OIDC token in CI or UV_PUBLISH_TOKEN)
release-publish-testpypi:
  uv publish --publish-url https://test.pypi.org/legacy/

# Publish to PyPI (requires OIDC token in CI or UV_PUBLISH_TOKEN)
release-publish-pypi:
  uv publish

# Verify TestPyPI installation (isolated environment)
release-verify-testpypi version:
  ./scripts/verify_testpypi.py {{version}}

# Create GitHub release (triggers PyPI publish)
release-create version:
  @echo "Creating GitHub release v{{version}}..."
  gh release create v{{version}} \
    --title "v{{version}}" \
    --notes "See [CHANGELOG.md](https://github.com/tbhb/typing-graph/blob/main/CHANGELOG.md) for details."

# Create GitHub pre-release
release-create-prerelease version:
  @echo "Creating GitHub pre-release v{{version}}..."
  gh release create v{{version}} \
    --prerelease \
    --title "v{{version}}" \
    --notes "See [CHANGELOG.md](https://github.com/tbhb/typing-graph/blob/main/CHANGELOG.md) for details."

# Show release status
release-status:
  @echo "Release Status: typing-graph"
  @echo "============================"
  @echo ""
  @echo "Current version: $(grep '^version' pyproject.toml | head -1 | cut -d'"' -f2)"
  @echo "Latest tag: $(git describe --tags --abbrev=0 2>/dev/null || echo 'none')"
  @echo ""
  @echo "Commits since last tag:"
  @git log $(git describe --tags --abbrev=0 2>/dev/null || echo HEAD)..HEAD --oneline 2>/dev/null | wc -l | xargs echo "  "
  @echo ""
  @echo "Recent workflow runs:"
  @gh run list --limit 3 2>/dev/null || echo "  (gh CLI not available)"

# === Version Management ===

# Show current version
version:
  @grep '^version' pyproject.toml | head -1 | cut -d'"' -f2

# Bump version (type: major, minor, patch, dev, alpha, beta, rc, post)
version-bump type:
  ./scripts/version_bump.py {{type}}

# Bump to next major version
version-bump-major:
  just version-bump major

# Bump to next minor version
version-bump-minor:
  just version-bump minor

# Bump to next patch version
version-bump-patch:
  just version-bump patch

# Bump to next alpha pre-release
version-bump-alpha:
  just version-bump alpha

# Bump to next beta pre-release
version-bump-beta:
  just version-bump beta

# Bump to next release candidate
version-bump-rc:
  just version-bump rc

# Bump to next dev release
version-bump-dev:
  just version-bump dev

# Bump to next post release
version-bump-post:
  just version-bump post

# === Release Announcements ===

# Draft release announcement (preview without posting)
release-announce-draft version:
  ./scripts/announce_draft.py {{version}}

# Draft social media announcements for Reddit and Bluesky
release-announce-social version:
  ./scripts/announce_social.py {{version}}

# Post release announcement to GitHub Discussions
release-announce version:
  ./scripts/announce_post.py {{version}}
