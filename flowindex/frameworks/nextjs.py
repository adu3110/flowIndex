"""Next.js route/page detection."""

from __future__ import annotations

import re
from pathlib import Path

from flowindex.schemas import RouteInfo, SymbolInfo


def detect_nextjs_routes(path: Path, source: str, symbols: list[SymbolInfo]) -> list[RouteInfo]:
    routes: list[RouteInfo] = []
    rel = path.as_posix()

    if "/app/" in rel and (rel.endswith("route.ts") or rel.endswith("route.js")):
        route_path = _app_route_path(rel)
        for method in _exported_methods(source):
            routes.append(
                RouteInfo(
                    method=method,
                    path=route_path,
                    handler_name=f"{method} handler",
                    framework="nextjs",
                    start_line=1,
                    end_line=len(source.splitlines()),
                )
            )

    if "/pages/" in rel and not path.name.startswith("_"):
        page_path = _pages_route_path(rel)
        routes.append(
            RouteInfo(
                method="GET",
                path=page_path,
                handler_name=path.stem,
                framework="nextjs",
                start_line=1,
                end_line=len(source.splitlines()),
            )
        )

    return routes


def _app_route_path(rel: str) -> str:
    part = rel.split("/app/", 1)[-1]
    part = re.sub(r"/route\.(ts|js|tsx|jsx)$", "", part)
    if not part:
        return "/"
    segments = [s for s in part.split("/") if not s.startswith("(")]
    return "/" + "/".join(segments)


def _pages_route_path(rel: str) -> str:
    part = rel.split("/pages/", 1)[-1]
    part = re.sub(r"\.(tsx|ts|js|jsx)$", "", part)
    if part.endswith("/index"):
        part = part[: -len("/index")] or "index"
    if part == "index":
        return "/"
    return "/" + part


def _exported_methods(source: str) -> list[str]:
    methods = []
    for m in re.finditer(r"export\s+(?:async\s+)?function\s+(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\b", source):
        methods.append(m.group(1).upper())
    return methods or ["GET"]
