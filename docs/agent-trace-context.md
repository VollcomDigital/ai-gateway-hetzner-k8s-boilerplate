# Agent trace context propagation

Orchestrators (n8n, LangGraph, custom agents) must propagate trace context into LiteLLM requests so a multi-step run appears as one trace in Tempo.

## Required headers

| Header | Purpose |
|--------|---------|
| `Authorization` | LiteLLM virtual key |
| `traceparent` | W3C trace context (OTel) |
| `x-litellm-agent-id` | Agent identity for MCP RBAC intersection |
| `x-litellm-end-user-id` | Engineer/end-user attribution |

## n8n HTTP Request node

Set custom headers on every LLM call:

```json
{
  "Authorization": "Bearer {{ $env.LITELLM_VIRTUAL_KEY }}",
  "traceparent": "{{ $json.traceparent }}",
  "x-litellm-agent-id": "n8n-wpml-translate",
  "x-litellm-end-user-id": "{{ $json.user_id }}"
}
```

Generate `traceparent` once per workflow run in a Function node and reuse across steps.

## MCP tool calls via LiteLLM

```json
{
  "type": "mcp",
  "server_label": "litellm",
  "server_url": "litellm_proxy",
  "require_approval": "never",
  "headers": {
    "x-litellm-api-key": "Bearer YOUR_VIRTUAL_KEY",
    "x-mcp-servers": "client-template-engagement",
    "traceparent": "00-TRACE_ID-SPAN_ID-01"
  }
}
```

## Run-level safety (orchestrator layer)

- Enforce `max_steps` and `max_spend_usd` per workflow run before calling the gateway.
- Gateway key budgets act as the backstop when the orchestrator fails.
- Alert on `litellm_spend_metric_total` velocity per team (see observability alerts).
