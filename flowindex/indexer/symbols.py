"""Symbol and entrypoint persistence."""

from __future__ import annotations

from sqlmodel import Session, select

from flowindex.db.models import EntrypointNode, SymbolNode, TestNode
from flowindex.schemas import RouteInfo, SymbolInfo, TestInfo


def store_symbols(
    session: Session,
    repo_id: int,
    file_id: int,
    symbols: list[SymbolInfo],
) -> dict[str, int]:
    mapping: dict[str, int] = {}
    for sym in symbols:
        node = SymbolNode(
            repo_id=repo_id,
            file_id=file_id,
            name=sym.name,
            qualified_name=sym.qualified_name,
            symbol_type=sym.symbol_type,
            start_line=sym.start_line,
            end_line=sym.end_line,
            signature=sym.signature,
            docstring=sym.docstring,
            visibility=sym.visibility,
        )
        session.add(node)
        session.flush()
        if node.id:
            mapping[sym.qualified_name] = node.id
    return mapping


def store_entrypoints(
    session: Session,
    repo_id: int,
    file_id: int,
    routes: list[RouteInfo],
    symbol_map: dict[str, int],
) -> list[EntrypointNode]:
    nodes: list[EntrypointNode] = []
    for route in routes:
        handler_id = _find_handler_symbol(route.handler_name, symbol_map)
        ep = EntrypointNode(
            repo_id=repo_id,
            file_id=file_id,
            symbol_id=handler_id,
            entrypoint_type="api_route",
            method=route.method,
            path=route.path,
            name=f"{route.method} {route.path}",
            framework=route.framework,
            start_line=route.start_line,
            end_line=route.end_line,
        )
        session.add(ep)
        session.flush()
        nodes.append(ep)
    return nodes


def store_tests(
    session: Session,
    repo_id: int,
    file_id: int,
    tests: list[TestInfo],
    symbol_map: dict[str, int],
) -> list[TestNode]:
    nodes: list[TestNode] = []
    for test in tests:
        sym_id = symbol_map.get(test.test_name)
        node = TestNode(
            repo_id=repo_id,
            file_id=file_id,
            symbol_id=sym_id,
            test_name=test.test_name,
            framework=test.framework,
            target_hint=test.target_hint,
            start_line=test.start_line,
            end_line=test.end_line,
        )
        session.add(node)
        session.flush()
        nodes.append(node)
    return nodes


def find_symbol_by_name(session: Session, repo_id: int, name: str) -> list[SymbolNode]:
    stmt = select(SymbolNode).where(SymbolNode.repo_id == repo_id)
    results = session.exec(stmt).all()
    name_lower = name.lower()
    return [
        s
        for s in results
        if name_lower in s.name.lower()
        or name_lower in s.qualified_name.lower()
        or name_lower in s.signature.lower()
    ]


def find_entrypoint(session: Session, repo_id: int, query: str) -> EntrypointNode | None:
    q = query.strip().upper()
    stmt = select(EntrypointNode).where(EntrypointNode.repo_id == repo_id)
    for ep in session.exec(stmt).all():
        label = f"{ep.method or ''} {ep.path or ''}".strip()
        if q == label.upper() or q in (ep.path or "").upper() or q in ep.name.upper():
            return ep
        if query.lower() in ep.name.lower() or query.lower() in (ep.path or "").lower():
            return ep
    return None


def _find_handler_symbol(handler_name: str, symbol_map: dict[str, int]) -> int | None:
    for qname, sid in symbol_map.items():
        if qname == handler_name or qname.endswith(f".{handler_name}") or qname.split(".")[-1] == handler_name:
            return sid
    return None
