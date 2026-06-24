"""Python AST parser."""

from __future__ import annotations

import ast
from pathlib import Path

from flowindex.frameworks.django import detect_django_views
from flowindex.frameworks.fastapi import detect_fastapi_routes
from flowindex.frameworks.flask import detect_flask_routes
from flowindex.indexer.tests import detect_pytest_tests
from flowindex.parsers.base import BaseParser
from flowindex.schemas import CallInfo, ImportInfo, ParseResult, SymbolInfo


class PythonParser(BaseParser):
    language = "python"

    def parse(self, path: Path, source: str) -> ParseResult:
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError:
            return ParseResult()

        imports: list[ImportInfo] = []
        symbols: list[SymbolInfo] = []

        class Visitor(ast.NodeVisitor):
            def __init__(self) -> None:
                self.scope: list[str] = []

            def visit_Import(self, node: ast.Import) -> None:
                for alias in node.names:
                    imports.append(ImportInfo(module=alias.name, names=[alias.asname or alias.name], line=node.lineno))
                self.generic_visit(node)

            def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
                module = node.module or ""
                names = [a.name for a in node.names]
                imports.append(ImportInfo(module=module, names=names, line=node.lineno))
                self.generic_visit(node)

            def _extract_calls(self, node: ast.AST) -> list[CallInfo]:
                calls: list[CallInfo] = []
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        callee = self._call_name(child.func)
                        if callee:
                            calls.append(CallInfo(callee=callee, line=child.lineno))
                return calls

            def _call_name(self, node: ast.AST) -> str | None:
                if isinstance(node, ast.Name):
                    return node.id
                if isinstance(node, ast.Attribute):
                    base = self._call_name(node.value)
                    return f"{base}.{node.attr}" if base else node.attr
                return None

            def _docstring(self, node: ast.AST) -> str:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                    doc = ast.get_docstring(node)
                    return doc or ""
                return ""

            def _signature(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
                args = [a.arg for a in node.args.args]
                return f"{node.name}({', '.join(args)})"

            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                qname = ".".join([*self.scope, node.name])
                decorators = [self._decorator_name(d) for d in node.decorator_list]
                symbols.append(
                    SymbolInfo(
                        name=node.name,
                        qualified_name=qname,
                        symbol_type="function",
                        start_line=node.lineno,
                        end_line=node.end_lineno or node.lineno,
                        signature=self._signature(node),
                        docstring=self._docstring(node),
                        decorators=[d for d in decorators if d],
                        calls=self._extract_calls(node),
                    )
                )
                self.generic_visit(node)

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
                qname = ".".join([*self.scope, node.name])
                decorators = [self._decorator_name(d) for d in node.decorator_list]
                symbols.append(
                    SymbolInfo(
                        name=node.name,
                        qualified_name=qname,
                        symbol_type="function",
                        start_line=node.lineno,
                        end_line=node.end_lineno or node.lineno,
                        signature=f"async {self._signature(node)}",
                        docstring=self._docstring(node),
                        decorators=[d for d in decorators if d],
                        calls=self._extract_calls(node),
                    )
                )
                self.generic_visit(node)

            def visit_ClassDef(self, node: ast.ClassDef) -> None:
                qname = ".".join([*self.scope, node.name])
                symbols.append(
                    SymbolInfo(
                        name=node.name,
                        qualified_name=qname,
                        symbol_type="class",
                        start_line=node.lineno,
                        end_line=node.end_lineno or node.lineno,
                        docstring=self._docstring(node),
                    )
                )
                self.scope.append(node.name)
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_qname = ".".join([*self.scope, item.name])
                        sig = (
                            self._signature(item)
                            if isinstance(item, ast.FunctionDef)
                            else f"async {self._signature(item)}"
                        )
                        symbols.append(
                            SymbolInfo(
                                name=item.name,
                                qualified_name=method_qname,
                                symbol_type="method",
                                start_line=item.lineno,
                                end_line=item.end_lineno or item.lineno,
                                signature=sig,
                                docstring=self._docstring(item),
                                visibility="private" if item.name.startswith("_") else "public",
                                calls=self._extract_calls(item),
                            )
                        )
                self.scope.pop()
                self.generic_visit(node)

            def _decorator_name(self, node: ast.AST) -> str:
                if isinstance(node, ast.Name):
                    return node.id
                if isinstance(node, ast.Attribute):
                    return node.attr
                if isinstance(node, ast.Call):
                    return self._decorator_name(node.func) or ""
                return ""

        visitor = Visitor()
        visitor.visit(tree)

        routes = detect_fastapi_routes(source, symbols)
        routes.extend(detect_flask_routes(source, symbols))
        routes.extend(detect_django_views(source, symbols))
        tests = detect_pytest_tests(source, path)

        return ParseResult(imports=imports, symbols=symbols, routes=routes, tests=tests)
