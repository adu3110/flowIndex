"""Explain command logic."""

from __future__ import annotations

from sqlmodel import Session, select

from flowindex.db.models import EntrypointNode, FileNode, SymbolNode
from flowindex.indexer.graph import get_neighbors
from flowindex.indexer.impact import analyze_impact
from flowindex.indexer.symbols import find_entrypoint, find_symbol_by_name


def explain_target(session: Session, repo_id: int, query: str) -> dict[str, object]:
    ep = find_entrypoint(session, repo_id, query)
    if ep:
        return _explain_entrypoint(session, repo_id, ep, query)

    symbols = find_symbol_by_name(session, repo_id, query)
    if symbols:
        return _explain_symbol(session, repo_id, symbols[0], query)

    files = session.exec(select(FileNode).where(FileNode.repo_id == repo_id)).all()
    for f in files:
        if query in f.path:
            impact = analyze_impact(session, repo_id, f.path)
            return {
                "title": f.path,
                "entrypoint": None,
                "location": f.path,
                "execution_path": impact.downstream_symbols,
                "tests": impact.related_tests,
                "commits": impact.recent_commits,
                "risk_notes": impact.risk.factors,
            }

    return {"title": query, "risk_notes": ["No matching entrypoint, symbol, or file found."]}


def _explain_entrypoint(session: Session, repo_id: int, ep: EntrypointNode, query: str) -> dict[str, object]:
    title = f"{ep.method} {ep.path}"
    file_path = _file_path(session, ep.file_id)
    handler = ""
    if ep.symbol_id:
        sym = session.get(SymbolNode, ep.symbol_id)
        if sym:
            handler = f"{file_path}:{sym.start_line} {sym.signature or sym.name + '()'}"

    execution_path: list[str] = []
    if ep.symbol_id:
        execution_path.append(handler or "handler")
        for edge in get_neighbors(session, repo_id, "symbol", ep.symbol_id, "calls"):
            callee = session.get(SymbolNode, edge.target_id)
            if callee:
                execution_path.append(callee.signature or f"{callee.name}()")

    impact = analyze_impact(session, repo_id, file_path or query)
    return {
        "title": title.strip(),
        "entrypoint": handler or title,
        "location": file_path,
        "execution_path": execution_path,
        "tests": impact.related_tests,
        "commits": impact.recent_commits,
        "risk_notes": impact.risk.factors,
    }


def _explain_symbol(session: Session, repo_id: int, sym: SymbolNode, query: str) -> dict[str, object]:
    file_path = _file_path(session, sym.file_id)
    impact = analyze_impact(session, repo_id, sym.qualified_name)
    execution_path = [sym.signature or f"{sym.name}()", *impact.downstream_symbols]
    return {
        "title": sym.qualified_name,
        "entrypoint": sym.signature or sym.name,
        "location": f"{file_path}:{sym.start_line}",
        "execution_path": execution_path,
        "tests": impact.related_tests,
        "commits": impact.recent_commits,
        "risk_notes": impact.risk.factors,
    }


def _file_path(session: Session, file_id: int) -> str | None:
    node = session.get(FileNode, file_id)
    return node.path if node else None
