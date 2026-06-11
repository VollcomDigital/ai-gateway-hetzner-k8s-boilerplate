# ai-gateway-hetzner-k8s-boilerplate

Flux GitOps boilerplate for a **LiteLLM AI gateway** on Hetzner Kubernetes — alias routing, MCP RBAC, optional vLLM inference, dual network paths (public Cursor + Tailscale internal), and OTel/LGTM observability hooks.

> **Agents:** see [AGENTS.md](AGENTS.md) · **Deploy checklist:** [tasks/todo.md](tasks/todo.md) · **Docs index:** [docs/README.md](docs/README.md)

## Architecture decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Gateway | LiteLLM Proxy | OpenAI-compatible API, virtual keys, MCP gateway, mature Helm chart |
| GitOps | Flux `HelmRelease` + Kustomize overlays | Matches existing Vollcom k8s patterns |
| Routing | Alias layer (`chat-default`, `code-default`, …) | Swap providers without touching consumers |
| Public path | Ingress `/v1` + `/anthropic` | Cursor + Claude-native clients |
| Internal path | Tailscale-exposed ClusterIP Service | Hermes, Open WebUI, n8n stay off the public internet |
| Secrets | External Secrets Operator templates | No plaintext provider keys in Git |
| Observability | OTel + Prometheus → Alloy → Tempo/Mimir | GenAI semantic conventions |

Core platform components (Terraform, ingress controller, cert-manager, Tailscale operator, Alloy) remain in your **foundation** stack — this repo ships app-layer manifests only.

## Repository layout

```text
k8s/
  bootstrap/namespaces.yaml
  apps/
    litellm/base/              # HelmRelease, config, ServiceMonitor
    litellm/bootstrap-governance/  # Idempotent teams/keys Job
    litellm/overlays/{staging,production}/
    litellm-db/                # Postgres, Redis, backup (+ CNPG example)
    inference/                 # vLLM self-hosted backend for chat-cheap
  networking/                  # Public ingress, Tailscale, NetworkPolicies
  secrets/external-secrets/    # ESO templates
  mcp/                         # Registry + client-template/
  observability/               # Alloy river config, alerts, dashboards, Langfuse example
  flux/                        # Flux Kustomization resources
  clusters/{staging,production}/
tasks/todo.md                  # Implementation checklist
docs/                          # Agent trace context + docs index
AGENTS.md                      # Instructions for coding agents
tests/                         # Config and layout validation (pytest)
scripts/ci-local.sh            # Local lint + kubeconform + pytest
```

## Clone for a new internal repo

1. Fork this repository into your org.
2. Replace placeholders:
   - `<PUBLIC_HOST>` — public DNS for Cursor (`k8s/networking/ingress-public.yaml`)
   - `<CERT_ISSUER>` — cert-manager ClusterIssuer name
   - `<TAILNET_HOSTNAME>` — Tailscale hostname for internal consumers
   - `<SECRET_STORE>` — External Secrets ClusterSecretStore name
   - `<VLLM_MODEL_NAME>` — HuggingFace model id in `k8s/apps/inference/vllm.yaml` and proxy config
   - `<CLIENT>` — client slug in MCP templates and per-client namespaces
3. Wire Flux to `./k8s/clusters/production` (or `staging` for pre-prod).
4. Follow `tasks/todo.md` through all phases.

## Initial configuration

Do **not** store plaintext secrets in Git. Use External Secrets (recommended) or bootstrap manually:

```bash
kubectl -n litellm create secret generic litellm-provider-keys \
  --from-literal=OPENAI_API_KEY='...' \
  --from-literal=ANTHROPIC_API_KEY='...'

kubectl -n litellm create secret generic litellm-db-secret \
  --from-literal=username='litellm' \
  --from-literal=password='...' \
  --from-literal=database='litellm'
```

Example manifests: `k8s/apps/litellm/base/provider-keys-secret.example.yaml`, `k8s/apps/litellm-db/litellm-db-secret.example.yaml`.

If your Hetzner CSI storage class is not `hcloud-volumes`, update PVC manifests in `k8s/apps/litellm-db/`.

## Flux GitOps sync

Flux reconciles in order:

1. `ai-gateway-bootstrap` → namespaces
2. `ai-gateway-secrets` → ExternalSecrets (requires ESO + ClusterSecretStore)
3. `litellm-db` → Postgres, Redis, backup
4. `ai-gateway-inference` → vLLM (optional GPU node)
5. `ai-gateway-mcp-template` → MCP client template namespace
6. `litellm` → LiteLLM proxy (production or staging overlay)
7. `litellm-bootstrap-governance` → teams, access groups, virtual keys Job
8. `ai-gateway-networking` → ingress, Tailscale, NetworkPolicies
9. `ai-gateway-observability` → PrometheusRule alerts

Entrypoints:

- Production: `./k8s/clusters/production`
- Staging: `./k8s/clusters/staging`

## Developer access with virtual keys

Developers use **virtual keys**, never provider root keys. Each consumer gets its own key scoped to aliases and budgets.

| Consumer | Network path | Alias | Notes |
|----------|--------------|-------|-------|
| Cursor | Public ingress | `code-default` | `/v1` or `/anthropic/v1/messages` |
| Open WebUI | Tailscale internal | `chat-default` | Fallback to `chat-cheap` allowed |
| Hermes | Tailscale internal | `chat-default` | Per-engineer virtual key |
| n8n agents | Tailscale internal | `agent-default` | Max steps enforced in workflow |

Example (OpenAI-compatible):

```bash
export OPENAI_API_BASE="https://<PUBLIC_HOST>/v1"
export OPENAI_API_KEY="sk-your-virtual-key"
```

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-your-virtual-key",
    base_url="https://<TAILNET_HOSTNAME>/v1",
)

resp = client.chat.completions.create(
    model="chat-default",
    messages=[{"role": "user", "content": "Hello from AI gateway"}],
)
print(resp.choices[0].message.content)
```

## Local validation

```bash
pip install -r requirements-test.txt
bash scripts/ci-local.sh
pre-commit install   # optional
```

## Security

Report vulnerabilities via GitHub private security advisories — see `SECURITY.md`.

Agent trace propagation for n8n/LangGraph: see `docs/agent-trace-context.md`.
