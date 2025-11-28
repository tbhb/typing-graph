# Security policy

## Supported versions

typing-graph is currently in early development. Security updates apply to the latest version only.

<!-- vale off -->

| Version | Supported          |
| ------- | ------------------ |
| 0.x.x   | :white_check_mark: |

<!-- vale on -->

## Python version support

typing-graph supports Python versions that have not reached end-of-life (EOL). When a Python version reaches EOL, the next minor release drops support for that version.

Supported versions start at **Python 3.10**

See the [Python Developer's Guide](https://devguide.python.org/versions/) for the official EOL schedule.

## Reporting a vulnerability

If you discover a security vulnerability in typing-graph, please report it responsibly.

### How to report

**Do not open a public GitHub issue for security vulnerabilities.**

Instead, please use GitHub's private vulnerability reporting feature:

1. Go to the [Security tab](https://github.com/tbhb/typing-graph/security) of the repository
2. Click "Report a vulnerability"
3. Fill out the form with details about the vulnerability

For more information, see [Privately reporting a security vulnerability](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability).

When reporting, please include:

1. A description of the vulnerability
2. Steps to reproduce the issue
3. Potential impact assessment
4. Any suggested fixes (optional)

### What to expect

- **Acknowledgment** - Expect acknowledgment of your report within 48 hours
- **Assessment** - Investigation and severity assessment within 7 days
- **Resolution** - Critical vulnerabilities receive fixes within 30 days
- **Disclosure** - Disclosure timing coordinated with you

### Security considerations

typing-graph processes arbitrary type annotations from user code. The following areas are particularly relevant to security:

#### Recursive depth limits

Type graphs can be deeply nested. The library implements depth limits to prevent stack overflow attacks.

#### Circular reference handling

Type aliases and forward references can create cycles. The caching mechanism prevents infinite recursion.

#### Arbitrary code execution

Inspecting annotations may trigger descriptor protocols or `__class_getitem__`. The library uses lazy evaluation to reduce unexpected code execution.

#### Memory exhaustion

Large type graphs with many union variants or fields could consume excessive memory. Consider memory limits to reduce resource consumption when processing untrusted type annotations.

#### Forward reference resolution

Forward references may reference undefined names. The library handles errors gracefully without information leakage.

## Security best practices

When using typing-graph:

1. **Validate input** - Be cautious when inspecting type annotations from untrusted sources
2. **Set depth limits** - Use the `max_depth` configuration option for untrusted input
3. **Handle errors** - Catch and handle exceptions when processing potentially malformed type annotations
4. **Track resources** - Be aware of memory usage when processing large type graphs

## Acknowledgments

Thank you to the security research community for identifying and responsibly disclosing vulnerabilities.
