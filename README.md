# litellm-hetzner-k8s-boilerplate

AI Gateway boilerplate for deploying LiteLLM on our Hetzner Kubernetes cluster.

## Overview

This repository contains Kubernetes app manifests for an organization-wide AI Gateway based on LiteLLM. It is designed to run on Hetzner Kubernetes with persistent storage provided by Hetzner CSI volumes.

Core platform components like Terraform, ingress controllers, and cert-manager are intended to stay external/foundation-level and are not replaced by the app manifests in this repo.

## Kubernetes App Layout

```text
k8s/apps/litellm/
  helmrepository.yaml
  helmrelease.yaml
  configmap.yaml
  provider-keys-secret.yaml
  kustomization.yaml

k8s/apps/litellm-db/
  namespace.yaml
  postgres.yaml
  redis.yaml
  kustomization.yaml

k8s/flux/
  litellm-db-kustomization.yaml
  litellm-kustomization.yaml
  kustomization.yaml

k8s/clusters/production/
  kustomization.yaml
```

## What this includes

- LiteLLM deployment via Flux `HelmRelease`
- Official LiteLLM Helm chart source via OCI Helm repository (`ghcr.io/berriai`)
- Dedicated PostgreSQL deployment + PVC on `hcloud-volumes`
- Dedicated Redis deployment + PVC on `hcloud-volumes`
- `proxy_server_config.yaml` provided through ConfigMap and mounted into LiteLLM

## Initial Configuration

Before syncing to the cluster, replace placeholder values:

1. `k8s/apps/litellm/provider-keys-secret.yaml`
   - `OPENAI_API_KEY`
   - `ANTHROPIC_API_KEY`
2. `k8s/apps/litellm-db/postgres.yaml`
   - `litellm-db-secret` password values
3. Storage class
   - If your Hetzner CSI class is not `hcloud-volumes`, update `storageClassName` in:
     - `k8s/apps/litellm-db/postgres.yaml`
     - `k8s/apps/litellm-db/redis.yaml`

LiteLLM master key is read from `PROXY_MASTER_KEY` and is managed by the Helm chart (auto-generated unless you provide your own secret).

## Flux GitOps Sync

This repo includes Flux `Kustomization` resources in `k8s/flux`:

- `litellm-db` reconciles `./k8s/apps/litellm-db`
- `litellm` reconciles `./k8s/apps/litellm` and `dependsOn: litellm-db`

To activate this stack in an existing Flux installation, include `k8s/flux` in your cluster-level GitRepository/Kustomization entrypoint (or apply `k8s/flux/kustomization.yaml` from your existing root).

For a single-path bootstrap target, use:

- `./k8s/clusters/production`

`k8s/clusters/production/kustomization.yaml` includes `../../flux`, so Flux can be pointed at one directory and still reconcile both `litellm-db` then `litellm`.

## Developer Access with Virtual Keys

Developers should not use provider root keys directly. Instead, generate LiteLLM virtual keys with scoped permissions/budgets and share only those keys.

Typical flow:

1. Platform team creates a virtual key in LiteLLM.
2. Developer configures SDK to call the gateway URL.
3. Requests are authenticated by virtual key and routed to upstream providers.

Example OpenAI-compatible usage:

```bash
export OPENAI_API_BASE="https://ai-gateway.your-domain.example"
export OPENAI_API_KEY="sk-your-virtual-key"
```

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-your-virtual-key",
    base_url="https://ai-gateway.your-domain.example",
)

resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello from LiteLLM gateway"}],
)

print(resp.choices[0].message.content)
```