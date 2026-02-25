# Contributing Guide

Thanks for helping improve this Kubernetes boilerplate.

## Prerequisites

- Kubernetes and Flux familiarity.
- Access to a non-production cluster for validation.
- A secrets management workflow (SOPS, External Secrets, or Sealed Secrets).

## Development Workflow

1. Create a feature branch from `main`.
2. Keep changes small and focused.
3. Validate manifests and lint checks locally before opening a pull request.
4. Include clear rationale for security-sensitive changes.

## Security Requirements

- Never commit plaintext credentials, tokens, or private keys.
- Do not commit real Secret manifests (`provider-keys-secret.yaml`, `litellm-db-secret.yaml`).
- Prefer immutable image tags and chart versions when practical.
- Route vulnerability reports through `SECURITY.md`.

## Local Quality Checks

Run these checks before submitting:

```bash
yamllint .
markdownlint "**/*.md"
```

## Pull Request Expectations

- Explain operational impact and rollback plan for changes affecting production manifests.
- Highlight namespace, storage, and secret-handling changes explicitly.
- Ensure CI checks pass before requesting review.
