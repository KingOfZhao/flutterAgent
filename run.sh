#!/usr/bin/env bash
# Bootstraps a venv, installs deps, and starts the FastAPI server.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

PY="${PYTHON:-python3}"

if [ ! -d ".venv" ]; then
  echo "[run] creating venv (.venv) ..."
  "$PY" -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "[run] installing dependencies ..."
pip install --upgrade pip >/dev/null
pip install -r requirements.txt

if [ ! -f ".env" ]; then
  echo "[run] no .env found, copying from .env.example ..."
  cp .env.example .env
  echo "[run] please edit .env and set DEEPSEEK_API_KEY before calling /v1/refine"
fi

# shellcheck disable=SC1091
set -a; source .env; set +a

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8765}"

echo "[run] starting flutter-agent on http://${HOST}:${PORT}"
echo "[run] OpenAPI docs:    http://${HOST}:${PORT}/docs"
echo "[run] OpenAPI schema:  http://${HOST}:${PORT}/openapi.json"

exec uvicorn flutter_agent.main:app \
  --app-dir src \
  --host "$HOST" \
  --port "$PORT" \
  --reload
