# Secret Management for LiteLLM Provider Keys

**Security Notice:** Storing secrets as plain YAML in Git carries risk—developers may accidentally commit real API keys. For production, use one of the patterns below.

## Recommended Approaches

### 1. SOPS (Secrets OPerationS)

Encrypt secret files so they can be safely committed. Flux has [built-in SOPS decryption](https://fluxcd.io/flux/guides/mozilla-sops/).

```bash
# Install sops and age
# Generate age key: age-keygen -o sops-age.key

# Create .sops.yaml in k8s/apps/litellm/
creation_rules:
  - path_regex: provider-keys-secret\.yaml$
    age: age1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Encrypt (after adding real values locally)
sops -e -i provider-keys-secret.yaml
```

Configure Flux's Kustomization with `decryption.provider: sops` and provide the age private key via Secret.

### 2. External Secrets Operator (ESO)

Fetch secrets from an external store (AWS Secrets Manager, GCP Secret Manager, HashiCorp Vault). The secret never exists in Git.

1. Install [External Secrets Operator](https://external-secrets.io/) in the cluster.
2. Store `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` in your secret backend.
3. Use the `provider-keys-secret-external.yaml` example—adjust the `SecretStore` and `ExternalSecret` for your backend.
4. Remove `provider-keys-secret.yaml` from `kustomization.yaml` and add `provider-keys-secret-external.yaml` instead.

### 3. Sealed Secrets

Encrypt secrets that only the in-cluster controller can decrypt.

```bash
# Install kubeseal, ensure Sealed Secrets controller is running
kubeseal --format yaml < provider-keys-secret.yaml > provider-keys-sealed.yaml
```

Commit `provider-keys-sealed.yaml` instead of the plain secret. Swap the resource in `kustomization.yaml`.

## Development / Placeholder Use

The plain `provider-keys-secret.yaml` with placeholder values is acceptable for local development or CI that never receives real keys. **Never commit this file after replacing placeholders with real API keys.**
