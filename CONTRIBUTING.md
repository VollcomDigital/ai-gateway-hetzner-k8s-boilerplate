# Contributing

Thank you for your interest in contributing to the LiteLLM Hetzner K8s Boilerplate.

## Getting Started

1. Fork the repository.
2. Create a feature branch from `main`.
3. Make your changes following the guidelines below.
4. Open a pull request against `main`.

## Guidelines

### Kubernetes Manifests

- Use **2-space indentation** for all YAML files.
- Follow the existing naming conventions (`kebab-case` for resource names).
- Never commit plaintext secrets. Use `.example.yaml` files for secret templates.
- Pin container image tags to specific versions (avoid `latest`).

### Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` for new features or resources
- `fix:` for bug fixes
- `chore:` for maintenance (dependency bumps, formatting)
- `docs:` for documentation changes
- `perf:` for performance improvements

### Pull Requests

- Keep PRs focused on a single concern.
- Ensure all YAML files pass `yamllint` before submitting.
- Describe the change and its motivation in the PR description.

## Security

If you discover a security issue, please follow the process outlined in [SECURITY.md](SECURITY.md).
Do not open public issues for vulnerabilities.
