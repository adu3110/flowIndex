"""Graph edge creation and queries."""

from __future__ import annotations

from sqlmodel import Session, select

from flowindex.db.models import FileNode, GraphEdge
from flowindex.schemas import CallInfo, ImportInfo, ParseResult


def add_edge(
    session: Session,
    repo_id: int,
    source_type: str,
    source_id: int,
    target_type: str,
    target_id: int,
    edge_type: str,
    weight: float = 1.0,
    evidence: str = "",
) -> GraphEdge:
    edge = GraphEdge(
        repo_id=repo_id,
        source_type=source_type,
        source_id=source_id,
        target_type=target_type,
        target_id=target_id,
        edge_type=edge_type,
        weight=weight,
        evidence=evidence,
    )
    session.add(edge)
    return edge


def build_file_graph(
    session: Session,
    repo_id: int,
    file_id: int,
    parse_result: ParseResult,
    symbol_map: dict[str, int],
    file_path_map: dict[str, int],
) -> int:
    """Create defines, imports, and call edges for a file. Returns edge count."""
    count = 0
    sym_by_name: dict[str, int] = {}
    sym_by_qname: dict[str, int] = {}

    for sym in parse_result.symbols:
        sym_id = symbol_map.get(sym.qualified_name)
        if sym_id:
            sym_by_name[sym.name] = sym_id
            sym_by_qname[sym.qualified_name] = sym_id
            add_edge(session, repo_id, "file", file_id, "symbol", sym_id, "defines", evidence=sym.name)
            count += 1

    # Build a set of symbols that are explicitly imported into this file.
    # This enables cross-file call resolution: if a file imports `charge` from
    # `ledger`, calls to `charge()` can be matched against the global symbol_map
    # even though `charge` is not defined locally.
    imported_symbols: dict[str, int] = {}
    for imp in parse_result.imports:
        target_file = _resolve_import(imp, file_path_map)
        if target_file:
            add_edge(
                session,
                repo_id,
                "file",
                file_id,
                "file",
                target_file,
                "imports",
                evidence=imp.module,
            )
            count += 1
        # Index each named import so _resolve_call can find cross-file symbols
        for name in imp.names:
            for qname, sid in symbol_map.items():
                if qname == name or qname.endswith(f".{name}"):
                    imported_symbols[name] = sid
                    imported_symbols[qname] = sid

    for sym in parse_result.symbols:
        sym_id = sym_by_qname.get(sym.qualified_name)
        if not sym_id:
            continue
        for call in sym.calls:
            target_sym = _resolve_call(call, sym_by_name, sym_by_qname, symbol_map, imported_symbols)
            if target_sym:
                add_edge(
                    session,
                    repo_id,
                    "symbol",
                    sym_id,
                    "symbol",
                    target_sym,
                    "calls",
                    evidence=call.callee,
                )
                count += 1

    return count


def link_entrypoints(
    session: Session,
    repo_id: int,
    entrypoint_id: int,
    handler_symbol_id: int | None,
    file_id: int,
) -> int:
    count = 0
    add_edge(session, repo_id, "file", file_id, "entrypoint", entrypoint_id, "exposes")
    count += 1
    if handler_symbol_id:
        add_edge(
            session,
            repo_id,
            "entrypoint",
            entrypoint_id,
            "symbol",
            handler_symbol_id,
            "handled_by",
        )
        count += 1
    return count


def link_tests(
    session: Session,
    repo_id: int,
    test_id: int,
    file_id: int,
    target_symbol_id: int | None = None,
) -> int:
    add_edge(session, repo_id, "file", file_id, "test", test_id, "defines")
    if target_symbol_id:
        add_edge(session, repo_id, "test", test_id, "symbol", target_symbol_id, "covers")
        return 2
    return 1


def get_neighbors(
    session: Session,
    repo_id: int,
    node_type: str,
    node_id: int,
    edge_type: str | None = None,
    direction: str = "out",
) -> list[GraphEdge]:
    stmt = select(GraphEdge).where(GraphEdge.repo_id == repo_id)
    if direction == "out":
        stmt = stmt.where(GraphEdge.source_type == node_type, GraphEdge.source_id == node_id)
    else:
        stmt = stmt.where(GraphEdge.target_type == node_type, GraphEdge.target_id == node_id)
    if edge_type:
        stmt = stmt.where(GraphEdge.edge_type == edge_type)
    return list(session.exec(stmt).all())


def get_file_connection_counts(session: Session, repo_id: int) -> list[tuple[str, int]]:
    files = session.exec(select(FileNode).where(FileNode.repo_id == repo_id)).all()
    counts: dict[int, int] = {}
    edges = session.exec(select(GraphEdge).where(GraphEdge.repo_id == repo_id)).all()
    for edge in edges:
        if edge.source_type == "file":
            counts[edge.source_id] = counts.get(edge.source_id, 0) + 1
        if edge.target_type == "file":
            counts[edge.target_id] = counts.get(edge.target_id, 0) + 1
    id_to_path = {f.id: f.path for f in files if f.id}
    ranked = sorted(((id_to_path[fid], c) for fid, c in counts.items()), key=lambda x: -x[1])
    return ranked[:10]


def _resolve_import(imp: ImportInfo, file_path_map: dict[str, int]) -> int | None:
    module = imp.module.replace(".", "/")
    candidates = [
        f"{module}.py",
        f"{module}/__init__.py",
        f"{module}.ts",
        f"{module}.js",
        f"src/{module}.py",
        f"src/{module}.ts",
    ]
    for c in candidates:
        if c in file_path_map:
            return file_path_map[c]
    for path, fid in file_path_map.items():
        if module in path:
            return fid
    return None


def _resolve_call(
    call: CallInfo,
    sym_by_name: dict[str, int],
    sym_by_qname: dict[str, int],
    all_symbols: dict[str, int],
    imported_symbols: dict[str, int] | None = None,
) -> int | None:
    # 1. Same-file exact name match
    if call.callee in sym_by_name:
        return sym_by_name[call.callee]
    # 2. Same-file qualified name match
    if call.callee in sym_by_qname:
        return sym_by_qname[call.callee]
    # 3. Strip obj.method() → method, try local lookup
    base = call.callee.split(".")[-1]
    if base in sym_by_name:
        return sym_by_name[base]
    # 4. Cross-file: check symbols that were explicitly imported into this file
    if imported_symbols:
        if call.callee in imported_symbols:
            return imported_symbols[call.callee]
        if base in imported_symbols:
            return imported_symbols[base]
    # 5. Repo-wide fallback by base name (lower precision, last resort)
    if base in all_symbols:
        return all_symbols[base]
    return None
