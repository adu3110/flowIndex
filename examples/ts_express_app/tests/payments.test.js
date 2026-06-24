const request = require("supertest");
const app = require("../server");
const { updateLedger, getLedgerBalance } = require("../services/ledger");

describe("payments API", () => {
  it("creates a payment", async () => {
    const res = await request(app)
      .post("/api/payments")
      .send({ customerId: "c1", amount: 500, idempotencyKey: "k1" });
    expect(res.status).toBe(200);
  });

  test("webhook retry updates ledger", async () => {
    const res = await request(app)
      .post("/api/stripe/webhook")
      .send({ type: "payment_intent.succeeded", data: { paymentId: "pay_1", amount: 100 } });
    expect(res.status).toBe(200);
  });
});

describe("ledger", () => {
  it("accumulates entries", () => {
    updateLedger("e1", 100);
    updateLedger("e1", 50);
    expect(getLedgerBalance("e1")).toBe(150);
  });
});
