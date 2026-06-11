"""Validate LiteLLM proxy config structure for the AI gateway boilerplate."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
PROXY_CONFIG = REPO_ROOT / "k8s/apps/litellm/base/config/proxy_server_config.yaml"

REQUIRED_ALIASES = {
    "chat-default",
    "code-default",
    "agent-default",
    "reasoning-heavy",
    "chat-cheap",
}

ALIASES_WITHOUT_FALLBACK = {"code-default", "agent-default"}


@pytest.fixture
def proxy_config() -> dict:
    assert PROXY_CONFIG.is_file(), f"missing config: {PROXY_CONFIG}"
    return yaml.safe_load(PROXY_CONFIG.read_text(encoding="utf-8"))


def test_required_aliases_present(proxy_config: dict) -> None:
    model_names = {entry["model_name"] for entry in proxy_config["model_list"]}
    missing = REQUIRED_ALIASES - model_names
    assert not missing, f"missing aliases: {sorted(missing)}"


def test_cache_disabled_by_default(proxy_config: dict) -> None:
    assert proxy_config["litellm_settings"]["cache"] is False


def test_otel_callbacks_enabled(proxy_config: dict) -> None:
    settings = proxy_config["litellm_settings"]
    assert "otel" in settings.get("callbacks", [])
    assert "prometheus" in settings.get("service_callbacks", [])


def test_router_pre_call_checks_enabled(proxy_config: dict) -> None:
    assert proxy_config["router_settings"]["enable_pre_call_checks"] is True


def test_code_and_agent_aliases_have_no_fallback(proxy_config: dict) -> None:
    fallbacks = proxy_config["litellm_settings"].get("fallbacks", [])
    fallback_sources = set()
    for entry in fallbacks:
        fallback_sources.update(entry.keys())
    overlap = ALIASES_WITHOUT_FALLBACK & fallback_sources
    assert not overlap, f"unexpected fallbacks for protected aliases: {sorted(overlap)}"


def test_retry_policy_distinguishes_error_classes(proxy_config: dict) -> None:
    policy = proxy_config["router_settings"]["retry_policy"]
    assert policy["TimeoutErrorRetries"] >= 1
    assert policy["RateLimitErrorRetries"] >= 1
    assert "BadRequestErrorRetries" not in policy


def test_no_raw_provider_names_as_top_level_aliases(proxy_config: dict) -> None:
    raw_patterns = ("gpt-4o-mini", "claude-3", "claude-sonnet-4")
    for entry in proxy_config["model_list"]:
        name = entry["model_name"]
        assert not any(pattern in name for pattern in raw_patterns), (
            f"raw model name exposed as alias: {name}"
        )


def test_general_settings_use_env_master_key(proxy_config: dict) -> None:
    assert proxy_config["general_settings"]["master_key"] == "os.environ/PROXY_MASTER_KEY"


def test_mcp_servers_configured(proxy_config: dict) -> None:
    servers = proxy_config.get("mcp_servers", {})
    assert "internal-docs" in servers
    assert servers["internal-docs"].get("allow_all_keys") is True
    assert "client-template-wordpress" in servers


def test_langfuse_callback_enabled(proxy_config: dict) -> None:
    assert "langfuse" in proxy_config["litellm_settings"].get("success_callback", [])


def test_drain_token_from_env(proxy_config: dict) -> None:
    assert proxy_config["general_settings"]["drain_endpoint_token"] == "os.environ/DRAIN_ENDPOINT_TOKEN"


def test_chat_cheap_uses_vllm_backend(proxy_config: dict) -> None:
    cheap_entries = [e for e in proxy_config["model_list"] if e["model_name"] == "chat-cheap"]
    api_bases = {e["litellm_params"].get("api_base", "") for e in cheap_entries}
    assert any("vllm.inference.svc.cluster.local" in base for base in api_bases)


def test_mcp_db_objects_enabled(proxy_config: dict) -> None:
    assert "mcp" in proxy_config["general_settings"].get("supported_db_objects", [])
