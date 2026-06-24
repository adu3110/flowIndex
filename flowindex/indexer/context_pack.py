"""Context pack generation for AI agents."""

from __future__ import annotations

import re

from sqlmodel import Session, select

from flowindex.db.models import CommitNode, EntrypointNode, FileNode, SymbolNode, TestNode
from flowindex.indexer.impact import analyze_impact, suggest_tests
from flowindex.schemas import ContextPack


def make_context_pack(session: Session, repo_id: int, task: str) -> ContextPack:
    keywords = _extract_keywords(task)
    entrypoints = _rank_entrypoints(session, repo_id, keywords)
    files = _rank_files(session, repo_id, keywords)
    symbols = _rank_symbols(session, repo_id, keywords)
    tests = _rank_tests(session, repo_id, keywords, files, symbols)
    commits = _rank_commits(session, repo_id, keywords)
    cautions = _build_cautions(session, repo_id, files, symbols)
    instructions = _build_instructions(entrypoints, files, symbols, tests)

    return ContextPack(
        task=task,
        entrypoints=entrypoints[:5],
        files=files[:8],
        symbols=symbols[:8],
        tests=tests[:8],
        commits=commits[:5],
        cautions=cautions[:5],
        instructions=instructions[:8],
    )


def _extract_keywords(task: str) -> list[str]:
    stop = {
        "a", "an", "the", "and", "or", "to", "for", "when", "fix", "add", "update",
        "change", "implement", "handle", "with", "in", "on", "of", "is", "are",
    }
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]*", task.lower())
    return [w for w in words if w not in stop and len(w) > 2]


def _score_text(text: str, keywords: list[str]) -> float:
    text_lower = text.lower()
    return sum(1.0 for kw in keywords if kw in text_lower)


def _rank_entrypoints(session: Session, repo_id: int, keywords: list[str]) -> list[str]:
    eps = session.exec(select(EntrypointNode).where(EntrypointNode.repo_id == repo_id)).all()
    scored: list[tuple[float, str]] = []
    for ep in eps:
        label = f"{ep.method} {ep.path}"
        score = _score_text(label, keywords) + _score_text(ep.name, keywords)
        if score:
            scored.append((score, label.strip()))
    scored.sort(key=lambda x: -x[0])
    return [s for _, s in scored]


def _rank_files(session: Session, repo_id: int, keywords: list[str]) -> list[str]:
    files = session.exec(select(FileNode).where(FileNode.repo_id == repo_id)).all()
    scored: list[tuple[float, str]] = []
    for f in files:
        score = _score_text(f.path, keywords)
        if score:
            scored.append((score, f.path))
    scored.sort(key=lambda x: -x[0])
    return [s for _, s in scored]


def _rank_symbols(session: Session, repo_id: int, keywords: list[str]) -> list[str]:
    symbols = session.exec(select(SymbolNode).where(SymbolNode.repo_id == repo_id)).all()
    scored: list[tuple[float, str]] = []
    for s in symbols:
        score = _score_text(s.qualified_name, keywords) + _score_text(s.docstring, keywords)
        if score:
            label = s.signature or f"{s.qualified_name}()"
            scored.append((score, label))
    scored.sort(key=lambda x: -x[0])
    return [s for _, s in scored]


def _rank_tests(
    session: Session,
    repo_id: int,
    keywords: list[str],
    files: list[str],
    symbols: list[str],
) -> list[str]:
    tests = session.exec(select(TestNode).where(TestNode.repo_id == repo_id)).all()
    scored: list[tuple[float, str]] = []
    file_ids = {f.id: f.path for f in session.exec(select(FileNode).where(FileNode.repo_id == repo_id)).all() if f.id}

    for t in tests:
        path = file_ids.get(t.file_id, t.test_name)
        score = _score_text(t.test_name, keywords) + _score_text(path, keywords)
        if any(kw in path.lower() for kw in keywords):
            score += 0.5
        if score:
            scored.append((score, path))
    scored.sort(key=lambda x: -x[0])

    # Boost tests from impact of top file
    if files:
        extra = suggest_tests(session, repo_id, files[0])
        result = [s for _, s in scored]
        for test_path in extra:
            if test_path not in result:
                result.append(test_path)
        return list(dict.fromkeys(result))[:8]
    return list(dict.fromkeys(s for _, s in scored))[:8]


def _rank_commits(session: Session, repo_id: int, keywords: list[str]) -> list[str]:
    commits = session.exec(select(CommitNode).where(CommitNode.repo_id == repo_id)).all()
    scored: list[tuple[float, str]] = []
    for c in commits:
        score = _score_text(c.message, keywords)
        if score:
            scored.append((score, f"{c.commit_hash[:7]} {c.message[:60]}"))
    scored.sort(key=lambda x: -x[0])
    return [s for _, s in scored]


def _build_cautions(
    session: Session,
    repo_id: int,
    files: list[str],
    symbols: list[str],
) -> list[str]:
    cautions: list[str] = []
    for f in files[:3]:
        impact = analyze_impact(session, repo_id, f)
        if impact.risk.level in {"medium", "high"}:
            cautions.append(f"{f} has {impact.risk.level} change risk ({impact.risk.score}).")
        for ep in impact.entrypoints_affected[:2]:
            cautions.append(f"{f} connects to entrypoint {ep}.")
    for sym in symbols[:2]:
        impact = analyze_impact(session, repo_id, sym.replace("()", ""))
        if len(impact.upstream_callers) > 2:
            cautions.append(f"{sym} is shared by multiple callers.")
    return cautions


def _build_instructions(
    entrypoints: list[str],
    files: list[str],
    symbols: list[str],
    tests: list[str],
) -> list[str]:
    instructions: list[str] = []
    for ep in entrypoints[:2]:
        instructions.append(f"entrypoint: {ep}")
    for f in files[:3]:
        instructions.append(f"file: {f}")
    for s in symbols[:3]:
        instructions.append(f"symbol: {s}")
    if tests:
        instructions.append(f"run tests: {', '.join(tests[:3])}")
    instructions.append("review git history for related bug fixes before editing shared modules")
    return instructions
