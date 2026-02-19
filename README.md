# litellm-hetzner-k8s-boilerplate

> **AI Gateway** — a centralized LLM proxy deployed on Hetzner Cloud Kubernetes, powered by [LiteLLM](https://docs.litellm.ai/).

This repository contains the Kubernetes manifests and GitOps configuration to run a production-grade AI Gateway that proxies requests to OpenAI, Anthropic, and any other LLM provider supported by LiteLLM.

---

## Architecture Overview

```
Developer / App
      │
      ▼
┌─────────────────┐     ┌──────────────┐
│  Ingress (nginx) │────▶│  LiteLLM     │──▶ OpenAI, Anthropic, Azure, …
│  + cert-manager  │     │  Proxy (x2)  │
└─────────────────┘     └──────┬───────┘
                               │
                 ┌─────────────┴─────────────┐
                 ▼                           ▼
          ┌────────────┐             ┌────────────┐
          │ PostgreSQL │             │   Redis    │
          │ (Hetzner   │             │ (Hetzner   │
          │  CSI PVC)  │             │  CSI PVC)  │
          └────────────┘             └────────────┘
```

| Component   | Purpose                                              |
|-------------|------------------------------------------------------|
| LiteLLM     | OpenAI-compatible proxy — routes, caches, rate-limits |
| PostgreSQL  | Stores virtual keys, spend tracking, audit logs       |
| Redis       | Response caching & rate-limit counters                |

---

## Repository Structure

```
k8s/
  apps/
    litellm/                  # LiteLLM application
      namespace.yaml
      helmrepository.yaml     # Flux HelmRepository source
      helmrelease.yaml        # Flux HelmRelease (Helm values inline)
      configmap.yaml          # proxy_server_config.yaml mounted into pods
      secrets.yaml            # API keys (PLACEHOLDER — use sealed-secrets in prod)
      kustomization.yaml
    litellm-db/               # Backing data stores
      namespace.yaml
      postgres-secret.yaml
      postgres-pvc.yaml       # Hetzner CSI — hcloud-volumes StorageClass
      postgres-deployment.yaml
      postgres-service.yaml
      redis-pvc.yaml          # Hetzner CSI — hcloud-volumes StorageClass
      redis-deployment.yaml
      redis-service.yaml
      kustomization.yaml
```

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Hetzner K8s cluster | With `hcloud-volumes` CSI StorageClass available |
| Flux CD v2 | For `HelmRelease` / `HelmRepository` reconciliation |
| NGINX Ingress Controller | Installed cluster-wide |
| cert-manager | With a `ClusterIssuer` named `letsencrypt-prod` |
| kubectl / kustomize | Local tooling for manual applies |

---

## Quick Start

### 1. Clone and configure secrets

```bash
git clone <this-repo> && cd litellm-hetzner-k8s-boilerplate

# Edit placeholder secrets (or use sealed-secrets / external-secrets)
$EDITOR k8s/apps/litellm/secrets.yaml
$EDITOR k8s/apps/litellm-db/postgres-secret.yaml
```

### 2. Update your domain

In `k8s/apps/litellm/helmrelease.yaml`, replace `ai-gateway.example.com` with your actual domain.

### 3. Deploy the database layer first

```bash
kubectl apply -k k8s/apps/litellm-db/
```

### 4. Deploy LiteLLM

```bash
# If using Flux (recommended):
kubectl apply -k k8s/apps/litellm/

# Flux will reconcile the HelmRelease automatically.
```

### 5. Verify

```bash
kubectl -n litellm get pods
kubectl -n litellm-db get pods
curl -s https://ai-gateway.example.com/health | jq .
```

---

## Connecting as a Developer — Virtual Keys

LiteLLM uses **virtual keys** so every developer and service gets its own tracked API key without ever seeing the underlying provider credentials.

### Get a virtual key from your platform admin

```bash
curl -X POST "https://ai-gateway.example.com/key/generate" \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "team_id": "engineering",
    "max_budget": 50.0,
    "duration": "30d",
    "metadata": {"user": "jane@example.com"}
  }'
```

The response contains a `key` field (e.g. `sk-abc123...`).

### Use the virtual key exactly like an OpenAI key

```python
import openai

client = openai.OpenAI(
    base_url="https://ai-gateway.example.com",
    api_key="sk-abc123...",      # your virtual key
)

response = client.chat.completions.create(
    model="gpt-4o",              # routed by LiteLLM to the real provider
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)
```

All standard OpenAI SDK features work (streaming, function calling, embeddings) because LiteLLM exposes a fully OpenAI-compatible API.

### Supported models (default config)

| Virtual Model Name | Routed To |
|-|-|
| `gpt-4o` | OpenAI `gpt-4o` |
| `gpt-4o-mini` | OpenAI `gpt-4o-mini` |
| `claude-sonnet` | Anthropic `claude-sonnet-4-20250514` |
| `claude-haiku` | Anthropic `claude-3-5-haiku-20241022` |

Add more models in `k8s/apps/litellm/configmap.yaml` under `model_list`.

---

## Production Hardening Checklist

- [ ] Replace `secrets.yaml` / `postgres-secret.yaml` with **Sealed Secrets** or **External Secrets Operator**
- [ ] Enable network policies to restrict traffic between namespaces
- [ ] Configure LiteLLM budget alerts (`alerting` in config)
- [ ] Set up Prometheus scraping (`/metrics` endpoint)
- [ ] Enable PostgreSQL backups (e.g., WAL-G to S3-compatible storage)
- [ ] Pin Helm chart and image versions to specific SHAs for reproducibility

---

## License

Internal use only. See your organization's policies.
