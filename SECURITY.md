# Security Policy

## Supported Versions

Security fixes are applied to the latest `main` branch.
Older snapshots, tags, and forks are not guaranteed to receive patches.

## Reporting a Vulnerability

Do not open public GitHub issues for security vulnerabilities.

Use one of these private channels:

1. GitHub Security Advisories (preferred): create a private report in the repository's Security tab.
2. Email: `info@sd-group.com.au`.

For public repositories, maintainers should enable GitHub private vulnerability reporting in repository settings.

Include:

- Affected component and version/commit.
- Reproduction steps or proof of concept.
- Expected impact and severity.
- Any suggested remediation.

## Response Process

The project maintainers aim to:

- Acknowledge reports within 3 business days.
- Confirm validity and severity as quickly as possible.
- Release a fix and advisory once remediation is available.

## Scope

In scope:

- Authentication and authorization bypass.
- Token/session handling weaknesses.
- Sensitive data exposure.
- Injection vulnerabilities (SQL, command, template).
- Privilege escalation and broken access control.

Out of scope:

- Vulnerabilities only present in unsupported forks.
- Issues requiring local developer misconfiguration of secrets.
- Automated dependency alerts without a working exploit path.
