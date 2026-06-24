"""Full repository indexing pipeline."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import Session, select

from flowindex.config import FlowIndexConfig
from flowindex.db.migrations import migrate
from flowindex.db.models import FileNode, Repository
from flowindex.db.session import clear_repo_data, get_session
from flowindex.indexer.git_history import analyze_git_history
from flowindex.indexer.graph import build_file_graph, link_entrypoints, link_tests
from flowindex.indexer.scanner import discover_files, scan_file
from flowindex.indexer.symbols import store_entrypoints, store_symbols, store_tests
from flowindex.parsers.python_parser import PythonParser
from flowindex.parsers.ts_parser import TypeScriptParser
from flowindex.schemas import ScanSummary


def run_scan(config: FlowIndexConfig) -> ScanSummary:
    migrate(config.db_path)
    root = config.root_path

    with get_session(config.db_path) as session:
        repo = _get_or_create_repo(session, root)
        assert repo.id
        clear_repo_data(session, repo.id)

        parsers = {
            "python": PythonParser(),
            "typescript": TypeScriptParser(),
            "javascript": TypeScriptParser(),
        }

        files_indexed = 0
        symbols_indexed = 0
        entrypoints_found = 0
        tests_found = 0
        edges_created = 0
        file_path_map: dict[str, int] = {}
        global_symbol_map: dict[str, int] = {}

        discovered = discover_files(root, config)
        for path in discovered:
            scanned = scan_file(path, root)
            if not scanned:
                continue

            parser = parsers.get(scanned.language)
            if not parser:
                continue

            file_node = FileNode(
                repo_id=repo.id,
                path=scanned.relative_path,
                language=scanned.language,
                size_bytes=scanned.size_bytes,
                content_hash=scanned.content_hash,
                last_indexed_at=datetime.now(UTC),
            )
            session.add(file_node)
            session.flush()
            assert file_node.id
            file_path_map[scanned.relative_path] = file_node.id
            files_indexed += 1

            result = parser.parse(path, scanned.source)
            symbol_map = store_symbols(session, repo.id, file_node.id, result.symbols)
            global_symbol_map.update(symbol_map)
            symbols_indexed += len(result.symbols)

            entrypoints = store_entrypoints(session, repo.id, file_node.id, result.routes, symbol_map)
            entrypoints_found += len(entrypoints)
            for ep in entrypoints:
                edges_created += link_entrypoints(session, repo.id, ep.id or 0, ep.symbol_id, file_node.id)

            test_nodes = store_tests(session, repo.id, file_node.id, result.tests, symbol_map)
            tests_found += len(test_nodes)
            for tn in test_nodes:
                target_sym = _match_test_target(tn.target_hint, global_symbol_map)
                edges_created += link_tests(session, repo.id, tn.id or 0, file_node.id, target_sym)

            edges_created += build_file_graph(
                session, repo.id, file_node.id, result, global_symbol_map, file_path_map
            )

        session.commit()

        git_result = analyze_git_history(session, repo.id, root, config, file_path_map)
        git_commits = len(git_result.commits)
        edges_created += git_result.changed_with_edges

        repo.updated_at = datetime.now(UTC)
        session.add(repo)
        session.commit()

        return ScanSummary(
            files_indexed=files_indexed,
            symbols_indexed=symbols_indexed,
            entrypoints_found=entrypoints_found,
            tests_found=tests_found,
            git_commits_analyzed=git_commits,
            edges_created=edges_created,
            index_path=str(config.db_path),
        )


def _get_or_create_repo(session: Session, root: Path) -> Repository:
    root_str = str(root.resolve())
    existing = session.exec(select(Repository).where(Repository.root_path == root_str)).first()
    if existing:
        return existing
    repo = Repository(root_path=root_str, name=root.name)
    session.add(repo)
    session.commit()
    session.refresh(repo)
    return repo


def _match_test_target(hint: str | None, symbol_map: dict[str, int]) -> int | None:
    if not hint:
        return None
    for qname, sid in symbol_map.items():
        if hint in qname.lower():
            return sid
    return None
