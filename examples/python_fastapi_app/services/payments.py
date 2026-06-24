"""Payment service layer."""

from __future__ import annotations


def validate_payment_input(amount_cents: int) -> None:
    if amount_cents <= 0:
        raise ValueError("amount must be positive")


def create_payment_intent(customer: dict, amount_cents: int, idempotency_key: str) -> dict[str, str]:
    payment_id = f"pay_{idempotency_key}"
    return {
        "payment_id": payment_id,
        "customer_id": customer["customer_id"],
        "amount_cents": str(amount_cents),
        "status": "created",
    }
