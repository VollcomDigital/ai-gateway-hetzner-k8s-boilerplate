"""Tests for idempotent LiteLLM governance bootstrap."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any
from unittest.mock import patch

import httpx
import pytest
import respx
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "k8s/apps/litellm/bootstrap-governance/bootstrap_litellm_governance.py"


def load_bootstrap_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("bootstrap_litellm_governance", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def bootstrap_module() -> ModuleType:
    return load_bootstrap_module()


@pytest.fixture
def governance_config() -> dict[str, Any]:
    return {
        "teams": [{"team_alias": "automation", "max_budget": 10, "budget_duration": "30d", "models": ["agent-default"]}],
        "virtual_keys": [
            {
                "key_alias": "n8n-automation",
                "team_alias": "automation",
                "models": ["agent-default"],
                "max_budget": 5,
                "budget_duration": "30d",
            }
        ],
        "access_groups": [
            {
                "group_name": "client-template-engagement",
                "models": ["chat-default"],
                "mcp_servers": ["internal-docs"],
            }
        ],
    }


@respx.mock
def test_bootstrap_is_idempotent_when_resources_exist(
    bootstrap_module: ModuleType,
    governance_config: dict[str, Any],
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "governance.yaml"
    config_path.write_text(yaml.dump(governance_config), encoding="utf-8")

    base = "http://litellm.litellm.svc.cluster.local:4000"
    respx.get(f"{base}/health/readiness").respond(200)
    respx.get(f"{base}/team/list").respond(200, json=[{"team_alias": "automation"}])
    respx.get(f"{base}/key/list").respond(200, json=[{"key_alias": "n8n-automation"}])
    respx.post(f"{base}/access_group/new").respond(409)

    with patch.dict(
        "os.environ",
        {
            "LITELLM_BASE_URL": base,
            "LITELLM_MASTER_KEY": "sk-test",
            "GOVERNANCE_CONFIG": str(config_path),
        },
        clear=False,
    ):
        bootstrap_module.bootstrap(yaml.safe_load(config_path.read_text(encoding="utf-8")))


@respx.mock
def test_bootstrap_creates_missing_team(
    bootstrap_module: ModuleType,
    governance_config: dict[str, Any],
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "governance.yaml"
    config_path.write_text(yaml.dump(governance_config), encoding="utf-8")
    base = "http://litellm.litellm.svc.cluster.local:4000"

    respx.get(f"{base}/health/readiness").respond(200)
    respx.get(f"{base}/team/list").respond(200, json=[])
    respx.post(f"{base}/team/new").respond(201, json={"team_alias": "automation"})
    respx.get(f"{base}/key/list").respond(200, json=[])
    respx.post(f"{base}/key/generate").respond(201, json={"key_alias": "n8n-automation"})
    respx.post(f"{base}/access_group/new").respond(201)

    with patch.dict(
        "os.environ",
        {
            "LITELLM_BASE_URL": base,
            "LITELLM_MASTER_KEY": "sk-test",
            "GOVERNANCE_CONFIG": str(config_path),
        },
        clear=False,
    ):
        bootstrap_module.bootstrap(yaml.safe_load(config_path.read_text(encoding="utf-8")))


@respx.mock
def test_bootstrap_fails_when_proxy_unreachable(
    bootstrap_module: ModuleType,
    governance_config: dict[str, Any],
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "governance.yaml"
    config_path.write_text(yaml.dump(governance_config), encoding="utf-8")
    base = "http://litellm.litellm.svc.cluster.local:4000"
    respx.get(f"{base}/health/readiness").respond(503)
    client = bootstrap_module.LiteLLMClient(base, "sk-test")

    with patch.dict(
        "os.environ",
        {
            "LITELLM_BASE_URL": base,
            "LITELLM_MASTER_KEY": "sk-test",
            "GOVERNANCE_CONFIG": str(config_path),
        },
        clear=False,
    ):
        with pytest.raises(RuntimeError, match="did not become ready"):
            bootstrap_module.wait_for_proxy(client, attempts=2)


def test_bootstrap_script_has_otel_tracer(bootstrap_module: ModuleType) -> None:
    assert hasattr(bootstrap_module, "TRACER")
