# Examples

FlowIndex ships two toy applications under `examples/`.

## Python FastAPI app

```bash
cd examples/python_fastapi_app
flowindex init --here
flowindex scan
flowindex explain "POST /payments"
flowindex context "fix duplicate payments when webhook retries"
```

Use `--here` when the example sits inside a larger git repo.

Structure:

- `main.py` — FastAPI routes for payments, refunds, Stripe webhook
- `services/ledger.py` — shared ledger (high-risk module)
- `tests/test_payments.py` — pytest tests

## TypeScript Express app

```bash
cd examples/ts_express_app
flowindex init --here
flowindex scan
flowindex explain "POST /api/payments"
flowindex impact services/ledger.js
```

Structure:

- `server.js` — Express app wiring
- `routes/payments.js` — payment and webhook handlers
- `services/ledger.js` — shared ledger
- `tests/payments.test.js` — Jest-style tests
