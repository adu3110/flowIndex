"""Shared test fixtures."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from flowindex.config import FlowIndexConfig, write_default_config
from flowindex.db.session import init_db
from flowindex.indexer.pipeline import run_scan


@pytest.fixture
def fastapi_example(tmp_path: Path) -> Path:
    src = Path(__file__).resolve().parents[1] / "examples" / "python_fastapi_app"
    dest = tmp_path / "fastapi_app"
    shutil.copytree(src, dest)
    _init_git(dest)
    write_default_config(dest)
    init_db(dest / ".flowindex" / "flowindex.db")
    config = FlowIndexConfig.from_dict(dest, _default_config_dict())
    run_scan(config)
    return dest


@pytest.fixture
def express_example(tmp_path: Path) -> Path:
    src = Path(__file__).resolve().parents[1] / "examples" / "ts_express_app"
    dest = tmp_path / "express_app"
    shutil.copytree(src, dest)
    _init_git(dest)
    write_default_config(dest)
    init_db(dest / ".flowindex" / "flowindex.db")
    config = FlowIndexConfig.from_dict(dest, _default_config_dict())
    run_scan(config)
    return dest


def _init_git(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True)
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=path, check=True)
    subprocess.run(["git", "commit", "--allow-empty", "-m", "fix duplicate ledger entry"], cwd=path, check=True)


def _default_config_dict() -> dict:
    from flowindex.config import DEFAULT_CONFIG
    return dict(DEFAULT_CONFIG)
