"""TypeScript/JavaScript parser tests."""

from pathlib import Path

from flowindex.parsers.ts_parser import TypeScriptParser, _extract_named_imports, _parse_destructured_names

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

CLASS_SAMPLE = '''
import { charge, refund } from "./ledger";

export class PaymentService {
  async processPayment(amount: number): Promise<void> {
    const result = charge(amount);
    return result;
  }

  async refundPayment(id: string): Promise<void> {
    refund(id);
  }
}
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


def test_class_method_extraction(tmp_path: Path) -> None:
    """Class methods should be extracted as qualified ClassName.method symbols."""
    path = tmp_path / "service.ts"
    path.write_text(CLASS_SAMPLE)
    result = TypeScriptParser().parse(path, CLASS_SAMPLE)
    qnames = {s.qualified_name for s in result.symbols}
    assert "PaymentService" in qnames
    assert "PaymentService.processPayment" in qnames
    assert "PaymentService.refundPayment" in qnames


def test_named_import_extraction() -> None:
    """Named imports should be extracted for cross-file call resolution."""
    line = 'import { charge, refund } from "./ledger";'
    names = _extract_named_imports(line)
    assert "charge" in names
    assert "refund" in names


def test_named_import_alias() -> None:
    """Import aliases (X as Y) should resolve to the local alias."""
    raw = "charge as pay, refund"
    names = _parse_destructured_names(raw)
    assert "pay" in names
    assert "refund" in names
    assert "charge" not in names


def test_named_imports_on_import_info(tmp_path: Path) -> None:
    """ImportInfo.names should be populated from named imports."""
    path = tmp_path / "service.ts"
    path.write_text(CLASS_SAMPLE)
    result = TypeScriptParser().parse(path, CLASS_SAMPLE)
    ledger_import = next((i for i in result.imports if "ledger" in i.module), None)
    assert ledger_import is not None
    assert "charge" in ledger_import.names
    assert "refund" in ledger_import.names


def test_qualified_call_extraction(tmp_path: Path) -> None:
    """obj.method() calls should be captured for cross-file resolution."""
    path = tmp_path / "service.ts"
    path.write_text(CLASS_SAMPLE)
    result = TypeScriptParser().parse(path, CLASS_SAMPLE)
    all_callees = {c.callee for sym in result.symbols for c in sym.calls}
    # charge() and refund() calls should appear (bare or qualified)
    assert any("charge" in c for c in all_callees)
