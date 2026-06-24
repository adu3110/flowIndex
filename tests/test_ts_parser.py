"""TypeScript/JavaScript parser tests."""

from pathlib import Path

from flowindex.parsers.ts_parser import TypeScriptParser

SAMPLE = '''
import express from "express";
const app = express();

app.post("/api/payments", async function createPaymentHandler(req, res) {
  validatePaymentInput(req.body.amount);
  const intent = createPaymentIntent(req.body.customerId, req.body.amount);
  updateLedger(intent.paymentId, req.body.amount);
  res.json(intent);
});

function validatePaymentInput(amount) {}
function createPaymentIntent(customerId, amount) { return {}; }
'''


def test_ts_parser_extracts_functions(tmp_path: Path) -> None:
    path = tmp_path / "server.ts"
    path.write_text(SAMPLE)
    result = TypeScriptParser().parse(path, SAMPLE)
    names = {s.name for s in result.symbols}
    assert "createPaymentHandler" in names
    assert "validatePaymentInput" in names


def test_express_route_detection(tmp_path: Path) -> None:
    path = tmp_path / "server.ts"
    path.write_text(SAMPLE)
    result = TypeScriptParser().parse(path, SAMPLE)
    assert any(r.path == "/api/payments" and r.method == "POST" for r in result.routes)


def test_jest_detection(tmp_path: Path) -> None:
    source = 'describe("payments", () => { it("creates payment", () => {}); });'
    path = tmp_path / "payments.test.ts"
    path.write_text(source)
    result = TypeScriptParser().parse(path, source)
    assert len(result.tests) >= 1
