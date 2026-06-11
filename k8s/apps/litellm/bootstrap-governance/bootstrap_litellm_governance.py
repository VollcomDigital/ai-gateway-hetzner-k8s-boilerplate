#!/usr/bin/env python3
"""Idempotent LiteLLM governance bootstrap — teams, access groups, virtual keys."""

from __future__ import annotations

import logging
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import httpx
import yaml
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

LOG = logging.getLogger("litellm.bootstrap")
TRACER = trace.get_tracer("litellm.bootstrap")


def configure_logging(trace_id: str) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='{"level":"%(levelname)s","logger":"%(name)s","message":"%(message)s","trace_id":"'
        + trace_id
        + '"}',
    )


def configure_tracing() -> None:
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        return
    traces_url = endpoint if endpoint.endswith("/v1/traces") else f"{endpoint.rstrip('/')}/v1/traces"
    provider = TracerProvider(resource=Resource.create({"service.name": "litellm-bootstrap"}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=traces_url)))
    trace.set_tracer_provider(provider)


def load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


class LiteLLMClient:
    def __init__(self, base_url: str, master_key: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {master_key}",
            "Content-Type": "application/json",
        }

    def get(self, path: str) -> httpx.Response:
        return httpx.get(f"{self._base_url}{path}", headers=self._headers, timeout=30.0)

    def post(self, path: str, payload: dict[str, Any]) -> httpx.Response:
        return httpx.post(
            f"{self._base_url}{path}",
            headers=self._headers,
            json=payload,
            timeout=60.0,
        )


def wait_for_proxy(client: LiteLLMClient, attempts: int = 30) -> None:
    with TRACER.start_as_current_span("wait_for_proxy") as span:
        for attempt in range(1, attempts + 1):
            try:
                response = client.get("/health/readiness")
                if response.status_code == 200:
                    span.set_attribute("attempts", attempt)
                    LOG.info("LiteLLM proxy is ready")
                    return
                LOG.warning("Proxy readiness HTTP %s (attempt %s/%s)", response.status_code, attempt, attempts)
            except httpx.HTTPError as exc:
                LOG.warning("Proxy not ready (attempt %s/%s): %s", attempt, attempts, exc)
            time.sleep(5)
        raise RuntimeError("LiteLLM proxy did not become ready in time")


def list_team_aliases(client: LiteLLMClient) -> set[str]:
    response = client.get("/team/list")
    if response.status_code != 200:
        LOG.warning("Could not list teams (%s) — assuming empty", response.status_code)
        return set()
    payload = response.json()
    teams = payload if isinstance(payload, list) else payload.get("teams", [])
    return {team.get("team_alias") or team.get("team_id") for team in teams}


def ensure_team(client: LiteLLMClient, spec: dict[str, Any]) -> None:
    alias = spec["team_alias"]
    with TRACER.start_as_current_span("ensure_team") as span:
        span.set_attribute("team_alias", alias)
        existing = list_team_aliases(client)
        if alias in existing:
            LOG.info("Team already exists: %s", alias)
            return
        response = client.post("/team/new", spec)
        if response.status_code in (200, 201):
            LOG.info("Created team: %s", alias)
            return
        if response.status_code == 409:
            LOG.info("Team conflict treated as success: %s", alias)
            return
        raise RuntimeError(f"Failed to create team {alias}: {response.status_code} {response.text}")


def list_key_aliases(client: LiteLLMClient) -> set[str]:
    response = client.get("/key/list")
    if response.status_code != 200:
        LOG.warning("Could not list keys (%s) — assuming empty", response.status_code)
        return set()
    payload = response.json()
    keys = payload if isinstance(payload, list) else payload.get("keys", [])
    return {entry.get("key_alias") for entry in keys if entry.get("key_alias")}


def ensure_virtual_key(client: LiteLLMClient, spec: dict[str, Any]) -> None:
    alias = spec["key_alias"]
    with TRACER.start_as_current_span("ensure_virtual_key") as span:
        span.set_attribute("key_alias", alias)
        if alias in list_key_aliases(client):
            LOG.info("Virtual key already exists: %s", alias)
            return
        response = client.post("/key/generate", spec)
        if response.status_code in (200, 201):
            LOG.info("Created virtual key: %s", alias)
            return
        if response.status_code == 409:
            LOG.info("Virtual key conflict treated as success: %s", alias)
            return
        raise RuntimeError(f"Failed to create key {alias}: {response.status_code} {response.text}")


def ensure_access_group(client: LiteLLMClient, spec: dict[str, Any]) -> None:
    name = spec["group_name"]
    with TRACER.start_as_current_span("ensure_access_group") as span:
        span.set_attribute("access_group", name)
        response = client.post("/access_group/new", spec)
        if response.status_code in (200, 201, 409):
            LOG.info("Access group ensured: %s", name)
            return
        LOG.warning(
            "Access group API returned %s for %s — may require UI setup: %s",
            response.status_code,
            name,
            response.text,
        )


def bootstrap(config: dict[str, Any]) -> None:
    base_url = os.environ["LITELLM_BASE_URL"]
    master_key = os.environ["LITELLM_MASTER_KEY"]

    with TRACER.start_as_current_span("bootstrap_governance") as span:
        span.set_attribute("team_count", len(config.get("teams", [])))
        span.set_attribute("key_count", len(config.get("virtual_keys", [])))
        client = LiteLLMClient(base_url, master_key)
        wait_for_proxy(client)

        for team in config.get("teams", []):
            ensure_team(client, team)
        for group in config.get("access_groups", []):
            ensure_access_group(client, group)
        for key in config.get("virtual_keys", []):
            ensure_virtual_key(client, key)


def main() -> int:
    trace_id = str(uuid.uuid4())
    configure_logging(trace_id)
    configure_tracing()

    config_path = Path(os.environ.get("GOVERNANCE_CONFIG", "/config/governance.yaml"))
    if not config_path.is_file():
        LOG.error("Governance config not found: %s", config_path)
        return 1

    try:
        bootstrap(load_config(config_path))
    except Exception:
        LOG.exception("Bootstrap failed")
        return 1

    LOG.info("Bootstrap completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
