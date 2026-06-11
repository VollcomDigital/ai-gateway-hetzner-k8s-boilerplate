"""Validate repository layout and clone placeholders."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = [
    "k8s/apps/litellm/base/config/proxy_server_config.yaml",
    "k8s/apps/litellm/overlays/production/kustomization.yaml",
    "k8s/apps/litellm/overlays/staging/kustomization.yaml",
    "k8s/apps/litellm/bootstrap-governance/job.yaml",
    "k8s/apps/inference/vllm.yaml",
    "k8s/networking/ingress-public.yaml",
    "k8s/networking/networkpolicies.yaml",
    "k8s/secrets/external-secrets/litellm-secrets.yaml",
    "k8s/mcp/registry.yaml",
    "k8s/observability/alloy-config.river",
    "k8s/observability/prometheus-rules/litellm.yaml",
    "k8s/flux/litellm-bootstrap-kustomization.yaml",
    "scripts/bootstrap_litellm_governance.py",
  "k8s/apps/litellm/bootstrap-governance/bootstrap_litellm_governance.py",
    "docs/README.md",
  "AGENTS.md",
  ".github/repository-metadata.yaml",
]


@pytest.mark.parametrize("relative_path", REQUIRED_PATHS)
def test_required_boilerplate_paths_exist(relative_path: str) -> None:
    path = REPO_ROOT / relative_path
    assert path.is_file(), f"missing required boilerplate file: {relative_path}"


def test_public_ingress_does_not_expose_admin_ui() -> None:
    ingress = (REPO_ROOT / "k8s/networking/ingress-public.yaml").read_text(encoding="utf-8")
    assert "path: /ui" not in ingress
    assert "path: /v1" in ingress


def test_public_ingress_exposes_anthropic_passthrough() -> None:
    ingress = (REPO_ROOT / "k8s/networking/ingress-public.yaml").read_text(encoding="utf-8")
    assert "path: /anthropic" in ingress


def test_placeholder_convention_documented_in_readme() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "<CLIENT>" in readme or "<PUBLIC_HOST>" in readme
