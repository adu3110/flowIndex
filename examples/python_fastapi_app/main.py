"""FastAPI payments example for FlowIndex demos."""

from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel
from services.ledger import update_ledger
from services.payments import create_payment_intent, validate_payment_input
from services.refunds import process_refund

app = FastAPI(title="Payments API")
router = APIRouter()


class PaymentRequest(BaseModel):
    customer_id: str
    amount_cents: int
    idempotency_key: str


class RefundRequest(BaseModel):
    payment_id: str
    amount_cents: int


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/payments")
async def create_payment_handler(body: PaymentRequest) -> dict[str, str]:
    validate_payment_input(body.amount_cents)
    customer = get_customer_account(body.customer_id)
    intent = create_payment_intent(customer, body.amount_cents, body.idempotency_key)
    update_ledger(intent["payment_id"], body.amount_cents)
    publish_payment_event(intent)
    return intent


@router.post("/refunds")
async def create_refund_handler(body: RefundRequest) -> dict[str, str]:
    result = process_refund(body.payment_id, body.amount_cents)
    update_ledger(result["refund_id"], -body.amount_cents)
    return result


@router.post("/stripe/webhook")
async def handle_stripe_webhook(payload: dict) -> dict[str, str]:
    event_type = payload.get("type", "")
    if event_type == "payment_intent.succeeded":
        payment_id = payload["data"]["payment_id"]
        amount = payload["data"]["amount"]
        update_ledger(payment_id, amount)
    return {"received": True}


def get_customer_account(customer_id: str) -> dict[str, str]:
    if not customer_id:
        raise HTTPException(status_code=400, detail="missing customer")
    return {"customer_id": customer_id}


def publish_payment_event(intent: dict) -> None:
    _ = intent


app.include_router(router, prefix="/api")
