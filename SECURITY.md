# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in this repository, please report it responsibly.

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please send a detailed report to the repository maintainers via private channels
(e.g., GitHub Security Advisories or direct contact). Include:

1. A description of the vulnerability.
2. Steps to reproduce the issue.
3. Potential impact assessment.
4. Any suggested fixes or mitigations.

We will acknowledge receipt within **48 hours** and aim to provide a resolution or
mitigation plan within **7 business days**.

## Security Practices

- Plaintext secrets are **never** committed to this repository.
- Secret example files (`.example.yaml`) contain only placeholder values.
- Real secrets must be created out-of-band using SOPS, External Secrets Operator, Sealed Secrets, or manual `kubectl` commands.
- The `.gitignore` explicitly excludes real secret manifest files.

## Dependency Updates

Container image versions used in this repository are tracked by Dependabot.
Review and merge Dependabot PRs promptly to stay current on security patches.
