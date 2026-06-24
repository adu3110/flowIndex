"""Database session management."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine, select

from flowindex.db.models import (
    CommitNode,
    EntrypointNode,
    FileNode,
    GraphEdge,
    SymbolNode,
    TestNode,
)


def get_engine(db_path: Path) -> Engine:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{db_path}", echo=False)


def init_db(db_path: Path) -> None:
    engine = get_engine(db_path)
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session(db_path: Path) -> Iterator[Session]:
    engine = get_engine(db_path)
    with Session(engine) as session:
        yield session


def clear_repo_data(session: Session, repo_id: int) -> None:
    """Remove all indexed data for a repository before re-scan."""
    for model in (GraphEdge, CommitNode, TestNode, EntrypointNode, SymbolNode, FileNode):
        rows = session.exec(select(model).where(model.repo_id == repo_id)).all()
        for row in rows:
            session.delete(row)
    session.commit()
