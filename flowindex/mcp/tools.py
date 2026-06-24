"""MCP tool implementations."""

from __future__ import annotations

from typing import Any

from sqlmodel import Session, select

from flowindex.config import FlowIndexConfig
from flowindex.db.models import Repository
from flowindex.db.session import get_session
from flowindex.indexer.context_pack import make_context_pack
from flowindex.indexer.explain import explain_target
from flowindex.indexer.impact import analyze_impact, suggest_tests
from flowindex.indexer.overview import build_overview
from flowindex.render.markdown import render_context_pack, render_explain


def _repo_session(config: FlowIndexConfig) -> tuple[Session, int, Any]:
    session_ctx = get_session(config.db_path)
    session = session_ctx.__enter__()
    repo = session.exec(
        select(Repository).where(Repository.root_path == str(config.root_path.resolve()))
    ).first()
    if not repo or not repo.id:
        raise RuntimeError("No indexed repository. Run `flowindex scan` first.")
    return session, repo.id, session_ctx


def get_repo_overview(config: FlowIndexConfig) -> str:
    session, repo_id, ctx = _repo_session(config)
    try:
        data = build_overview(session, repo_id)
        lines = ["# FlowIndex Repository Overview", ""]
        for k, v in data.items():
            lines.append(f"## {k}")
            if isinstance(v, list):
                lines.extend(f"- {item}" for item in v)
            else:
                lines.append(str(v))
            lines.append("")
        return "\n".join(lines)
    finally:
        ctx.__exit__(None, None, None)


def explain_entrypoint(config: FlowIndexConfig, query: str) -> str:
    session, repo_id, ctx = _repo_session(config)
    try:
        return render_explain(explain_target(session, repo_id, query))
    finally:
        ctx.__exit__(None, None, None)


def get_symbol_context(config: FlowIndexConfig, symbol: str) -> str:
    return explain_entrypoint(config, symbol)


def get_change_impact(config: FlowIndexConfig, target: str) -> str:
    session, repo_id, ctx = _repo_session(config)
    try:
        result = analyze_impact(session, repo_id, target)
        lines = [
            f"# Impact: {result.target}",
            f"Risk: {result.risk.level} ({result.risk.score})",
            "",
            "## Factors",
            *[f"- {f}" for f in result.risk.factors],
            "",
            "## Entrypoints",
            *[f"- {e}" for e in result.entrypoints_affected],
            "",
            "## Tests",
            *[f"- {t}" for t in result.related_tests],
        ]
        return "\n".join(lines)
    finally:
        ctx.__exit__(None, None, None)


def suggest_tests_tool(config: FlowIndexConfig, target: str) -> str:
    session, repo_id, ctx = _repo_session(config)
    try:
        tests = suggest_tests(session, repo_id, target)
        return "\n".join(tests) if tests else "No tests found."
    finally:
        ctx.__exit__(None, None, None)


def find_related_patches(config: FlowIndexConfig, query: str) -> str:
    session, repo_id, ctx = _repo_session(config)
    try:
        from flowindex.indexer.git_history import commits_for_file
        commits = commits_for_file(session, repo_id, query, limit=15)
        return "\n".join(commits) if commits else "No related commits found."
    finally:
        ctx.__exit__(None, None, None)


def make_context_pack_tool(config: FlowIndexConfig, task: str) -> str:
    session, repo_id, ctx = _repo_session(config)
    try:
        pack = make_context_pack(session, repo_id, task)
        return render_context_pack(pack)
    finally:
        ctx.__exit__(None, None, None)
