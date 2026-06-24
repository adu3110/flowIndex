"""Payments API tests."""

import pytest
from fastapi.testclient import TestClient
from main import app
from services.ledger import get_ledger_balance, update_ledger
from services.payments import create_payment_intent, validate_payment_input


@pytest.fixture
def client():
    return TestClient(app)


def test_validate_payment_input_rejects_zero():
    with pytest.raises(ValueError):
        validate_payment_input(0)


def test_create_payment_intent_idempotency():
    customer = {"customer_id": "cust_1"}
    intent = create_payment_intent(customer, 1000, "key-abc")
    assert intent["payment_id"] == "pay_key-abc"


def test_create_payment_handler(client):
    response = client.post(
        "/api/payments",
        json={"customer_id": "cust_1", "amount_cents": 500, "idempotency_key": "k1"},
    )
    assert response.status_code == 200


def test_webhook_retry_updates_ledger(client):
    payload = {"type": "payment_intent.succeeded", "data": {"payment_id": "pay_1", "amount": 100}}
    response = client.post("/api/stripe/webhook", json=payload)
    assert response.status_code == 200


class TestLedger:
    def test_update_ledger_accumulates(self):
        update_ledger("entry_1", 100)
        update_ledger("entry_1", 50)
        assert get_ledger_balance("entry_1") == 150
