#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HELM_RELEASE="${ROOT}/k8s/apps/litellm/base/helmrelease.yaml"
CHART_VERSION="$(grep -E '^\s+version:' "${HELM_RELEASE}" | head -1 | awk '{print $2}' | tr -d '"')"
BUILD_DIR="${ROOT}/.build/helm"
mkdir -p "${BUILD_DIR}"

if ! command -v helm >/dev/null 2>&1; then
  echo "helm not installed — skipping helm validation"
  exit 0
fi

helm pull "oci://ghcr.io/berriai/litellm-helm" --version "${CHART_VERSION}" -d "${BUILD_DIR}"

helm lint "${BUILD_DIR}/litellm-helm-${CHART_VERSION}.tgz"
helm template litellm "${BUILD_DIR}/litellm-helm-${CHART_VERSION}.tgz" \
  -f "${ROOT}/k8s/apps/litellm/base/helm-values-lint.yaml" \
  > "${BUILD_DIR}/litellm-rendered.yaml"

if command -v kubeconform >/dev/null 2>&1; then
  kubeconform -summary -ignore-missing-schemas "${BUILD_DIR}/litellm-rendered.yaml"
fi

echo "helm validation passed for chart ${CHART_VERSION}"
