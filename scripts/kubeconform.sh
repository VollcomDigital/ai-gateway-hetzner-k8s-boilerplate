#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${ROOT}/.build/kustomize"
mkdir -p "${BUILD_DIR}"

echo "Building kustomize overlays..."
kubectl kustomize "${ROOT}/k8s/apps/litellm/overlays/production" > "${BUILD_DIR}/litellm-production.yaml"
kubectl kustomize "${ROOT}/k8s/apps/litellm/overlays/staging" > "${BUILD_DIR}/litellm-staging.yaml"
kubectl kustomize "${ROOT}/k8s/apps/litellm-db" > "${BUILD_DIR}/litellm-db.yaml"
kubectl kustomize "${ROOT}/k8s/apps/inference" > "${BUILD_DIR}/inference.yaml"
kubectl kustomize "${ROOT}/k8s/networking" > "${BUILD_DIR}/networking.yaml"
kubectl kustomize "${ROOT}/k8s/observability" > "${BUILD_DIR}/observability.yaml"
kubectl kustomize "${ROOT}/k8s/apps/litellm/bootstrap-governance" > "${BUILD_DIR}/bootstrap-governance.yaml"

if ! command -v kubeconform >/dev/null 2>&1; then
  echo "kubeconform not installed — skipping schema validation"
  exit 0
fi

SCHEMA_FLAGS=(
  -summary
  -ignore-missing-schemas
  -kubernetes-version 1.30.0
)

for manifest in "${BUILD_DIR}"/*.yaml; do
  kubeconform "${SCHEMA_FLAGS[@]}" "${manifest}"
done

echo "kubeconform validation passed"
