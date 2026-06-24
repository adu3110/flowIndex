function processRefund(paymentId, amount) {
  return { refundId: `ref_${paymentId}`, paymentId, amount };
}

module.exports = { processRefund };
