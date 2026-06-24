"""SQLModel database models for FlowIndex."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(UTC)


class Repository(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    root_path: str
    name: str
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class FileNode(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    repo_id: int = Field(foreign_key="repository.id", index=True)
    path: str = Field(index=True)
    language: str
    size_bytes: int
    content_hash: str
    last_indexed_at: datetime = Field(default_factory=utcnow)


class SymbolNode(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    repo_id: int = Field(foreign_key="repository.id", index=True)
    file_id: int = Field(foreign_key="filenode.id", index=True)
    name: str = Field(index=True)
    qualified_name: str = Field(index=True)
    symbol_type: str = Field(index=True)
    start_line: int
    end_line: int
    signature: str = ""
    docstring: str = ""
    visibility: str = "public"


class EntrypointNode(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    repo_id: int = Field(foreign_key="repository.id", index=True)
    file_id: int = Field(foreign_key="filenode.id", index=True)
    symbol_id: int | None = Field(default=None, foreign_key="symbolnode.id")
    entrypoint_type: str = Field(index=True)
    method: str | None = None
    path: str | None = Field(default=None, index=True)
    name: str
    framework: str
    start_line: int
    end_line: int


class TestNode(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    repo_id: int = Field(foreign_key="repository.id", index=True)
    file_id: int = Field(foreign_key="filenode.id", index=True)
    symbol_id: int | None = Field(default=None, foreign_key="symbolnode.id")
    test_name: str = Field(index=True)
    framework: str
    target_hint: str | None = None
    start_line: int
    end_line: int


class CommitNode(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    repo_id: int = Field(foreign_key="repository.id", index=True)
    commit_hash: str = Field(index=True)
    author: str
    date: datetime
    message: str


class GraphEdge(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    repo_id: int = Field(foreign_key="repository.id", index=True)
    source_type: str
    source_id: int
    target_type: str
    target_id: int
    edge_type: str = Field(index=True)
    weight: float = 1.0
    evidence: str = ""
    created_at: datetime = Field(default_factory=utcnow)


EDGE_TYPES = frozenset(
    {
        "defines",
        "imports",
        "calls",
        "exposes",
        "handled_by",
        "tests",
        "covers",
        "changed_with",
        "depends_on",
        "reads",
        "writes",
        "mentions",
    }
)

RISK_KEYWORDS = frozenset(
    {
        "fix",
        "bug",
        "regression",
        "revert",
        "failing",
        "broken",
        "incident",
        "hotfix",
        "flaky",
    }
)

CRITICAL_PATH_KEYWORDS = frozenset(
    {"auth", "payment", "billing", "db", "database", "security", "migration"}
)
