"""Simple schema migrations for FlowIndex SQLite database."""

from __future__ import annotations

from pathlib import Path

from flowindex.db.session import init_db


def migrate(db_path: Path) -> None:
    """Create or upgrade schema. MVP uses create_all."""
    init_db(db_path)
