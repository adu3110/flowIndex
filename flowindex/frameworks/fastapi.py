"""FastAPI route detection."""

from __future__ import annotations

import re

from flowindex.schemas import RouteInfo, SymbolInfo

FASTAPI_DECORATOR = re.compile(
    r"@(?:app|router)\.(get|post|put|patch|delete|options|head)\(\s*['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)


def detect_fastapi_routes(source: str, symbols: list[SymbolInfo]) -> list[RouteInfo]:
    lines = source.splitlines()
    routes: list[RouteInfo] = []
    symbol_by_line = {s.start_line: s for s in symbols}

    for i, line in enumerate(lines, 1):
        m = FASTAPI_DECORATOR.search(line)
        if not m:
            continue
        handler = _next_function_name(lines, i, symbol_by_line)
        routes.append(
            RouteInfo(
                method=m.group(1).upper(),
                path=m.group(2),
                handler_name=handler,
                framework="fastapi",
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
        if stripped.startswith("async def ") or stripped.startswith("def "):
            return stripped.split("(")[0].replace("async def ", "").replace("def ", "").strip()
    return "handler"
