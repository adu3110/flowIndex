const { processRefund } = require("../services/refunds");
const { updateLedger } = require("../services/ledger");

async function createRefundHandler(req, res) {
  const result = processRefund(req.body.paymentId, req.body.amount);
  updateLedger(result.refundId, -req.body.amount);
  res.json(result);
}

module.exports = { createRefundHandler };
