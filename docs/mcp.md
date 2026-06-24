# MCP Integration

FlowIndex exposes the same analysis engine through an MCP server for Cursor, Claude Code, and other MCP-compatible clients.

## Install

```bash
pip install -e ".[mcp]"
```

## Run

```bash
flowindex mcp
```

Ensure you have run `flowindex init` and `flowindex scan` in your target repository first.

## Tools

| MCP Tool | CLI Equivalent |
|----------|----------------|
| `get_repo_overview` | `flowindex overview` |
| `explain_entrypoint` | `flowindex explain` |
| `get_symbol_context` | `flowindex explain <symbol>` |
| `get_change_impact` | `flowindex impact` |
| `suggest_tests` | `flowindex tests-for` |
| `find_related_patches` | git-related subset of explain/impact |
| `make_context_pack` | `flowindex context` |

## Cursor configuration

Add to your MCP settings:

```json
{
  "mcpServers": {
    "flowindex": {
      "command": "flowindex",
      "args": ["mcp"],
      "cwd": "/path/to/your/repo"
    }
  }
}
```

Run `flowindex scan` in that repo before connecting the agent.
