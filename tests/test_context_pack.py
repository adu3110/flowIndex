"""Context pack tests."""

from sqlmodel import select

from flowindex.config import load_config
from flowindex.db.models import Repository
from flowindex.db.session import get_session
from flowindex.indexer.context_pack import make_context_pack


def test_context_pack_for_payment_task(fastapi_example) -> None:
    config = load_config(fastapi_example)
    with get_session(config.db_path) as session:
        repo = session.exec(select(Repository)).first()
        pack = make_context_pack(session, repo.id, "fix duplicate payments when webhook retries")
        assert pack.task
        md = pack.to_markdown()
        assert "FlowIndex Context Pack" in md
        assert len(pack.files) >= 1 or len(pack.entrypoints) >= 1
