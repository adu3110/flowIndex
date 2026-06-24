"""Overview command logic."""

from __future__ import annotations

from collections import Counter

from sqlmodel import Session, select

from flowindex.db.models import FileNode, SymbolNode, TestNode
from flowindex.indexer.entrypoints import list_entrypoints
from flowindex.indexer.graph import get_file_connection_counts


def build_overview(session: Session, repo_id: int) -> dict[str, object]:
    files = session.exec(select(FileNode).where(FileNode.repo_id == repo_id)).all()
    lang_counts = Counter(f.language for f in files)
    languages = ", ".join(f"{k}: {v}" for k, v in lang_counts.most_common())

    entrypoints = list_entrypoints(session, repo_id, limit=8)
    top_eps = [f"{ep.method} {ep.path} ({ep.framework})" for ep in entrypoints]

    test_count = len(session.exec(select(TestNode).where(TestNode.repo_id == repo_id)).all())
    symbol_count = len(session.exec(select(SymbolNode).where(SymbolNode.repo_id == repo_id)).all())

    connected = get_file_connection_counts(session, repo_id)
    most_connected = [f"{path} ({count} edges)" for path, count in connected[:5]]

    # High-risk: files in critical paths with many connections
    high_risk = []
    for path, count in connected:
        lower = path.lower()
        if any(k in lower for k in ("auth", "payment", "ledger", "webhook", "security")) and count >= 3:
            high_risk.append(f"{path} ({count} connections)")
    high_risk = high_risk[:5] or ["(none detected)"]

    return {
        "Languages": languages or "(none)",
        "Top entrypoints": top_eps or ["(none)"],
        "High-risk files": high_risk,
        "Test count": test_count,
        "Symbol count": symbol_count,
        "Most connected files": most_connected or ["(none)"],
        "Recently active areas": [f"{p} ({c} git touches)" for p, c in connected[:3]] or ["(run scan with git)"],
    }
