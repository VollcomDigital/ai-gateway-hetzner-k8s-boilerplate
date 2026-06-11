#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

yamllint "${ROOT}"
markdownlint "${ROOT}/**/*.md" --config "${ROOT}/.markdownlint.json"
bash "${ROOT}/scripts/kubeconform.sh"
bash "${ROOT}/scripts/helm-validate.sh" || true
pytest "${ROOT}/tests/" -q
