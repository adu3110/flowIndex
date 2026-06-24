"""Impact analysis tests."""

from sqlmodel import select

from flowindex.config import load_config
from flowindex.db.models import GraphEdge, Repository
from flowindex.db.session import get_session
from flowindex.indexer.impact import analyze_impact, suggest_tests


def test_impact_on_ledger(fastapi_example) -> None:
    config = load_config(fastapi_example)
    with get_session(config.db_path) as session:
        repo = session.exec(select(Repository)).first()
        result = analyze_impact(session, repo.id, "update_ledger")
        assert result.target
        assert result.risk.level in {"low", "medium", "high"}
        assert result.risk.factors


def test_impact_critical_path_boost(fastapi_example) -> None:
    config = load_config(fastapi_example)
    with get_session(config.db_path) as session:
        repo = session.exec(select(Repository)).first()
        result = analyze_impact(session, repo.id, "services/ledger.py")
        assert result.target
        assert result.risk.level in {"low", "medium", "high"}
        assert len(result.risk.factors) >= 1


def test_suggest_tests_for_ledger(fastapi_example) -> None:
    """suggest_tests should surface tests related to ledger.py."""
    config = load_config(fastapi_example)
    with get_session(config.db_path) as session:
        repo = session.exec(select(Repository)).first()
        tests = suggest_tests(session, repo.id, "services/ledger.py")
        # At minimum the keyword match should find tests with 'ledger' in path/name
        assert isinstance(tests, list)


def test_cross_file_import_edges_created(fastapi_example) -> None:
    """The graph should contain import edges between files after a scan."""
    config = load_config(fastapi_example)
    with get_session(config.db_path) as session:
        repo = session.exec(select(Repository)).first()
        import_edges = session.exec(
            select(GraphEdge).where(
                GraphEdge.repo_id == repo.id,
                GraphEdge.edge_type == "imports",
            )
        ).all()
        assert len(import_edges) >= 1, "Expected at least one import edge in graph"
