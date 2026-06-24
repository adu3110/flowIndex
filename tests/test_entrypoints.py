"""Entrypoint detection integration tests."""

from sqlmodel import select

from flowindex.config import load_config
from flowindex.db.models import EntrypointNode
from flowindex.db.session import get_session


def test_fastapi_entrypoints_indexed(fastapi_example) -> None:
    config = load_config(fastapi_example)
    with get_session(config.db_path) as session:
        from flowindex.db.models import Repository
        repo = session.exec(select(Repository)).first()
        assert repo and repo.id
        eps = session.exec(select(EntrypointNode).where(EntrypointNode.repo_id == repo.id)).all()
        paths = {ep.path for ep in eps}
        assert "/payments" in paths or any("/payments" in (p or "") for p in paths)


def test_express_entrypoints_indexed(express_example) -> None:
    config = load_config(express_example)
    with get_session(config.db_path) as session:
        from flowindex.db.models import Repository
        repo = session.exec(select(Repository)).first()
        eps = session.exec(select(EntrypointNode).where(EntrypointNode.repo_id == repo.id)).all()
        assert len(eps) >= 1
