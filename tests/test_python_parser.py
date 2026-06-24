"""Python parser tests."""

from pathlib import Path

from flowindex.parsers.python_parser import PythonParser

SAMPLE = '''
import os
from services.ledger import update_ledger

@app.post("/payments")
async def create_payment_handler(body):
    validate_payment_input(body.amount)
    intent = create_payment_intent(body.customer_id, body.amount)
    update_ledger(intent["payment_id"], body.amount)
    return intent

def validate_payment_input(amount):
    pass

def create_payment_intent(customer_id, amount):
    return {"payment_id": "pay_1"}
'''


def test_python_parser_extracts_symbols_and_calls(tmp_path: Path) -> None:
    path = tmp_path / "main.py"
    path.write_text(SAMPLE)
    result = PythonParser().parse(path, SAMPLE)
    names = {s.name for s in result.symbols}
    assert "create_payment_handler" in names
    assert "validate_payment_input" in names
    handler = next(s for s in result.symbols if s.name == "create_payment_handler")
    callees = {c.callee for c in handler.calls}
    assert "validate_payment_input" in callees
    assert "update_ledger" in callees


def test_fastapi_route_detection(tmp_path: Path) -> None:
    path = tmp_path / "routes.py"
    path.write_text(SAMPLE)
    result = PythonParser().parse(path, SAMPLE)
    assert any(r.path == "/payments" and r.method == "POST" for r in result.routes)


def test_pytest_detection(tmp_path: Path) -> None:
    source = "def test_payment_flow():\n    assert True\n"
    path = tmp_path / "tests" / "test_flow.py"
    path.parent.mkdir()
    path.write_text(source)
    result = PythonParser().parse(path, source)
    assert any(t.test_name == "test_payment_flow" for t in result.tests)
