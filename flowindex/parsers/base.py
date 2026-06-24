"""Parser base types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from flowindex.schemas import ParseResult


class BaseParser(ABC):
    language: str

    @abstractmethod
    def parse(self, path: Path, source: str) -> ParseResult:
        raise NotImplementedError
