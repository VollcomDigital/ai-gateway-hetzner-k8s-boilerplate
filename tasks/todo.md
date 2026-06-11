# AI Gateway deploy checklist

Post-clone operational runbook — not a record of boilerplate development work.  
Replace all `<PLACEHOLDER>` values before production cutover.

## Phase 0 — Clone and configure

- [ ] Fork/clone repo to internal GitHub org
- [ ] Replace `<PUBLIC_HOST>`, `<CERT_ISSUER>` in `k8s/networking/ingress-public.yaml`
- [ ] Replace `<TAILNET_HOSTNAME>` in `k8s/networking/tailscale-service.yaml`
- [ ] Replace `<SECRET_STORE>` in `k8s/secrets/external-secrets/litellm-secrets.yaml`
- [ ] Replace `<VLLM_MODEL_NAME>` in `k8s/apps/inference/vllm.yaml` and `proxy_server_config.yaml`
- [ ] Create secrets in vault: provider keys, DB, master key, drain token, Langfuse (optional)
- [ ] Review pinned LiteLLM chart (`0.1.287`) and image tag in `k8s/apps/litellm/base/helmrelease.yaml` against supply-chain policy
- [ ] (Optional) Set GitHub variable `SONAR_PROJECT_KEY=ai-gateway-hetzner-k8s-boilerplate` if using SonarCloud
- [ ] Point Flux at `./k8s/clusters/production` or `staging`
- [ ] (Optional) Remove from `k8s/flux/kustomization.yaml` if not available in target cluster:
  - `secrets-kustomization.yaml` — no External Secrets Operator
  - `inference-kustomization.yaml` — no GPU nodes for vLLM

## Phase 1 — Gateway core

- [ ] Confirm ESO synced all secrets (`litellm-master-key`, `litellm-drain-token`, …)
- [ ] Verify LiteLLM pods `2/2 Ready`
- [ ] Confirm aliases: `chat-default`, `code-default`, `agent-default`, `chat-cheap` (vLLM when inference enabled)
- [ ] Smoke: `curl -H "Authorization: Bearer $VIRTUAL_KEY" https://<PUBLIC_HOST>/v1/models`
- [ ] Smoke Anthropic: `curl https://<PUBLIC_HOST>/anthropic/v1/messages …`

## Phase 2 — Security and networking

- [ ] Validate ingress exposes `/v1` + `/anthropic` only (no `/ui`)
- [ ] Confirm NetworkPolicies (gateway ↔ DB/Redis/inference/MCP)
- [ ] Bootstrap Job created virtual keys — retrieve from LiteLLM UI or API
- [ ] Dedicated Cursor key with tight budget on `code-default`

## Phase 3 — Operability

- [ ] Postgres backup CronJob writing to PVC
- [ ] (Optional) Migrate to CNPG using `k8s/apps/litellm-db/postgres-cnpg.example.yaml`
- [ ] Staging overlay tested before prod model changes

## Phase 4 — Observability, MCP, agents

- [ ] Merge `k8s/observability/alloy-config.river` into foundation Alloy
- [ ] Import Grafana dashboard + verify PrometheusRule alerts fire in staging
- [ ] (Optional) Deploy Langfuse from `k8s/observability/langfuse/helmrelease.example.yaml`
- [ ] Clone MCP template per client; update `mcp_servers` in proxy config
- [ ] Verify MCP RBAC: engineer without Client B group does not see Client B tools
- [ ] Wire n8n trace headers per `docs/agent-trace-context.md`

## Phase 5 — Consumer onboarding

- [ ] Cursor → public URL, key `code-default`
- [ ] Open WebUI / Hermes → Tailscale URL, key `chat-default`
- [ ] n8n → Tailscale URL, key `agent-default`, max steps in workflow

## Verification gates

- [ ] `litellm_deployment_successful_fallbacks_total` spikes trigger alert
- [ ] `litellm_deployment_cooled_down_total` alert on provider flap
- [ ] Budget velocity alert on runaway agent
- [ ] Drain hook succeeds on rolling restart (`kubectl rollout restart deployment/litellm -n litellm`)
