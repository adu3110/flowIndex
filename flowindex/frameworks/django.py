"""Django view detection (heuristic)."""

from __future__ import annotations

import re

from flowindex.schemas import RouteInfo, SymbolInfo

PATH_DECORATOR = re.compile(r"@(?:path|re_path)\(\s*['\"]([^'\"]+)['\"]")


def detect_django_views(source: str, symbols: list[SymbolInfo]) -> list[RouteInfo]:
    lines = source.splitlines()
    routes: list[RouteInfo] = []
    symbol_by_line = {s.start_line: s for s in symbols}

    for i, line in enumerate(lines, 1):
        m = PATH_DECORATOR.search(line)
        if not m:
            continue
        handler = _next_function_name(lines, i, symbol_by_line)
        routes.append(
            RouteInfo(
                method="GET",
                path=m.group(1),
                handler_name=handler,
                framework="django",
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
    return "view"
