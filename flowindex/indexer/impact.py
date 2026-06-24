"""Impact analysis."""

from __future__ import annotations

from sqlmodel import Session, select

from flowindex.db.models import (
    CRITICAL_PATH_KEYWORDS,
    EntrypointNode,
    FileNode,
    GraphEdge,
    SymbolNode,
    TestNode,
)
from flowindex.indexer.git_history import commits_for_file
from flowindex.indexer.graph import get_neighbors
from flowindex.schemas import ImpactResult, RiskBreakdown


def analyze_impact(session: Session, repo_id: int, target: str) -> ImpactResult:
    file_node, symbol_node = _resolve_target(session, repo_id, target)

    if symbol_node:
        return _impact_symbol(session, repo_id, symbol_node, target)
    if file_node:
        return _impact_file(session, repo_id, file_node, target)
    return ImpactResult(
        target=target,
        entrypoints_affected=[],
        downstream_symbols=[],
        upstream_callers=[],
        related_tests=[],
        changed_together_files=[],
        recent_commits=[],
        risk=RiskBreakdown(score=0, level="low", factors=["Target not found in index"]),
    )


def suggest_tests(session: Session, repo_id: int, target: str) -> list[str]:
    """Suggest tests for a target file or symbol.

    Sources (applied in priority order):
    1. Tests directly linked via graph ``covers`` edges
    2. Tests in files that import the target file (transitive relevance)
    3. Keyword / name / target_hint matching against all stored test nodes
    """
    impact = analyze_impact(session, repo_id, target)
    tests = set(impact.related_tests)

    file_node, symbol_node = _resolve_target(session, repo_id, target)
    keyword = (symbol_node.name if symbol_node else _path_stem(file_node.path if file_node else target)).lower()

    # Source 2: find test files that import the target file via graph edges
    if file_node and file_node.id:
        import_edges = session.exec(
            select(GraphEdge).where(
                GraphEdge.repo_id == repo_id,
                GraphEdge.edge_type == "imports",
                GraphEdge.target_id == file_node.id,
            )
        ).all()
        importing_file_ids = {e.source_id for e in import_edges}
        if importing_file_ids:
            for tn in session.exec(select(TestNode).where(TestNode.repo_id == repo_id)).all():
                if tn.file_id in importing_file_ids:
                    path = _file_path(session, tn.file_id) or tn.test_name
                    tests.add(path)

    # Source 3: keyword / name / target_hint matching (original heuristic)
    all_tests = session.exec(select(TestNode).where(TestNode.repo_id == repo_id)).all()
    for test_node in all_tests:
        file_path = _file_path(session, test_node.file_id) or test_node.test_name
        if keyword and keyword in file_path.lower():
            tests.add(file_path)
        if keyword and keyword in test_node.test_name.lower():
            tests.add(file_path)
        if test_node.target_hint and keyword in test_node.target_hint:
            tests.add(file_path)

    return sorted(tests)[:15]


def _path_stem(path: str) -> str:
    from pathlib import Path

    return Path(path).stem


def _resolve_target(
    session: Session, repo_id: int, target: str
) -> tuple[FileNode | None, SymbolNode | None]:
    files = session.exec(select(FileNode).where(FileNode.repo_id == repo_id)).all()
    for f in files:
        if target in f.path or f.path.endswith(target):
            return f, None

    symbols = session.exec(select(SymbolNode).where(SymbolNode.repo_id == repo_id)).all()
    t_lower = target.lower()
    for s in symbols:
        if t_lower in s.name.lower() or t_lower in s.qualified_name.lower():
            return None, s
    return None, None


def _impact_file(session: Session, repo_id: int, file_node: FileNode, target: str) -> ImpactResult:
    assert file_node.id
    entrypoints: set[str] = set()
    downstream: set[str] = set()
    upstream: set[str] = set()
    tests: set[str] = set()
    changed_with: set[str] = set()

    symbols = session.exec(
        select(SymbolNode).where(SymbolNode.repo_id == repo_id, SymbolNode.file_id == file_node.id)
    ).all()
    for sym in symbols:
        sub = _impact_symbol(session, repo_id, sym, sym.qualified_name, include_risk=False)
        entrypoints.update(sub.entrypoints_affected)
        downstream.update(sub.downstream_symbols)
        upstream.update(sub.upstream_callers)
        tests.update(sub.related_tests)

    for edge in get_neighbors(session, repo_id, "file", file_node.id, "changed_with"):
        other_id = edge.target_id if edge.source_id == file_node.id else edge.source_id
        path = _file_path(session, other_id)
        if path:
            changed_with.add(path)

    for edge in get_neighbors(session, repo_id, "file", file_node.id, "changed_with", direction="in"):
        path = _file_path(session, edge.source_id)
        if path:
            changed_with.add(path)

    recent = commits_for_file(session, repo_id, file_node.path)
    risk = _compute_risk(
        file_node.path,
        len(entrypoints),
        len(upstream),
        len(downstream),
        len(changed_with),
        len(recent),
    )
    return ImpactResult(
        target=target,
        entrypoints_affected=sorted(entrypoints),
        downstream_symbols=sorted(downstream)[:20],
        upstream_callers=sorted(upstream)[:20],
        related_tests=sorted(tests)[:15],
        changed_together_files=sorted(changed_with)[:10],
        recent_commits=recent,
        risk=risk,
    )


