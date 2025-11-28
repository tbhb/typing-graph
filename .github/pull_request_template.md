# External pull requests are not being accepted at this time

**Thank you for your interest in contributing to typing-graph!** However, this project is currently in pre-1.0 development and is **not accepting pull requests from external contributors** during this phase.

## Why aren't PRs accepted yet?

typing-graph is in active flux as core architecture, APIs, and design patterns are being established. This phase requires the freedom to make rapid, breaking changes without coordination overhead or backwards compatibility concerns that would slow development.

## How you can contribute right now

Your contributions are valued and welcome through these channels:

- **[Report bugs and issues](https://github.com/tbhb/typing-graph/issues/new)**: Found a bug? Open an issue with a minimal reproducible example
- **[Start a discussion](https://github.com/tbhb/typing-graph/discussions)**: Questions, ideas, design feedback, or suggestions
- **[Report security vulnerabilities](https://github.com/tbhb/typing-graph/security/advisories/new)**: Use private vulnerability reporting for security issues

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed guidance on how to report bugs effectively and what makes a great issue or discussion.

## When will PRs be accepted?

Pull requests will be welcomed **around or after the initial 1.0 release**, when:

- Core APIs are more stable
- Contribution guidelines are expanded with development setup and review processes
- A clearer roadmap helps guide contribution efforts
- The project is ready to onboard contributors effectively

You can follow the project's progress by watching the repository or checking release announcements.

## What should you do now?

If you've identified a bug, improvement, or feature idea:

1. **Check if an issue already exists** for your topic
2. **Open a new issue** describing the problem or suggestion
3. **Start a discussion** if you want to explore ideas or get feedback before formal proposals

Issues and discussions are reviewed regularly, and valuable contributions at this stage will help shape the project's direction before 1.0.

---

## Maintainer checklist (internal PRs only)

*This section is for maintainer use only. If you're not the maintainer, please close this PR and open an issue or discussion instead.*

### Pre-merge verification

- [ ] All CI checks pass (linting, type checking, tests across Python versions and OSes)
- [ ] Test coverage remains >95%
- [ ] Commit messages follow conventional commits format
- [ ] Documentation is updated (if applicable)
- [ ] Breaking changes are documented (if applicable)
- [ ] Security implications are considered

### Code quality

- [ ] Linting and type checking passes: `just lint`
- [ ] Tests pass: `just test`
- [ ] Public APIs have comprehensive docstrings
- [ ] No new dependencies added without strong justification

### Description

<!-- Maintainer: Describe what this PR changes and why -->
