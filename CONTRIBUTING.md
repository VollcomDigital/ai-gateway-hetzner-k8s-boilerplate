# Contributing

Thanks for improving this AI gateway Kubernetes boilerplate.

## Prerequisites

- Kubernetes and Flux familiarity
- Access to a non-production cluster for validation
- Secrets via External Secrets Operator (recommended), SOPS, or Sealed Secrets

## Development workflow

1. Branch from `main`.
2. Keep changes focused — one concern per PR.
3. Run local CI before opening a PR (see below).
4. Document operational impact for manifest changes.

## Security

Never commit plaintext credentials. Ignored secret paths (see `.gitignore`):

- `k8s/apps/litellm/base/provider-keys-secret.yaml`
- `k8s/apps/litellm/base/master-key-secret.yaml`
- `k8s/apps/litellm/base/observability-secrets.yaml`
- `k8s/apps/litellm-db/litellm-db-secret.yaml`

Use `*.example.yaml` templates only. Report vulnerabilities via `SECURITY.md`.

## Local quality checks

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-test.txt yamllint
bash scripts/ci-local.sh
pre-commit install   # optional
```

## Agent / automation contributors

See [AGENTS.md](AGENTS.md) for key paths, conventions, and validation commands.

## Pull request expectations

- Explain rollback plan for production-impacting manifest changes.
- Call out namespace, storage, secret, and Flux ordering changes explicitly.
- Ensure CI passes (lint, kubeconform, helm validate, pytest, security scans).
