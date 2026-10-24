#!/bin/bash
set -e
cd "$(dirname "$0")"
PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python 3 was not found. Install Python 3.11 from https://www.python.org/downloads/macos/ and try again."
  exit 1
fi
"$PYTHON_BIN" - <<'PY'
import sys
if sys.version_info < (3, 10):
    print("Python 3.10+ is required. Install Python 3.11 and rerun ./start.sh.")
    raise SystemExit(1)
PY
if [ ! -d .venv ]; then
  "$PYTHON_BIN" -m venv .venv
fi
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
echo ""
echo "Starting ArtMockery at http://127.0.0.1:8000"
echo "Press Ctrl+C to stop."
exec .venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8000
