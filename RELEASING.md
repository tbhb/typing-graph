# Releasing typing-graph

This document describes the process for releasing new versions of typing-graph to PyPI.

## Prerequisites

- Commit access to the repository
- [PyPI Trusted Publisher](https://docs.pypi.org/trusted-publishers/) configured (see [Setup](#trusted-publisher-setup))
- [GitHub CLI](https://cli.github.com/) installed (`gh`)

## Version format

typing-graph uses [PEP 440](https://peps.python.org/pep-0440/) versioning:

| Type | Format | Example |
| ---- | ------ | ------- |
| Release | X.Y.Z | 0.1.0, 1.0.0 |
| Alpha | X.Y.ZaN | 0.2.0a1 |
| Beta | X.Y.ZbN | 0.2.0b1 |
| Release candidate | X.Y.ZrcN | 0.2.0rc1 |

**Note**: typing-graph is currently in major version zero (0.x.x). Per [SemVer](https://semver.org/#spec-item-4), breaking changes may occur on minor version bumps until 1.0.0.

## Release process

### 1. Check release readiness

Ensure all quality gates pass:

```bash
just release-check
```

This runs linting, type checking, and tests.

### 2. Update changelog

Edit `CHANGELOG.md`:

1. Move items from `[Unreleased]` to a new version section
2. Add the release date in ISO format
3. Update the compare link

```markdown
## [Unreleased]

## [0.2.0](https://github.com/tbhb/typing-graph/compare/v0.1.0...v0.2.0) - 2025-01-15

### Added
- New feature description

### Fixed
- Bug fix description
```

### 3. Update version

Use the version bump recipes:

```bash
# For a minor release (0.1.0 → 0.2.0)
just version-bump minor

# For a patch release (0.1.0 → 0.1.1)
just version-bump patch

# For a major release (0.1.0 → 1.0.0)
just version-bump major

# For pre-releases (PEP 440)
just version-bump dev    # 0.2.0 → 0.2.0.dev1 (development)
just version-bump alpha  # 0.2.0 → 0.2.0a1    (alpha)
just version-bump beta   # 0.2.0 → 0.2.0b1    (beta)
just version-bump rc     # 0.2.0 → 0.2.0rc1   (release candidate)
just version-bump post   # 0.2.0 → 0.2.0.post1 (post-release)
```

Or edit `pyproject.toml` manually:

```toml
[project]
version = "0.2.0"
```

### 4. Commit and tag

```bash
git add CHANGELOG.md pyproject.toml
git commit -m "chore(release): prepare v0.2.0"
git tag v0.2.0
git push origin main --tags
```

Pushing the tag triggers the release workflow which:

- Builds the distribution packages
- Generates SBOM (CycloneDX format)
- Tests the package installation
- Generates build provenance and SBOM attestations (Sigstore)
- Publishes to TestPyPI with attestations

### 5. Verify TestPyPI release

Wait for the workflow to complete, then verify the package installs correctly:

```bash
just release-verify-testpypi 0.2.0
```

Or manually:

```bash
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    typing-graph==0.2.0

python -c "import typing_graph; print(typing_graph.__version__)"
```

### 6. Create GitHub release

Once TestPyPI verification passes, create the GitHub release:

```bash
just release-create 0.2.0
```

Or via the GitHub UI:

1. Go to [Releases](https://github.com/tbhb/typing-graph/releases)
2. Click "Create a new release"
3. Select the tag `v0.2.0`
4. Set title to `v0.2.0`
5. Copy the changelog section as release notes
6. Click "Publish release"

Creating the GitHub release triggers the PyPI publish.

**Draft releases:** You can create a draft release to test the full publishing workflow before the final release. Each draft creation or edit automatically:

1. Computes an ephemeral version: `{base_version}.dev{run_id}` (e.g., `0.2.0.dev12345678901`)
2. Builds the package with SBOM
3. Generates attestations
4. Publishes to TestPyPI
5. Verifies installation

This lets you iterate on the release process without consuming real version numbers. When satisfied, publish the release to trigger PyPI deployment with the actual version.

### 7. Verify PyPI release

```bash
pip install typing-graph==0.2.0
python -c "import typing_graph; print(typing_graph.__version__)"
```

### 8. Create release announcements

Post announcements to GitHub Discussions and social media:

```bash
# Preview GitHub Discussions announcement
just release-announce-draft 0.2.0

# Preview Reddit and Bluesky announcements
just release-announce-social 0.2.0

# Post to GitHub Discussions (requires "Announcements" category)
just release-announce 0.2.0
```

Or use `/release:announce 0.2.0` for help drafting polished announcements for all channels.

**Channels:**

- **GitHub Discussions** - Automated via `just release-announce`
- **Reddit (r/python)** - Manual post using drafted content
- **Bluesky** - Manual post using drafted content

## Pre-releases

For alpha, beta, or release candidate versions:

```bash
# Update version to pre-release format
# pyproject.toml: version = "0.2.0a1"

git commit -am "chore(release): prepare v0.2.0a1"
git tag v0.2.0a1
git push origin main --tags

# After TestPyPI verification
just release-create-prerelease 0.2.0a1
```

Pre-releases are marked as such on GitHub and PyPI, allowing users to opt-in.

## Hotfix releases

For urgent fixes to a released version:

```bash
# Create branch from release tag
git checkout -b hotfix/v0.1.1 v0.1.0

# Apply fix
# Update CHANGELOG.md
# Update version to 0.1.1

git commit -am "fix: critical bug fix"
git commit -am "chore(release): prepare v0.1.1"
git tag v0.1.1
git push origin hotfix/v0.1.1 --tags

# Follow standard release process from here
```

## Just recipes

| Recipe | Description |
| ------ | ----------- |
| `just version` | Show current version |
| `just version-bump <type>` | Bump version (major, minor, patch, dev, alpha, beta, rc, post) |
| `just version-bump-major` | Bump major version |
| `just version-bump-minor` | Bump minor version |
| `just version-bump-patch` | Bump patch version |
| `just version-bump-dev` | Bump dev release |
| `just version-bump-alpha` | Bump alpha pre-release |
| `just version-bump-beta` | Bump beta pre-release |
| `just version-bump-rc` | Bump release candidate |
| `just version-bump-post` | Bump post release |
| `just release-check` | Run all quality gates |
| `just release-status` | Show current release status |
| `just build` | Build distribution packages |
| `just build-release` | Build with SBOM generation |
| `just sbom [output]` | Generate SBOM (CycloneDX JSON) |
| `just release-publish-testpypi` | Publish to TestPyPI |
| `just release-publish-pypi` | Publish to PyPI |
| `just release-verify-testpypi <version>` | Verify TestPyPI installation (isolated venv) |
| `just release-create <version>` | Create GitHub release |
| `just release-create-prerelease <version>` | Create GitHub pre-release |
| `just release-announce-draft <version>` | Preview GitHub Discussions announcement |
| `just release-announce-social <version>` | Preview Reddit and Bluesky announcements |
| `just release-announce <version>` | Post announcement to GitHub Discussions |

## Trusted Publisher setup

typing-graph uses [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/) for secure, token-free publishing.

### Initial setup (one-time)

#### PyPI

1. Go to [PyPI Publishing Settings](https://pypi.org/manage/account/publishing/)
2. Add a new pending publisher:
   - PyPI project name: `typing-graph`
   - Owner: `tbhb`
   - Repository: `typing-graph`
   - Workflow name: `release.yml`
   - Environment name: `pypi`

#### TestPyPI

1. Go to [TestPyPI Publishing Settings](https://test.pypi.org/manage/account/publishing/)
2. Add a new pending publisher with the same settings, but:
   - Environment name: `testpypi`

#### GitHub Environments

1. Go to repository Settings > Environments
2. Create `testpypi` environment (no protection rules needed)
3. Create `pypi` environment (optionally add required reviewers)

## Supply chain security

Each release includes:

- **SBOM**: Software Bill of Materials in CycloneDX JSON format, listing all dependencies
- **Build provenance attestation**: Sigstore-signed attestation linking artifacts to the build workflow
- **SBOM attestation**: Sigstore-signed attestation binding the SBOM to the distribution files

Verify attestations with the GitHub CLI:

```bash
gh attestation verify typing_graph-0.2.0-py3-none-any.whl --owner tbhb
```

## Troubleshooting

### Checking workflow status

```bash
# List recent release workflow runs
gh run list --workflow=release.yml --limit 5

# Watch running workflow interactively
gh run watch

# View specific run details
gh run view <run-id>

# View failed job logs
gh run view <run-id> --log-failed

# Open run in browser
gh run view <run-id> --web

# Re-run failed jobs
gh run rerun <run-id> --failed
```

### TestPyPI publish failed

1. Get the failed run:

   ```bash
   gh run list --workflow=release.yml --status=failure --limit 1
   gh run view <run-id> --log-failed
   ```

2. Verify Trusted Publisher configuration matches workflow
3. Ensure environment name is exactly `testpypi`

### PyPI publish failed

1. Check workflow logs:

   ```bash
   gh run view <run-id> --log-failed
   ```

2. Verify Trusted Publisher configuration
3. Version cannot be re-uploaded - bump to next version if needed

### Recovering from a failed release

If you need to delete a release and re-do it:

```bash
# Delete the GitHub release
gh release delete v0.1.0 --yes

# Delete the tag
git tag -d v0.1.0
git push origin --delete v0.1.0

# Fix the issue, then re-tag and push
git tag v0.1.0
git push origin main --tags
```

Note: If version was already uploaded to PyPI, you must use a new version number.

### Package install fails from TestPyPI

TestPyPI may not have all dependencies. Use `--extra-index-url` to fall back to PyPI:

```bash
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    typing-graph==<version>
```
