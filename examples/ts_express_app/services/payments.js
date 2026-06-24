function validatePaymentInput(amount) {
  if (amount <= 0) throw new Error("amount must be positive");
}

function createPaymentIntent(customerId, amount, idempotencyKey) {
  return {
    paymentId: `pay_${idempotencyKey}`,
    customerId,
    amount,
    status: "created",
  };
}

module.exports = { validatePaymentInput, createPaymentIntent };
