"""Refund service."""

from __future__ import annotations


def process_refund(payment_id: str, amount_cents: int) -> dict[str, str]:
    return {
        "refund_id": f"ref_{payment_id}",
        "payment_id": payment_id,
        "amount_cents": str(amount_cents),
    }
