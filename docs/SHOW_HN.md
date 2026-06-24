# Show HN post (draft)

**Title:** Show HN: FlowIndex – behavior-first repo indexing for AI coding agents

**URL:** https://github.com/adu3110/flowIndex

---

Most AI coding tools index files, chunks, symbols, or embeddings.

FlowIndex indexes **behavior**: entrypoints, call paths, tests, git co-change history, and patch impact — stored locally in SQLite. No LLM calls. No vector DB.

It answers questions like:

- What code path handles this feature?
- What breaks if I change this function?
- Which tests should I run for this patch?
- What minimal context should an agent get before editing?

```bash
pip install flowindex
cd your-repo
flowindex init
flowindex scan
flowindex context "fix duplicate payments when webhook retries"
```

That last command returns a markdown context pack: relevant entrypoints, files, symbols, tests, cautions, and suggested agent instructions — ranked deterministically from the behavior graph.

Also ships an MCP server for Cursor / Claude Code:

```bash
pip install "flowindex[mcp]"
flowindex mcp
```

Built this because I kept watching agents grep random files or pull embedding chunks that miss the webhook handler, shared ledger module, and the integration test that actually covers retries.

Alpha / dev tool / local-first. Python + TS/JS static analysis today. Would love feedback on what would make this useful in your workflow.

GitHub: https://github.com/adu3110/flowIndex

---

## Posting tips

- Post between **9–11am PT**, Tuesday–Thursday
- Put the **GitHub link** as the URL (not your personal site)
- First comment: link to demo output or GIF, MCP Cursor config, and note `--here` for nested repos
- Reply to every comment in the first 2 hours
