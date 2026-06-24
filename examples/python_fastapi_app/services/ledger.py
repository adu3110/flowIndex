"""Shared ledger module — high-risk shared state."""

from __future__ import annotations

_ledger: dict[str, int] = {}


def update_ledger(entry_id: str, amount_cents: int) -> None:
    current = _ledger.get(entry_id, 0)
    _ledger[entry_id] = current + amount_cents


def get_ledger_balance(entry_id: str) -> int:
    return _ledger.get(entry_id, 0)
