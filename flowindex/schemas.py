"""Pydantic schemas for parser output and API responses."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ImportInfo(BaseModel):
    module: str
    names: list[str] = Field(default_factory=list)
    line: int


class CallInfo(BaseModel):
    callee: str
    line: int


class SymbolInfo(BaseModel):
    name: str
    qualified_name: str
    symbol_type: str
    start_line: int
    end_line: int
    signature: str = ""
    docstring: str = ""
    visibility: str = "public"
    decorators: list[str] = Field(default_factory=list)
    calls: list[CallInfo] = Field(default_factory=list)


class RouteInfo(BaseModel):
    method: str
    path: str
    handler_name: str
    framework: str
    start_line: int
    end_line: int


class TestInfo(BaseModel):
    test_name: str
    framework: str
    start_line: int
    end_line: int
    target_hint: str | None = None


class ParseResult(BaseModel):
    imports: list[ImportInfo] = Field(default_factory=list)
    symbols: list[SymbolInfo] = Field(default_factory=list)
    routes: list[RouteInfo] = Field(default_factory=list)
    tests: list[TestInfo] = Field(default_factory=list)


class ScanSummary(BaseModel):
    files_indexed: int
    symbols_indexed: int
    entrypoints_found: int
    tests_found: int
    git_commits_analyzed: int
    edges_created: int
    index_path: str


class RiskBreakdown(BaseModel):
    score: int
    level: str
    factors: list[str]


class ImpactResult(BaseModel):
    target: str
    entrypoints_affected: list[str]
    downstream_symbols: list[str]
    upstream_callers: list[str]
    related_tests: list[str]
    changed_together_files: list[str]
    recent_commits: list[str]
    risk: RiskBreakdown


class ContextPack(BaseModel):
    task: str
    entrypoints: list[str]
    files: list[str]
    symbols: list[str]
    tests: list[str]
    commits: list[str]
    cautions: list[str]
    instructions: list[str]

    def to_markdown(self) -> str:
        def bullets(items: list[str]) -> list[str]:
            return [f"- {x}" for x in items] if items else ["- (none)"]

        lines = [
            "# FlowIndex Context Pack",
            "",
            "## Task",
            self.task,
            "",
            "## Likely Relevant Entrypoints",
            *bullets(self.entrypoints),
            "",
            "## Likely Relevant Files",
            *bullets(self.files),
            "",
            "## High-Risk Symbols",
            *bullets(self.symbols),
            "",
            "## Tests to Run",
            *bullets(self.tests),
            "",
            "## Past Related Commits",
            *bullets(self.commits),
            "",
            "## Caution",
            *bullets(self.cautions),
            "",
            "## Suggested Agent Instructions",
            "Before editing, inspect:",
        ]
        for i, instr in enumerate(self.instructions, 1):
            lines.append(f"{i}. {instr}")
        return "\n".join(lines)
