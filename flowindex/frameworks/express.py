"""Express route detection."""

from __future__ import annotations

import re

from flowindex.schemas import RouteInfo, SymbolInfo

EXPRESS_ROUTE = re.compile(
    r"(?:app|router)\.(get|post|put|patch|delete|options|head)\(\s*['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)


def detect_express_routes(source: str, symbols: list[SymbolInfo]) -> list[RouteInfo]:
    routes: list[RouteInfo] = []
    for m in EXPRESS_ROUTE.finditer(source):
        start = source[: m.start()].count("\n") + 1
        handler = _handler_near(source, m.end())
        routes.append(
            RouteInfo(
                method=m.group(1).upper(),
                path=m.group(2),
                handler_name=handler,
                framework="express",
                start_line=start,
                end_line=start,
            )
        )
    return routes


def _handler_near(source: str, pos: int) -> str:
    chunk = source[pos : pos + 200]
    fn = re.search(r"(?:async\s+)?function\s+(\w+)", chunk)
    if fn:
        return fn.group(1)
    arrow = re.search(r"(?:const|let)\s+(\w+)\s*=", chunk)
    if arrow:
        return arrow.group(1)
    sym = re.search(r",\s*(\w+)\s*\)", chunk)
    if sym:
        return sym.group(1)
    return "handler"
