#!/usr/bin/env bash
# Run the FastAPI example demo and save terminal output for README/docs.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

source .venv/bin/activate
pip install -e . -q

APP="$ROOT/examples/python_fastapi_app"
rm -rf "$APP/.flowindex"

{
  echo '$ cd examples/python_fastapi_app'
  cd "$APP"
  echo '$ flowindex init --here'
  flowindex init --here
  echo
  echo '$ flowindex scan'
  flowindex scan
  echo
  echo '$ flowindex context "fix duplicate payments when webhook retries"'
  flowindex context "fix duplicate payments when webhook retries"
} | tee "$ROOT/docs/demo-output.txt"

echo
echo "Saved docs/demo-output.txt"
