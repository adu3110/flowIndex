"""Flask route detection."""

from __future__ import annotations

import re

from flowindex.schemas import RouteInfo, SymbolInfo

FLASK_ROUTE = re.compile(
    r"@(?:app|bp|blueprint)\.route\(\s*['\"]([^'\"]+)['\"](?:,\s*methods\s*=\s*\[([^\]]+)\])?",
    re.IGNORECASE,
)


def detect_flask_routes(source: str, symbols: list[SymbolInfo]) -> list[RouteInfo]:
    lines = source.splitlines()
    routes: list[RouteInfo] = []
    symbol_by_line = {s.start_line: s for s in symbols}

    for i, line in enumerate(lines, 1):
        m = FLASK_ROUTE.search(line)
        if not m:
            continue
        path = m.group(1)
        methods_raw = m.group(2) or "'GET'"
        methods = [x.strip().strip("'\"").upper() for x in methods_raw.split(",")]
        handler = _next_function_name(lines, i, symbol_by_line)
        for method in methods:
            routes.append(
                RouteInfo(
                    method=method,
                    path=path,
                    handler_name=handler,
                    framework="flask",
                    start_line=i,
                    end_line=i,
                )
            )
    return routes


def _next_function_name(lines: list[str], decor_line: int, symbols: dict[int, SymbolInfo]) -> str:
    for j in range(decor_line, min(decor_line + 5, len(lines))):
        sym = symbols.get(j + 1)
        if sym:
            return sym.name
        stripped = lines[j].strip()
        if stripped.startswith("def "):
            return stripped.split("(")[0].replace("def ", "").strip()
    return "handler"
