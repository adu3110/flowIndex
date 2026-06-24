# Concepts

## Behavior-first indexing

Most coding tools index **what exists** in a repository: files, chunks, symbols, embeddings. FlowIndex indexes **how the repository behaves**:

- Where requests enter (API routes, CLI commands, pages)
- Which functions call which other functions
- Which tests cover which behavior
- Which files change together in git history
- Which areas carry higher change risk

The result is a **deterministic, inspectable behavior graph** stored locally in SQLite.

## Graph nodes

| Node type | Examples |
|-----------|----------|
| File | `src/services/ledger.py` |
| Symbol | `update_ledger()`, `PaymentService` |
| Entrypoint | `POST /api/payments` |
| Test | `test_webhook_retry_updates_ledger` |
| Commit | `a13f9c fixed duplicate ledger entry` |

## Graph edges

| Edge | Meaning |
|------|---------|
| `defines` | File defines symbol |
| `imports` | File imports another file/module |
| `calls` | Symbol calls symbol |
| `exposes` | File exposes entrypoint |
| `handled_by` | Entrypoint handled by symbol |
| `tests` / `covers` | Test references symbol |
| `changed_with` | Files frequently co-changed in git |

## Entrypoints

Entrypoints are externally observable behavior boundaries: HTTP routes, webhooks, CLI commands, cron jobs, pages. FlowIndex detects common framework patterns (FastAPI, Flask, Express, Next.js) and links them to handler symbols.

## Impact analysis

Given a file or symbol, FlowIndex walks the graph to find:

- Connected entrypoints
- Upstream callers and downstream callees
- Related tests
- Co-changed files
- Recent bug-fix commits

It computes an **explainable risk score** from transparent factors (caller count, entrypoint connectivity, critical directories, git churn).

## Context packs

Context packs assemble the minimal relevant subgraph for a natural-language task. FlowIndex ranks candidates using lexical matching, graph proximity, and git history — **without calling an LLM**.
