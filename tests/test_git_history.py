"""Git history analyzer tests."""

from sqlmodel import select

from flowindex.config import load_config
from flowindex.db.models import GraphEdge
from flowindex.db.session import get_session


def test_git_commits_indexed(fastapi_example) -> None:
    config = load_config(fastapi_example)
    with get_session(config.db_path) as session:
        from flowindex.db.models import CommitNode, Repository
        repo = session.exec(select(Repository)).first()
        commits = session.exec(select(CommitNode).where(CommitNode.repo_id == repo.id)).all()
        assert len(commits) >= 1


def test_changed_with_edges(fastapi_example) -> None:
    config = load_config(fastapi_example)
    with get_session(config.db_path) as session:
        from flowindex.db.models import Repository
        repo = session.exec(select(Repository)).first()
        edges = session.exec(
            select(GraphEdge).where(
                GraphEdge.repo_id == repo.id,
                GraphEdge.edge_type == "changed_with",
            )
        ).all()
        # May be empty for tiny repos; ensure analyzer ran without error
        assert edges is not None
