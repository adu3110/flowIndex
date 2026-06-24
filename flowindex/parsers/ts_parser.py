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
# Extended: also captures the named-import block so we can extract individual names
IMPORT_NAMED_RE = re.compile(
    r"""^import\s+(?:type\s+)?(?:(\{[^}]+\})|(?:\*\s+as\s+\w+|\w+))(?:\s*,\s*(\{[^}]+\}))?"""
    r"""\s+from\s+['"]([^'"]+)['"]""",
    re.MULTILINE,
)
REQUIRE_RE = re.compile(r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)""")
# Extended: also captures destructured require: const { a, b } = require('...')
REQUIRE_NAMED_RE = re.compile(
    r"""(?:const|let|var)\s+(?:\{([^}]+)\}|(\w+))\s*=\s*require\s*\(\s*['"]([^'"]+)['"]\s*\)"""
)
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
# Extended: class methods with optional access modifiers and static/async
CLASS_METHOD_RE = re.compile(
    r"^\s*(?:(?:public|private|protected|static|async|override|readonly)\s+)*(\w+)\s*\(([^)]*)\)\s*(?::\s*[^{;]+)?\{",
    re.MULTILINE,
)
CALL_RE = re.compile(r"(?<![.\w])(\w+)\s*\(", re.MULTILINE)
# Extended: also match qualified obj.method() calls
QUALIFIED_CALL_RE = re.compile(r"(?<!\w)(\w+)\.(\w+)\s*\(", re.MULTILINE)

_JS_RESERVED = {
    "if", "for", "while", "switch", "catch", "function", "return", "new",
    "typeof", "instanceof", "delete", "void", "throw", "await", "yield",
    "super", "constructor", "class", "import", "export", "const", "let", "var",
}


class TypeScriptParser(BaseParser):
    language = "typescript"

    def parse(self, path: Path, source: str) -> ParseResult:
        lines = source.splitlines()

        # --- Imports (original logic kept; extended with named-import extraction) ---
        imports: list[ImportInfo] = []
        for i, line in enumerate(lines, 1):
            m = IMPORT_RE.match(line.strip())
            if m:
                names = _extract_named_imports(line.strip())
                imports.append(ImportInfo(module=m.group(1), names=names, line=i))
            for req in REQUIRE_RE.finditer(line):
                rn = REQUIRE_NAMED_RE.match(line.strip())
                names = _parse_destructured_names(rn.group(1)) if rn and rn.group(1) else []
                imports.append(ImportInfo(module=req.group(1), names=names, line=i))

        # --- Symbols (original logic kept; class methods added) ---
        symbols: list[SymbolInfo] = []
        seen_names: set[str] = set()

        for m in FUNC_RE.finditer(source):
            name = m.group(1)
            if name in seen_names:
                continue
            seen_names.add(name)
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
            if name in seen_names:
                continue
            seen_names.add(name)
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
                    signature=f"{name}()",
                    calls=calls,
                )
            )

        for m in CLASS_RE.finditer(source):
            name = m.group(1)
            if name in seen_names:
                continue
            seen_names.add(name)
            cls_start = source[: m.start()].count("\n") + 1
            cls_end = self._find_block_end(lines, cls_start)
            symbols.append(
                SymbolInfo(
                    name=name,
                    qualified_name=name,
                    symbol_type="class",
                    start_line=cls_start,
                    end_line=cls_end,
                )
            )
            # Extract methods within the class body
            cls_body = "\n".join(lines[cls_start - 1 : cls_end])
            for mm in CLASS_METHOD_RE.finditer(cls_body):
                mname = mm.group(1)
                if mname in _JS_RESERVED or mname == "constructor":
                    continue
                qname = f"{name}.{mname}"
                if qname in seen_names:
                    continue
                seen_names.add(qname)
                meth_start = cls_start + cls_body[: mm.start()].count("\n")
                meth_end = self._find_block_end(lines, meth_start)
                meth_body = "\n".join(lines[meth_start - 1 : meth_end])
                calls = self._extract_calls(meth_body)
                symbols.append(
                    SymbolInfo(
                        name=mname,
                        qualified_name=qname,
                        symbol_type="method",
                        start_line=meth_start,
                        end_line=meth_end,
                        signature=f"{qname}({mm.group(2)})",
                        calls=calls,
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
        seen: set[str] = set()
        reserved = {"if", "for", "while", "switch", "catch", "function", "return", "new"} | _JS_RESERVED

        # Original: bare function calls
        for m in CALL_RE.finditer(chunk):
            name = m.group(1)
            if name in reserved or name in seen:
                continue
            seen.add(name)
            line = chunk[: m.start()].count("\n") + 1
            calls.append(CallInfo(callee=name, line=line))

        # Extended: qualified obj.method() calls for cross-file resolution
        for m in QUALIFIED_CALL_RE.finditer(chunk):
            obj, method = m.group(1), m.group(2)
            if method in reserved:
                continue
            callee = f"{obj}.{method}"
            if callee in seen:
                continue
            seen.add(callee)
            line = chunk[: m.start()].count("\n") + 1
            calls.append(CallInfo(callee=callee, line=line))

        return calls[:40]


def _extract_named_imports(line: str) -> list[str]:
    """Extract named symbols from an ES6 import line.

    e.g. ``import { charge, refund } from './ledger'`` → ``['charge', 'refund']``
    """
    m = re.search(r"\{([^}]+)\}", line)
    if not m:
        return []
    return _parse_destructured_names(m.group(1))


def _parse_destructured_names(raw: str) -> list[str]:
    """Parse ``A, B as C, D`` into ``['A', 'C', 'D']`` (uses local alias)."""
    names: list[str] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        names.append(part.split(" as ")[-1].strip())
    return [n for n in names if n]
