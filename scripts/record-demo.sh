#!/usr/bin/env bash
# Record a FlowIndex demo GIF (requires vhs: brew install vhs)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v vhs >/dev/null 2>&1; then
  echo "Install vhs first: brew install vhs"
  echo "Then run: cd scripts && vhs demo.tape"
  exit 1
fi

# Ensure flowindex is on PATH
source .venv/bin/activate 2>/dev/null || pip install -e . >/dev/null

cd scripts
vhs demo.tape
mv demo.gif ../docs/demo.gif
echo "Wrote docs/demo.gif"
