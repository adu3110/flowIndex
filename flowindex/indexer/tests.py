"""Test detection helpers."""

from __future__ import annotations

import re
from pathlib import Path

from flowindex.schemas import TestInfo

PYTEST_FUNC = re.compile(r"^def\s+(test_\w+)", re.MULTILINE)
PYTEST_CLASS = re.compile(r"^class\s+(Test\w+)", re.MULTILINE)
JS_TEST = re.compile(r"\b(?:it|test)\(\s*['\"`]([^'\"`]+)['\"`]", re.MULTILINE)
JS_DESCRIBE = re.compile(r"\bdescribe\(\s*['\"`]([^'\"`]+)['\"`]", re.MULTILINE)


def detect_pytest_tests(source: str, path: Path) -> list[TestInfo]:
    if not _is_test_file(path):
        return []
    tests: list[TestInfo] = []
    for m in PYTEST_FUNC.finditer(source):
        line = source[: m.start()].count("\n") + 1
        tests.append(
            TestInfo(
                test_name=m.group(1),
                framework="pytest",
                start_line=line,
                end_line=line,
                target_hint=_target_hint(m.group(1)),
            )
        )
    for m in PYTEST_CLASS.finditer(source):
        line = source[: m.start()].count("\n") + 1
        tests.append(
            TestInfo(
                test_name=m.group(1),
                framework="pytest",
                start_line=line,
                end_line=line,
            )
        )
    return tests


def detect_js_tests(source: str, path: Path) -> list[TestInfo]:
    if not _is_test_file(path):
        return []
    framework = "vitest" if "vitest" in source else "jest"
    tests: list[TestInfo] = []
    for m in JS_TEST.finditer(source):
        line = source[: m.start()].count("\n") + 1
        tests.append(
            TestInfo(
                test_name=m.group(1),
                framework=framework,
                start_line=line,
                end_line=line,
                target_hint=_target_hint(m.group(1)),
            )
        )
    for m in JS_DESCRIBE.finditer(source):
        line = source[: m.start()].count("\n") + 1
        tests.append(
            TestInfo(
                test_name=m.group(1),
                framework=framework,
                start_line=line,
                end_line=line,
            )
        )
    return tests


def _is_test_file(path: Path) -> bool:
    name = path.name.lower()
    parts = path.as_posix().lower()
    return (
        name.startswith("test_")
        or name.endswith("_test.py")
        or ".test." in name
        or ".spec." in name
        or "/tests/" in parts
        or "/__tests__/" in parts
        or "/test/" in parts
    )


def _target_hint(name: str) -> str | None:
    cleaned = re.sub(r"^test_", "", name, flags=re.IGNORECASE)
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "", cleaned)
    return cleaned.lower() if cleaned else None
