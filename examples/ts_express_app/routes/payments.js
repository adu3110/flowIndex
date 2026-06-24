const { validatePaymentInput, createPaymentIntent } = require("../services/payments");
const { updateLedger } = require("../services/ledger");
const { publishPaymentEvent } = require("../services/events");

async function createPaymentHandler(req, res) {
  validatePaymentInput(req.body.amount);
  const intent = createPaymentIntent(req.body.customerId, req.body.amount, req.body.idempotencyKey);
  updateLedger(intent.paymentId, req.body.amount);
  publishPaymentEvent(intent);
  res.json(intent);
}

async function handleStripeWebhook(req, res) {
  const eventType = req.body.type || "";
  if (eventType === "payment_intent.succeeded") {
    updateLedger(req.body.data.paymentId, req.body.data.amount);
  }
  res.json({ received: true });
}

module.exports = { createPaymentHandler, handleStripeWebhook };
