"""File discovery and scanning."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from flowindex.config import FlowIndexConfig, detect_language, should_exclude


@dataclass
class ScannedFile:
    path: Path
    relative_path: str
    language: str
    size_bytes: int
    content_hash: str
    source: str


def discover_files(root: Path, config: FlowIndexConfig) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if should_exclude(path, root, config):
            continue
        lang = detect_language(path)
        if lang is None or lang not in config.supported_languages:
            continue
        files.append(path)
    return sorted(files)


def scan_file(path: Path, root: Path) -> ScannedFile | None:
    lang = detect_language(path)
    if lang is None:
        return None
    try:
        source = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None
    rel = path.relative_to(root).as_posix()
    content_hash = hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
    return ScannedFile(
        path=path,
        relative_path=rel,
        language=lang,
        size_bytes=path.stat().st_size,
        content_hash=content_hash,
        source=source,
    )
