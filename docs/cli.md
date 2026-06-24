# CLI Reference

## Installation

```bash
pip install -e ".[dev]"
```

## Commands

### `flowindex init [path]`

Creates `.flowindex/` with `config.toml` and `flowindex.db`.

### `flowindex scan [path]`

Parses the repository, analyzes git history, and builds the behavior graph.

### `flowindex overview [path]`

Shows languages, top entrypoints, high-risk files, test count, and most connected files.

### `flowindex explain <target>`

Explains an API route, symbol, or file:

```bash
flowindex explain "POST /payments"
flowindex explain update_ledger
flowindex explain services/ledger.py
```

### `flowindex impact <target>`

Shows impact analysis and risk score for a file or symbol.

### `flowindex tests-for <target>`

Suggests tests to run based on naming, graph links, and git co-change history.

### `flowindex context "<task>"`

Generates a markdown context pack for an AI agent.

### `flowindex mcp`

Starts the MCP server (requires `pip install -e ".[mcp]"`).

## Configuration

`.flowindex/config.toml` controls included/excluded paths, supported languages, test directories, and git analysis limits.
