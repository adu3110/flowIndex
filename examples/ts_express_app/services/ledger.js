const ledger = new Map();

function updateLedger(entryId, amount) {
  const current = ledger.get(entryId) || 0;
  ledger.set(entryId, current + amount);
}

function getLedgerBalance(entryId) {
  return ledger.get(entryId) || 0;
}

module.exports = { updateLedger, getLedgerBalance };
