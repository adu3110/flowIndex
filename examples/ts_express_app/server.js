const express = require("express");
const { createPaymentHandler, handleStripeWebhook } = require("./routes/payments");
const { createRefundHandler } = require("./routes/refunds");

const app = express();
app.use(express.json());

app.get("/health", (_req, res) => res.json({ status: "ok" }));
app.post("/api/payments", createPaymentHandler);
app.post("/api/stripe/webhook", handleStripeWebhook);
app.post("/api/refunds", createRefundHandler);

module.exports = app;
