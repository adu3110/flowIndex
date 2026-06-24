"""FlowIndex configuration and repository root detection."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import tomli_w

FLOWINDEX_DIR = ".flowindex"
CONFIG_FILE = "config.toml"
DB_FILE = "flowindex.db"

DEFAULT_EXCLUDES = [
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    ".next",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".flowindex",
]

DEFAULT_INCLUDES = ["**/*"]

DEFAULT_LANGUAGES = ["python", "typescript", "javascript"]

DEFAULT_TEST_DIRS = ["tests", "test", "__tests__", "spec"]

DEFAULT_CONFIG: dict[str, Any] = {
    "included_paths": DEFAULT_INCLUDES,
    "excluded_paths": DEFAULT_EXCLUDES,
    "supported_languages": DEFAULT_LANGUAGES,
    "test_directories": DEFAULT_TEST_DIRS,
    "framework_detection": {
        "fastapi": True,
        "flask": True,
        "django": True,
        "express": True,
        "nextjs": True,
    },
    "git": {
        "max_commits": 500,
        "changed_with_min_count": 2,
    },
}


@dataclass
class FlowIndexConfig:
    """Runtime configuration loaded from `.flowindex/config.toml`."""

    root_path: Path
    included_paths: list[str] = field(default_factory=lambda: list(DEFAULT_INCLUDES))
    excluded_paths: list[str] = field(default_factory=lambda: list(DEFAULT_EXCLUDES))
    supported_languages: list[str] = field(default_factory=lambda: list(DEFAULT_LANGUAGES))
    test_directories: list[str] = field(default_factory=lambda: list(DEFAULT_TEST_DIRS))
    framework_detection: dict[str, bool] = field(
        default_factory=lambda: dict(DEFAULT_CONFIG["framework_detection"])
    )
    git_max_commits: int = 500
    git_changed_with_min_count: int = 2

    @property
    def flowindex_dir(self) -> Path:
        return self.root_path / FLOWINDEX_DIR

    @property
    def db_path(self) -> Path:
        return self.flowindex_dir / DB_FILE

    @property
    def config_path(self) -> Path:
        return self.flowindex_dir / CONFIG_FILE

    @classmethod
    def from_dict(cls, root_path: Path, data: dict[str, Any]) -> FlowIndexConfig:
        git = data.get("git", {})
        return cls(
            root_path=root_path.resolve(),
            included_paths=list(data.get("included_paths", DEFAULT_INCLUDES)),
            excluded_paths=list(data.get("excluded_paths", DEFAULT_EXCLUDES)),
            supported_languages=list(data.get("supported_languages", DEFAULT_LANGUAGES)),
            test_directories=list(data.get("test_directories", DEFAULT_TEST_DIRS)),
            framework_detection=dict(
                data.get("framework_detection", DEFAULT_CONFIG["framework_detection"])
            ),
            git_max_commits=int(git.get("max_commits", 500)),
            git_changed_with_min_count=int(git.get("changed_with_min_count", 2)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "included_paths": self.included_paths,
            "excluded_paths": self.excluded_paths,
            "supported_languages": self.supported_languages,
            "test_directories": self.test_directories,
            "framework_detection": self.framework_detection,
            "git": {
                "max_commits": self.git_max_commits,
                "changed_with_min_count": self.git_changed_with_min_count,
            },
        }


def find_repo_root(start: Path | None = None) -> Path:
    """Walk up from start (or cwd) to find the nearest `.flowindex` directory."""
    current = (start or Path.cwd()).resolve()
    for path in [current, *current.parents]:
        if (path / FLOWINDEX_DIR).is_dir():
            return path
    raise FileNotFoundError(
        "FlowIndex is not initialized. Run `flowindex init` in your repository root."
    )


def find_project_root(start: Path | None = None, *, here: bool = False) -> Path:
    """Find git root or cwd for init/scan before `.flowindex` exists."""
    current = (start or Path.cwd()).resolve()
    if here:
        return current
    for path in [current, *current.parents]:
        if (path / ".git").exists():
            return path
    return current


def load_config(root: Path | None = None) -> FlowIndexConfig:
    root_path = find_repo_root(root)
    config_path = root_path / FLOWINDEX_DIR / CONFIG_FILE
    if not config_path.exists():
        raise FileNotFoundError(f"Missing config at {config_path}. Run `flowindex init`.")
    with config_path.open("rb") as f:
        data = tomllib.load(f)
    return FlowIndexConfig.from_dict(root_path, data)


def write_default_config(root_path: Path) -> Path:
    """Create `.flowindex/config.toml` with defaults."""
    flowindex_dir = root_path / FLOWINDEX_DIR
    flowindex_dir.mkdir(parents=True, exist_ok=True)
    config_path = flowindex_dir / CONFIG_FILE
    with config_path.open("wb") as f:
        tomli_w.dump(DEFAULT_CONFIG, f)
    return config_path


def should_exclude(path: Path, root: Path, config: FlowIndexConfig) -> bool:
    rel = path.relative_to(root).as_posix()
    parts = rel.split("/")
    for excluded in config.excluded_paths:
        if excluded in parts or rel.startswith(excluded.rstrip("/")):
            return True
        if rel == excluded or rel.startswith(f"{excluded}/"):
            return True
    return False


def detect_language(path: Path) -> str | None:
    ext = path.suffix.lower()
    mapping = {
        ".py": "python",
        ".pyi": "python",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".mjs": "javascript",
        ".cjs": "javascript",
    }
    lang = mapping.get(ext)
    if lang == "typescript" and "javascript" in os.environ.get("FLOWINDEX_FORCE_JS", ""):
        return "javascript"
    return lang
