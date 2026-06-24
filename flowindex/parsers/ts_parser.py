"""TypeScript/JavaScript heuristic parser."""

from __future__ import annotations

import re
from pathlib import Path

from flowindex.frameworks.express import detect_express_routes
from flowindex.frameworks.nextjs import detect_nextjs_routes
from flowindex.indexer.tests import detect_js_tests
from flowindex.parsers.base import BaseParser
from flowindex.schemas import CallInfo, ImportInfo, ParseResult, SymbolInfo

IMPORT_RE = re.compile(
    r"""^import\s+(?:type\s+)?(?:\{[^}]+\}|\*\s+as\s+\w+|\w+)\s+from\s+['"]([^'"]+)['"]""",
    re.MULTILINE,
)
REQUIRE_RE = re.compile(r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)""")
FUNC_RE = re.compile(
    r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)",
    re.MULTILINE,
)
ARROW_RE = re.compile(
    r"(?:export\s+)?(?:const|let)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>",
    re.MULTILINE,
)
CLASS_RE = re.compile(r"(?:export\s+)?class\s+(\w+)", re.MULTILINE)
METHOD_RE = re.compile(
    r"(?:async\s+)?(\w+)\s*\([^)]*\)\s*(?::\s*[^{]+)?\{",
    re.MULTILINE,
)
CALL_RE = re.compile(r"(?<![.\w])(\w+)\s*\(", re.MULTILINE)


class TypeScriptParser(BaseParser):
    language = "typescript"

    def parse(self, path: Path, source: str) -> ParseResult:
        lines = source.splitlines()
        imports: list[ImportInfo] = []
        for i, line in enumerate(lines, 1):
            m = IMPORT_RE.match(line.strip())
            if m:
                imports.append(ImportInfo(module=m.group(1), line=i))
            for req in REQUIRE_RE.finditer(line):
                imports.append(ImportInfo(module=req.group(1), line=i))

        symbols: list[SymbolInfo] = []
        for m in FUNC_RE.finditer(source):
            name = m.group(1)
            start = source[: m.start()].count("\n") + 1
            end = self._find_block_end(lines, start)
            calls = self._extract_calls(source[m.start() : m.end() + 500])
            symbols.append(
                SymbolInfo(
                    name=name,
                    qualified_name=name,
                    symbol_type="function",
                    start_line=start,
                    end_line=end,
                    signature=f"{name}({m.group(2)})",
                    calls=calls,
                )
            )

        for m in ARROW_RE.finditer(source):
            name = m.group(1)
            start = source[: m.start()].count("\n") + 1
            symbols.append(
                SymbolInfo(
                    name=name,
                    qualified_name=name,
                    symbol_type="function",
                    start_line=start,
                    end_line=start + 20,
                    signature=f"{name}()",
                )
            )

        for m in CLASS_RE.finditer(source):
            name = m.group(1)
            start = source[: m.start()].count("\n") + 1
            symbols.append(
                SymbolInfo(
                    name=name,
                    qualified_name=name,
                    symbol_type="class",
                    start_line=start,
                    end_line=start + 50,
                )
            )

        routes = detect_express_routes(source, symbols)
        routes.extend(detect_nextjs_routes(path, source, symbols))
        tests = detect_js_tests(source, path)

        return ParseResult(imports=imports, symbols=symbols, routes=routes, tests=tests)

    def _find_block_end(self, lines: list[str], start: int) -> int:
        depth = 0
        started = False
        for i in range(start - 1, min(start + 200, len(lines))):
            depth += lines[i].count("{") - lines[i].count("}")
            if "{" in lines[i]:
                started = True
            if started and depth <= 0:
                return i + 1
        return min(start + 50, len(lines))

    def _extract_calls(self, chunk: str) -> list[CallInfo]:
        calls: list[CallInfo] = []
        reserved = {"if", "for", "while", "switch", "catch", "function", "return", "new"}
        for m in CALL_RE.finditer(chunk):
            name = m.group(1)
            if name in reserved:
                continue
            line = chunk[: m.start()].count("\n") + 1
            calls.append(CallInfo(callee=name, line=line))
        return calls[:30]