def _impact_symbol(
    session: Session,
    repo_id: int,
    symbol_node: SymbolNode,
    target: str,
    include_risk: bool = True,
) -> ImpactResult:
    assert symbol_node.id
    entrypoints: set[str] = set()
    downstream: set[str] = set()
    upstream: set[str] = set()
    tests: set[str] = set()
    changed_with: set[str] = set()

    for edge in _walk_calls(session, repo_id, symbol_node.id, depth=3):
        callee = session.get(SymbolNode, edge.target_id)
        if callee:
            downstream.add(callee.qualified_name)

    for edge in get_neighbors(session, repo_id, "symbol", symbol_node.id, "calls", direction="in"):
        caller = session.get(SymbolNode, edge.source_id)
        if caller:
            upstream.add(caller.qualified_name)

    eps = session.exec(select(EntrypointNode).where(EntrypointNode.repo_id == repo_id)).all()
    for ep in eps:
        if ep.symbol_id == symbol_node.id:
            entrypoints.add(f"{ep.method} {ep.path}")

    for edge in get_neighbors(session, repo_id, "symbol", symbol_node.id, "covers", direction="in"):
        test = session.get(TestNode, edge.source_id)
        if test:
            tests.add(_file_path(session, test.file_id) or test.test_name)

    file_path = _file_path(session, symbol_node.file_id) or target
    recent = commits_for_file(session, repo_id, file_path)

    for edge in get_neighbors(session, repo_id, "file", symbol_node.file_id, "changed_with"):
        other_id = edge.target_id if edge.source_id == symbol_node.file_id else edge.source_id
        path = _file_path(session, other_id)
        if path:
            changed_with.add(path)

    risk = (
        _compute_risk(file_path, len(entrypoints), len(upstream), len(downstream), len(changed_with), len(recent))
        if include_risk
        else RiskBreakdown(score=0, level="low", factors=[])
    )
    return ImpactResult(
        target=target,
        entrypoints_affected=sorted(entrypoints),
        downstream_symbols=sorted(downstream)[:20],
        upstream_callers=sorted(upstream)[:20],
        related_tests=sorted(tests)[:15],
        changed_together_files=sorted(changed_with)[:10],
        recent_commits=recent,
        risk=risk,
    )


def _walk_calls(session: Session, repo_id: int, symbol_id: int, depth: int) -> list[GraphEdge]:
    if depth <= 0:
        return []
    edges = get_neighbors(session, repo_id, "symbol", symbol_id, "calls")
    collected = list(edges)
    for edge in edges:
        collected.extend(_walk_calls(session, repo_id, edge.target_id, depth - 1))
    return collected


def _compute_risk(
    file_path: str,
    entrypoints: int,
    upstream: int,
    downstream: int,
    changed_with: int,
    bugfix_commits: int,
) -> RiskBreakdown:
    score = 0
    factors: list[str] = []
    score += 2 * entrypoints
    if entrypoints:
        factors.append(f"{entrypoints} connected entrypoint(s) (+{2 * entrypoints})")
    score += upstream
    if upstream:
        factors.append(f"{upstream} upstream caller(s) (+{upstream})")
    score += downstream
    if downstream:
        factors.append(f"{downstream} downstream call(s) (+{downstream})")
    score += 2 * changed_with
    if changed_with:
        factors.append(f"{changed_with} frequently co-changed file(s) (+{2 * changed_with})")
    path_lower = file_path.lower()
    if any(kw in path_lower for kw in CRITICAL_PATH_KEYWORDS):
        score += 3
        factors.append("file in critical path (+3)")
    if bugfix_commits:
        score += 2
        factors.append(f"{bugfix_commits} related bug-fix commit(s) (+2)")

    if score >= 12:
        level = "high"
    elif score >= 6:
        level = "medium"
    else:
        level = "low"
    return RiskBreakdown(score=score, level=level, factors=factors or ["No significant risk factors"])


def _file_path(session: Session, file_id: int | None) -> str | None:
    if not file_id:
        return None
    node = session.get(FileNode, file_id)
    return node.path if node else None
