"""Entrypoint helpers."""

from __future__ import annotations

from sqlmodel import Session, select

from flowindex.db.models import EntrypointNode


def list_entrypoints(session: Session, repo_id: int, limit: int = 20) -> list[EntrypointNode]:
    stmt = select(EntrypointNode).where(EntrypointNode.repo_id == repo_id).limit(limit)
    return list(session.exec(stmt).all())
