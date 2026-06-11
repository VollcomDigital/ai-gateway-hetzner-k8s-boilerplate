# Agent guide — ai-gateway-hetzner-k8s-boilerplate

GitOps boilerplate for a production LiteLLM AI gateway on Hetzner Kubernetes. App-layer manifests only — foundation (ingress, cert-manager, Tailscale, Alloy, ESO) lives elsewhere.

## What this repo is

- **Gateway**: LiteLLM proxy with alias routing (`chat-default`, `code-default`, `agent-default`, …)
- **GitOps**: Flux reconciles from `k8s/clusters/{production,staging}`
- **Governance**: Virtual keys, teams, MCP access groups — bootstrap Job + `teams-template.yaml`
- **Inference**: Optional vLLM backend for `chat-cheap`
- **Not in scope**: Terraform, cluster provisioning, foundation Helm charts

## Key paths

| Path | Purpose |
|------|---------|
| `k8s/apps/litellm/base/config/proxy_server_config.yaml` | Routing source of truth (aliases, MCP, OTel) |
| `k8s/flux/` | Flux Kustomization chain and reconcile order |
| `k8s/apps/litellm/bootstrap-governance/` | Idempotent teams/keys Job |
| `k8s/networking/` | Public ingress, Tailscale, NetworkPolicies |
| `k8s/secrets/external-secrets/` | ESO templates (placeholders) |
| `tasks/todo.md` | Deploy checklist after clone |
| `docs/agent-trace-context.md` | n8n/LangGraph trace propagation |

## Conventions

- Clients use **alias names**, never raw provider model IDs.
- `code-default` and `agent-default` have **no silent model fallback**.
- Secrets: only `*.example.yaml` in Git; real secrets via ESO or manual bootstrap.
- Pin chart/image versions in `helmrelease.yaml` — do not use floating tags.
- Placeholders: `<PUBLIC_HOST>`, `<SECRET_STORE>`, `<CLIENT>`, `<VLLM_MODEL_NAME>`, etc.

## Before changing manifests

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-test.txt yamllint
bash scripts/ci-local.sh
```

## Do not

- Commit plaintext API keys or `*.yaml` secrets (non-example).
- Expose LiteLLM admin UI on public ingress.
- Enable response cache by default without explicit approval.
- Rename aliases in examples without updating `tests/test_litellm_config.py`.

## Flux reconcile order

`bootstrap` → `secrets` → `litellm-db` → `inference` → `mcp-template` → `litellm` → `bootstrap-governance` → `networking` → `observability`

## Docs

- [README](../README.md) — overview and clone guide
- [tasks/todo.md](../tasks/todo.md) — implementation checklist
- [docs/agent-trace-context.md](agent-trace-context.md) — agent observability
- [CONTRIBUTING.md](../CONTRIBUTING.md) — PR and security rules
