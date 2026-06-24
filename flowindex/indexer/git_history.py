"""Git history analysis."""

from __future__ import annotations

import subprocess
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from itertools import combinations
from pathlib import Path

from sqlmodel import Session

from flowindex.config import FlowIndexConfig
from flowindex.db.models import RISK_KEYWORDS, CommitNode
from flowindex.indexer.graph import add_edge


@dataclass
class GitAnalysisResult:
    commits: list[CommitNode]
    changed_with_edges: int
    hot_files: list[tuple[str, int]]
    bugfix_commits: list[tuple[str, str]]


def analyze_git_history(
    session: Session,
    repo_id: int,
    root: Path,
    config: FlowIndexConfig,
    file_path_to_id: dict[str, int],
) -> GitAnalysisResult:
    commits_raw = _git_log(root, config.git_max_commits)
    commits: list[CommitNode] = []
    bugfix: list[tuple[str, str]] = []
    file_change_counts: Counter[str] = Counter()
    pair_counts: Counter[tuple[str, str]] = Counter()
    commit_files: list[tuple[str, list[str]]] = []

    for entry in commits_raw:
        commit_hash, author, date_str, message, files = entry
        try:
            date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            date = datetime.now(UTC)
        node = CommitNode(
            repo_id=repo_id,
            commit_hash=commit_hash,
            author=author,
            date=date,
            message=message,
        )
        session.add(node)
        session.flush()
        commits.append(node)

        msg_lower = message.lower()
        if any(kw in msg_lower for kw in RISK_KEYWORDS):
            bugfix.append((commit_hash[:7], message[:80]))

        rel_files = [f for f in files if f in file_path_to_id]
        for f in rel_files:
            file_change_counts[f] += 1
        commit_files.append((commit_hash, rel_files))

    edge_count = 0
    for _, files in commit_files:
        if len(files) < 2:
            continue
        for a, b in combinations(sorted(set(files)), 2):
            pair_counts[(a, b)] += 1

    for (a, b), count in pair_counts.items():
        if count < config.git_changed_with_min_count:
            continue
        fa, fb = file_path_to_id.get(a), file_path_to_id.get(b)
        if fa and fb:
            add_edge(
                session,
                repo_id,
                "file",
                fa,
                "file",
                fb,
                "changed_with",
                weight=float(count),
                evidence=f"co-changed {count} times",
            )
            edge_count += 1

    hot_files = file_change_counts.most_common(10)
    session.commit()
    return GitAnalysisResult(
        commits=commits,
        changed_with_edges=edge_count,
        hot_files=hot_files,
        bugfix_commits=bugfix[:20],
    )


def commits_for_file(session: Session, repo_id: int, file_path: str, limit: int = 10) -> list[str]:
    """Return recent commit summaries mentioning or touching a file (via git re-log)."""
    # Stored commit messages matched by filename keyword heuristic
    rows = session.exec(
        __import__("sqlmodel").select(CommitNode).where(CommitNode.repo_id == repo_id)
    ).all()
    keyword = Path(file_path).stem.lower()
    matched = []
    for row in rows:
        if keyword in row.message.lower() or keyword in file_path.lower():
            matched.append(f"{row.commit_hash[:7]} {row.message[:60]}")
    return matched[:limit]


def _git_log(root: Path, max_commits: int) -> list[tuple[str, str, str, str, list[str]]]:
    fmt = "%H%x1f%an%x1f%aI%x1f%s"
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "log", f"-{max_commits}", f"--pretty=format:{fmt}", "--name-only"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return []
    if proc.returncode != 0:
        return []

    entries: list[tuple[str, str, str, str, list[str]]] = []
    current: tuple[str, str, str, str] | None = None
    files: list[str] = []

    for line in proc.stdout.splitlines():
        if "\x1f" in line:
            if current:
                entries.append((*current, files))
            parts = line.split("\x1f")
            if len(parts) >= 4:
                current = (parts[0], parts[1], parts[2], parts[3])
                files = []
        elif line.strip():
            files.append(line.strip())
    if current:
        entries.append((*current, files))
    return entries
