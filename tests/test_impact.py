"""Impact analysis tests."""

from sqlmodel import select

from flowindex.config import load_config
from flowindex.db.models import Repository
from flowindex.db.session import get_session
from flowindex.indexer.impact import analyze_impact


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
