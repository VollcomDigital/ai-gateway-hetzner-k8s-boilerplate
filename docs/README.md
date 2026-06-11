# Documentation

| Document | Audience | Contents |
|----------|----------|----------|
| [README](../README.md) | Humans + operators | Architecture, layout, Flux sync, consumer onboarding |
| [AGENTS.md](../AGENTS.md) | Coding agents | Key paths, conventions, validation commands |
| [tasks/todo.md](../tasks/todo.md) | Platform team | Post-clone deploy checklist (Phases 0–5) |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Contributors | PR workflow, security, local CI |
| [SECURITY.md](../SECURITY.md) | Security reporters | Vulnerability disclosure |
| [agent-trace-context.md](agent-trace-context.md) | Agent builders | W3C trace propagation for n8n / MCP via LiteLLM |

## Related config (not prose docs)

| Path | Purpose |
|------|---------|
| `k8s/apps/litellm/base/config/` | Proxy config fragments + `proxy_server_config.yaml` |
| `k8s/mcp/registry.yaml` | MCP server registry (keep in sync with proxy config) |
| `k8s/observability/` | Alloy river snippet, Prometheus rules, Grafana dashboard JSON |
